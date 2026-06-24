#!/usr/bin/env python3
"""Validate experiment notes and regenerate their registry index.

Experiment notes are checked-in Markdown files under experiment/notes/ with YAML
frontmatter. They are the agent-runnable spec + runbook for one experiment family
(see experiment/notes/_SCHEMA.md). This validator enforces the schema so the
structure holds at commit time (.githooks/pre-commit) and on every PR
(.github/workflows/validate.yml). Generic kg/edge correctness is left to
validate_kg_relationships.py; this checks the experiment-note-specific contract.

Usage (run from repo root):
    python3 .agents/skills/experiment-runner/scripts/validate_experiment_notes.py experiment/notes
    python3 .agents/skills/experiment-runner/scripts/validate_experiment_notes.py experiment/notes --emit-index
    python3 .agents/skills/experiment-runner/scripts/validate_experiment_notes.py experiment/notes --json

Exit code 1 if any note fails (mirrors research_session.py validate); else 0.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

VALID_STATUS = {"proposed", "ready", "running", "blocked", "done", "superseded"}
VALID_GOVERNANCE = {"exploratory", "amendment", "locked"}
VALID_LANE = {"local", "cloud", "either"}

# (canonical label, lowercased substring that must appear in some `##` heading)
REQUIRED_SECTIONS = [
    ("Question & Hypothesis", "question"),
    ("Design", "design"),
    ("Prerequisites & Gating", "prerequisites"),
    ("Runbook", "runbook"),
    ("Validation contract", "validation contract"),
    ("Outputs & provenance", "outputs"),
    ("Variations", "variations"),
    ("Status log", "status log"),
]

FRONTMATTER_RE = re.compile(r"\A---[ \t]*\r?\n(?P<body>.*?)\r?\n---(?:\r?\n|\Z)", re.S)
HEADING_RE = re.compile(r"^##\s+(.+?)\s*$", re.M)
BACKTICK_RE = re.compile(r"`([^`]+)`")
# repo-root-relative path prefixes whose backticked references must exist on disk
PATH_PREFIXES = (
    "experiment/", "library/", "meta-analysis/", "bin/", "tools/", "docs/",
    ".agents/", ".skills/", ".claude/", ".github/",
)


def repo_root() -> Path:
    """Walk up for the repo root (the dir owning bin/sync_skills.py); fallback cwd."""
    here = Path.cwd().resolve()
    for cand in (here, *here.parents):
        if (cand / "bin" / "sync_skills.py").is_file():
            return cand
    return here


_IGNORE_CACHE: dict[str, bool] = {}


def is_gitignored(root: Path, rel: str) -> bool:
    """True if `rel` (repo-relative) is excluded by .gitignore. Cached.

    Gitignored paths (e.g. library/fulltext/ HTML, restricted/large data) are not
    committed, so a runbook may legitimately reference one that is present for the
    operator but absent in a fresh CI checkout. Existence of such paths cannot be
    enforced, so they are skipped rather than flagged as rot.
    """
    if rel in _IGNORE_CACHE:
        return _IGNORE_CACHE[rel]
    try:
        res = subprocess.run(
            [
                "git",
                "-c",
                f"safe.directory={root.as_posix()}",
                "-C",
                str(root),
                "check-ignore",
                "-q",
                "--",
                rel,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        ignored = res.returncode == 0
    except (OSError, subprocess.SubprocessError):
        ignored = False
    _IGNORE_CACHE[rel] = ignored
    return ignored


def split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        raise ValueError("note must start with YAML frontmatter")
    fm = yaml.safe_load(match.group("body")) or {}
    if not isinstance(fm, dict):
        raise ValueError("frontmatter must be a YAML mapping")
    return fm, text[match.end():]


def sections(body: str) -> dict[str, str]:
    """Map each `##` heading (lowercased) to the text under it."""
    out: dict[str, str] = {}
    matches = list(HEADING_RE.finditer(body))
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        out[m.group(1).strip().lower()] = body[m.end():end].strip()
    return out


def has_real_content(text: str) -> bool:
    """True if the section has prose beyond whitespace and HTML-comment placeholders."""
    stripped = re.sub(r"<!--.*?-->", "", text, flags=re.S).strip()
    return len(stripped) >= 20


def iter_note_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    if path.is_dir():
        return sorted(
            p for p in path.glob("*.md")
            if not p.name.startswith("_") and p.name.upper() != "README.MD"
        )
    raise ValueError(f"path does not exist: {path}")


def validate_note(path: Path, root: Path) -> list[str]:
    errors: list[str] = []
    loc = f"{path}: "
    try:
        fm, body = split_frontmatter(path.read_text(encoding="utf-8"))
    except ValueError as exc:
        return [f"{loc}{exc}"]

    stem = path.stem

    # --- kg block ---
    kg = fm.get("kg")
    if not isinstance(kg, dict):
        errors.append(f"{loc}kg block is required")
    else:
        if kg.get("type") != "experiment":
            errors.append(f"{loc}kg.type must be 'experiment'")
        kid = kg.get("id", "")
        if kid != f"experiment:{stem}":
            errors.append(f"{loc}kg.id must be 'experiment:{stem}' (matches filename), got {kid!r}")
        if not kg.get("status"):
            errors.append(f"{loc}kg.status is required")

    # --- scalar frontmatter ---
    if not fm.get("title"):
        errors.append(f"{loc}title is required")
    if fm.get("status") not in VALID_STATUS:
        errors.append(f"{loc}status must be one of {sorted(VALID_STATUS)}")
    governance = fm.get("governance")
    if governance not in VALID_GOVERNANCE:
        errors.append(f"{loc}governance must be one of {sorted(VALID_GOVERNANCE)}")
    if fm.get("lane") not in VALID_LANE:
        errors.append(f"{loc}lane must be one of {sorted(VALID_LANE)}")
    for key in ("phase", "est_compute"):
        if not fm.get(key):
            errors.append(f"{loc}{key} is required")

    # --- relationships: a `tests` edge is mandatory ---
    rels = fm.get("relationships")
    if not isinstance(rels, list):
        errors.append(f"{loc}relationships must be a list")
        rels = []
    if not any(isinstance(r, dict) and r.get("type") == "tests" for r in rels):
        errors.append(f"{loc}relationships must include a 'tests' edge (to a gap or mechanism)")
    if not isinstance(fm.get("related", []), list):
        errors.append(f"{loc}related must be a list")

    # --- required body sections ---
    secs = sections(body)
    heads = list(secs.keys())
    for label, needle in REQUIRED_SECTIONS:
        if not any(needle in h for h in heads):
            errors.append(f"{loc}missing required section '## {label}'")

    # --- governance rule ---
    if governance in {"locked", "amendment"}:
        if "PROTOCOL" not in body:
            errors.append(f"{loc}{governance} note must reference PROTOCOL.md (a section)")
    elif governance == "exploratory":
        design = next((secs[h] for h in heads if "design" in h), "")
        if not has_real_content(design):
            errors.append(f"{loc}exploratory note must carry an inline Design section")

    # --- runbook path rule (catch rot of referenced scripts/recipes) ---
    runbook = next((secs[h] for h in heads if "runbook" in h), "")
    for token in BACKTICK_RE.findall(runbook):
        tok = token.strip()
        if (
            tok.startswith(PATH_PREFIXES)
            and not (root / tok).exists()
            and not is_gitignored(root, tok)
        ):
            errors.append(f"{loc}runbook references missing path '{tok}'")

    return errors


def tests_target(fm: dict[str, Any]) -> str:
    for r in fm.get("relationships") or []:
        if isinstance(r, dict) and r.get("type") == "tests":
            return str(r.get("target_id") or r.get("target") or "")
    return ""


def emit_index(path: Path) -> str:
    rows = []
    for note in iter_note_files(path):
        try:
            fm, _ = split_frontmatter(note.read_text(encoding="utf-8"))
        except ValueError:
            continue
        rows.append({
            "stem": note.stem,
            "title": fm.get("title", note.stem),
            "status": fm.get("status", "?"),
            "governance": fm.get("governance", "?"),
            "phase": fm.get("phase", "?"),
            "lane": fm.get("lane", "?"),
            "tests": tests_target(fm),
        })
    order = {s: i for i, s in enumerate(
        ["running", "ready", "blocked", "proposed", "done", "superseded"])}
    rows.sort(key=lambda r: (order.get(r["status"], 99), r["stem"]))

    out = [
        "# Experiment notes registry",
        "",
        "Auto-generated by `validate_experiment_notes.py --emit-index`; do not "
        "hand-edit. Each note is an agent-runnable spec + runbook "
        "(see [_SCHEMA.md](_SCHEMA.md)). Point an agent at a note to set it up, "
        "run it, document it, and validate it.",
        "",
        f"{len(rows)} experiment note(s).",
        "",
        "| Experiment | Status | Governance | Phase | Lane | Tests |",
        "|---|---|---|---|---|---|",
    ]
    for r in rows:
        out.append(
            f"| [[{r['stem']}]] | {r['status']} | {r['governance']} | "
            f"{r['phase']} | {r['lane']} | {r['tests']} |"
        )
    out.append("")
    text = "\n".join(out)
    (path / "README.md").write_text(text, encoding="utf-8")
    return text


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Validate experiment notes; regenerate the registry.")
    ap.add_argument("path", nargs="?", default="experiment/notes")
    ap.add_argument("--emit-index", action="store_true", help="regenerate experiment/notes/README.md")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    root = repo_root()
    target = Path(args.path)

    try:
        notes = iter_note_files(target)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    errors: list[str] = []
    for note in notes:
        errors.extend(validate_note(note, root))

    if args.json:
        print(json.dumps({"errors": errors, "notes": len(notes)}, indent=2))
    elif errors:
        print("Experiment-note validation failed:")
        for e in errors:
            print(f"- {e}")
    else:
        print(f"Experiment-note validation passed ({len(notes)} note(s)).")

    if args.emit_index and not errors and target.is_dir():
        emit_index(target)
        print(f"Wrote {target / 'README.md'}")

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
