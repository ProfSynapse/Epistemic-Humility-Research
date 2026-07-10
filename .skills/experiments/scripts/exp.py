#!/usr/bin/env python3
"""Experiments lifecycle CLI for the experiments-first layout.

One self-contained directory per evidence-producing experiment lives under the
repo-root ``experiments/`` tree. Each directory holds a signed ``AMENDMENT.md``
(prose), a thin machine-readable ``experiment.yaml`` manifest (the single source
of truth for machine state), the instrument configs, a ``NOTEBOOK.md`` running
log, an untracked ``analysis/`` scratch dir, and a gitignored ``directions/``
data dir. The registry files under ``experiments/`` are GENERATED from the
manifests and must never be hand-edited.

This module is stdlib + PyYAML only, deterministic (no timestamps in any
generated output), and is exercised both through ``bin/exp`` and directly in
tests. Every core function takes an explicit repo ``root`` so tests can drive it
against a temporary tree.

Subcommands: new, sign, list, show, resolve, validate, regen.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import yaml

EXPERIMENTS_DIRNAME = "experiments"
MANIFEST_NAME = "experiment.yaml"
REGISTRY_MD_NAME = "REGISTRY.md"
REGISTRY_JSON_NAME = "registry.json"

# Reserved directory names under experiments/ that are never themselves an
# experiment: common/ is the shared cross-experiment code home (graders, renders,
# promoted directions). They carry no manifest and are excluded from validation,
# the manifest scan, and the registry.
RESERVED_DIRNAMES = frozenset({"common"})
_SKIP_DIRNAMES = frozenset({"__pycache__"}) | RESERVED_DIRNAMES

TYPES = (
    "steer-cell",
    "training-run",
    "eval",
    "probe-fit",
    "lab-diagnostic",
    "historical-amendment",
)
STATUSES = ("draft", "signed", "running", "resolved", "null-result", "falsified", "historical")
# Statuses at or beyond signing: pins are expected to exist and still match.
SIGNED_PLUS = frozenset({"signed", "running", "resolved", "null-result", "falsified"})
# Terminal statuses that must carry a verdict.
RESOLVED_STATES = frozenset({"resolved", "null-result", "falsified", "historical"})
# Statuses whose pins must exist and still match: signed+ plus migrated
# historical-amendment records, which carry pins from their original run but
# are not caught by SIGNED_PLUS.
PIN_CHECK_STATUSES = SIGNED_PLUS | {"historical"}

GENERATED_HEADER = "GENERATED - do not edit; run bin/exp regen and stage the result"

# GitHub project the pr field links into (used only for REGISTRY.md rendering).
_GH_REPO = "ProfSynapse/Epistemic-Humility-Research"


class ExpError(Exception):
    """A user-facing error; the CLI prints the message and exits non-zero."""


# --- repo / path discovery ---------------------------------------------------

def find_repo_root(start: Path | None = None) -> Path:
    """Walk up from ``start`` (or cwd) until a dir holds a ``.git`` entry.

    Worktrees keep a ``.git`` file rather than a directory, so we accept either.
    """
    here = (start or Path.cwd()).resolve()
    for candidate in (here, *here.parents):
        if (candidate / ".git").exists():
            return candidate
    raise ExpError(f"no git repo root found above {here}")


def experiments_dir(root: Path) -> Path:
    return root / EXPERIMENTS_DIRNAME


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def now_utc() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def slugify(value: str) -> str:
    import re

    slug = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
    return slug or "experiment"


# --- manifest IO -------------------------------------------------------------

def load_manifest(manifest_path: Path) -> dict:
    """Parse one manifest, returning a dict. Raises ExpError on unreadable YAML."""
    try:
        text = manifest_path.read_text(encoding="utf-8")
    except OSError as exc:  # pragma: no cover - filesystem dependent
        raise ExpError(f"{manifest_path}: cannot read ({exc})") from exc
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ExpError(f"{manifest_path}: invalid YAML ({exc})") from exc
    if not isinstance(data, dict):
        raise ExpError(f"{manifest_path}: manifest must be a YAML mapping")
    return data


def manifest_path_for(root: Path, slug: str) -> Path:
    return experiments_dir(root) / slug / MANIFEST_NAME


def iter_manifests(root: Path) -> list[tuple[str, Path, dict]]:
    """Every experiment dir's (slug, manifest_path, manifest) sorted by slug.

    Directories without a manifest are skipped silently so partially staged trees
    do not crash read-only commands; ``validate`` reports missing manifests.
    """
    base = experiments_dir(root)
    if not base.is_dir():
        return []
    out: list[tuple[str, Path, dict]] = []
    for child in sorted(base.iterdir(), key=lambda p: p.name):
        if not child.is_dir():
            continue
        if child.name in _SKIP_DIRNAMES:
            continue
        mpath = child / MANIFEST_NAME
        if not mpath.is_file():
            continue
        out.append((child.name, mpath, load_manifest(mpath)))
    return out


def _dump_manifest(manifest_path: Path, data: dict) -> None:
    """Write a manifest with stable key order and no timestamps."""
    manifest_path.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True, default_flow_style=False),
        encoding="utf-8",
    )


# --- templates ---------------------------------------------------------------

def _manifest_template(slug: str, exp_type: str, title: str | None = None) -> dict:
    return {
        "slug": slug,
        "title": title or slug,
        "type": exp_type,
        "status": "draft",
        "registered": True,
        "created_at": now_utc(),
        "question": "",
        "prediction": "",
        "falsifier": "",
        "checkpoint": {"repo": "", "revision": ""},
        "instrument": {
            "configs": [],
            "modules": [],
            "pins": {},
        },
        "inputs": [],
        "verdict": "",
        "kg": [],
    }


_AMENDMENT_TEMPLATE = """# {title}

Status: draft (not signed; do not launch as confirmatory evidence).

Keep this document the prose home for the experiment. The machine state lives in
`{manifest}` and is never duplicated here.

## Motivation and posture

Why this experiment exists, what prior result or gap it follows from, and whether
it is headline or exploratory evidence.

## Design

Substrate, signal, rendering, arms, and controls. Name the instrument config
files that `exp sign` will pin.

## Prediction

One sentence, stated before the run. Copy it into `prediction:` in the manifest.

## Falsifier

The concrete result that would falsify the prediction. Copy it into
`falsifier:` in the manifest.

## Gates

The pre-stated pass/fail thresholds. Derive them from the expected effect size
and its uncertainty; do not round to a convenient default.

## Predictions scoreboard

| Predictor | Call |
|-----------|------|
| orchestrator | |
| user | |

## Outcome

Filled at resolve. Record the verdict, the gate results, and the one-sentence
summary that also goes into `verdict:` in the manifest.
"""


_NOTEBOOK_TEMPLATE = """# {title} notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `{manifest}`.

## Entries

- (add dated entries as the experiment progresses)
"""


_GITIGNORE_TEMPLATE = """# Fitted directions and other large local data for this experiment.
directions/
# Local analysis scratch; keep untracked, promote real outputs deliberately.
analysis/
"""


_CELL_TEMPLATE = """# TODO: replace this placeholder with the pinned experiment instrument.
# Keep this file in the experiment directory unless the runner skill for this
# experiment type requires a different config layout.
#
# Before signing:
# - fill the actual runner/tuner config
# - list this file under experiment.yaml instrument.configs
# - run `bin/exp sign <slug>` to pin the final bytes
"""


_GATES_TEMPLATE = """# TODO: replace this placeholder with pre-stated gates.
# Gates must be fixed before launch and should define the pass/fail thresholds
# and falsifier boundary used by the amendment.
"""


# --- validation --------------------------------------------------------------

def _validate_manifest(root: Path, slug: str, mpath: Path, data: dict) -> list[str]:
    """Return a list of human-readable problems for one manifest (empty = ok)."""
    problems: list[str] = []

    def err(msg: str) -> None:
        problems.append(f"{mpath}: {msg}")

    # slug matches dir name
    declared_slug = data.get("slug")
    if declared_slug != slug:
        err(f"slug {declared_slug!r} does not match directory name {slug!r}")

    exp_type = data.get("type")
    if exp_type not in TYPES:
        err(f"type {exp_type!r} not one of {', '.join(TYPES)}")

    status = data.get("status")
    if status not in STATUSES:
        err(f"status {status!r} not one of {', '.join(STATUSES)}")

    registered = data.get("registered")
    if not isinstance(registered, bool):
        err("registered must be a boolean (true|false)")
        registered = True  # assume registered so downstream checks still run

    question = data.get("question")
    if not (isinstance(question, str) and question.strip()):
        err("question must be a non-empty string")

    instrument = data.get("instrument")
    if not isinstance(instrument, dict):
        err("instrument must be a mapping with configs/pins")
        return problems
    configs = instrument.get("configs", [])
    modules = instrument.get("modules", []) or []
    pins = instrument.get("pins", {})
    if not isinstance(configs, list):
        err("instrument.configs must be a list")
        configs = []
    if not isinstance(modules, list):
        err("instrument.modules must be a list")
        modules = []
    if not isinstance(pins, dict):
        err("instrument.pins must be a mapping")
        pins = {}

    inputs = data.get("inputs", []) or []
    if not isinstance(inputs, list):
        err("inputs must be a list")
        inputs = []

    kg = data.get("kg", []) or []
    if not isinstance(kg, list):
        err("kg must be a list")
        kg = []

    # Claim requirements: only for registered experiments past draft.
    if registered and status in SIGNED_PLUS:
        for field in ("prediction", "falsifier"):
            val = data.get(field)
            if not (isinstance(val, str) and val.strip()):
                err(f"{field} must be non-empty for a registered {status} experiment")
    if registered and status in RESOLVED_STATES:
        verdict = data.get("verdict")
        if not (isinstance(verdict, str) and verdict.strip()):
            err(f"verdict must be non-empty for a {status} experiment")

    exp_dir = mpath.parent

    # Pins: signed+ experiments must have pinned every config, and every pinned
    # file must still exist and hash to its recorded value. Historical-amendment
    # records are not required to have pinned every config/module (some were
    # migrated with partial pin coverage), but any pin they do carry must still
    # match, so they get the drift check without the completeness check.
    if status in SIGNED_PLUS:
        pin_targets = [str(c) for c in configs] + [str(m) for m in modules]
        for rel in pin_targets:
            if rel not in pins:
                err(f"config/module {rel!r} is not pinned (run exp sign)")
    if status in PIN_CHECK_STATUSES:
        for rel, recorded in pins.items():
            fpath = exp_dir / rel
            if not fpath.is_file():
                err(f"pinned file missing: {rel}")
                continue
            actual = _sha256(fpath)
            if actual != recorded:
                err(f"pin drift: {rel} hashes {actual[:12]}..., pinned {str(recorded)[:12]}...")

    # Inputs: repo-relative paths that must exist.
    for rel in inputs:
        ipath = root / str(rel)
        if not ipath.exists():
            err(f"input path does not exist: {rel}")

    # KG ids must resolve to real library nodes.
    if kg:
        known = _scan_kg_ids(root)
        for node_id in kg:
            if str(node_id) not in known:
                err(f"kg id does not resolve to a library node: {node_id}")

    return problems


def _parse_frontmatter_id(path: Path) -> str | None:
    """Best-effort read of a leading ``id:`` from a markdown frontmatter block."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:  # pragma: no cover
        return None
    if not text.startswith("---"):
        return None
    try:
        end = text.index("\n---", 3)
    except ValueError:
        return None
    for line in text[3:end].split("\n"):
        stripped = line.strip()
        if stripped.startswith("id:"):
            value = stripped.split(":", 1)[1].strip().strip('"').strip("'")
            return value or None
    return None


def _scan_kg_ids(root: Path) -> set[str]:
    """Collect resolvable KG node ids from library/ (frontmatter id, else stem).

    Mirrors the id-scan posture of the kg-ingest inventory: concept atoms and
    mechanisms carry an ``id:`` in frontmatter (fallback to the file stem), and
    paper notes resolve by stem.
    """
    ids: set[str] = set()
    library = root / "library"
    if not library.is_dir():
        return ids
    for md in library.rglob("*.md"):
        ids.add(md.stem)
        fm_id = _parse_frontmatter_id(md)
        if fm_id:
            ids.add(fm_id)
    return ids


def validate(root: Path) -> int:
    """Validate every manifest under experiments/. Returns process exit code."""
    base = experiments_dir(root)
    problems: list[str] = []

    if base.is_dir():
        # Surface experiment dirs that lack a manifest entirely.
        for child in sorted(base.iterdir(), key=lambda p: p.name):
            if not child.is_dir():
                continue
            if child.name in _SKIP_DIRNAMES:
                continue
            if not (child / MANIFEST_NAME).is_file():
                problems.append(f"{child}: missing {MANIFEST_NAME}")
        for slug, mpath, data in iter_manifests(root):
            problems.extend(_validate_manifest(root, slug, mpath, data))

    if problems:
        print("exp validate: FAILED")
        for line in problems:
            print(f"  - {line}")
        return 1
    count = len(iter_manifests(root))
    print(f"exp validate: OK ({count} experiment(s))")
    return 0


# --- registry generation -----------------------------------------------------

def _pr_cell(pr: object) -> str:
    if pr in (None, "", 0):
        return ""
    return f"[#{pr}](https://github.com/{_GH_REPO}/pull/{pr})"


def render_registry_md(root: Path) -> str:
    lines = [
        f"<!-- {GENERATED_HEADER} -->",
        "",
        "# Experiments registry",
        "",
        "| slug | type | status | PR | question | verdict |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for slug, _mpath, data in iter_manifests(root):
        question = str(data.get("question", "") or "").replace("|", "\\|").strip()
        verdict = str(data.get("verdict", "") or "").replace("|", "\\|").strip()
        # registered:false rows stay in the inventory but are marked so they are
        # never read as a claim.
        if data.get("registered") is False:
            question = f"teaching artifact: {question}".strip()
        row = [
            slug,
            str(data.get("type", "") or ""),
            str(data.get("status", "") or ""),
            _pr_cell(data.get("pr")),
            question,
            verdict,
        ]
        lines.append("| " + " | ".join(row) + " |")
    lines.append("")
    return "\n".join(lines)


def render_registry_json(root: Path) -> str:
    payload = {
        "_generated": GENERATED_HEADER,
        "experiments": [data for _slug, _mpath, data in iter_manifests(root)],
    }
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def regen(root: Path, *, check: bool = False) -> int:
    base = experiments_dir(root)
    md_text = render_registry_md(root)
    json_text = render_registry_json(root)
    md_path = base / REGISTRY_MD_NAME
    json_path = base / REGISTRY_JSON_NAME

    if check:
        stale: list[str] = []
        for path, expected in ((md_path, md_text), (json_path, json_text)):
            current = path.read_text(encoding="utf-8") if path.is_file() else None
            if current != expected:
                stale.append(str(path.relative_to(root)))
        if stale:
            print("exp regen --check: STALE registry files: " + ", ".join(stale))
            print("  run `bin/exp regen` and stage the result")
            return 1
        print("exp regen --check: registry up to date")
        return 0

    base.mkdir(parents=True, exist_ok=True)
    md_path.write_text(md_text, encoding="utf-8")
    json_path.write_text(json_text, encoding="utf-8")
    print(f"exp regen: wrote {md_path.relative_to(root)} and {json_path.relative_to(root)}")
    return 0


# --- subcommands: new / sign / list / show / resolve -------------------------

def cmd_new(root: Path, slug: str | None, exp_type: str, title: str | None = None) -> int:
    if exp_type not in TYPES:
        raise ExpError(f"type {exp_type!r} not one of {', '.join(TYPES)}")
    if not slug:
        if not title:
            raise ExpError("provide a slug or --title")
        slug = slugify(title)
    if not slug or not all(c.islower() or c.isdigit() or c == "-" for c in slug) or slug[0] == "-":
        raise ExpError(
            f"slug {slug!r} must be kebab-case (lowercase letters, digits, hyphens; "
            "not starting with a hyphen)"
        )
    title = title or slug
    exp_dir = experiments_dir(root) / slug
    if exp_dir.exists():
        raise ExpError(f"experiment already exists: {exp_dir}")

    exp_dir.mkdir(parents=True)
    _dump_manifest(exp_dir / MANIFEST_NAME, _manifest_template(slug, exp_type, title))
    (exp_dir / "AMENDMENT.md").write_text(
        _AMENDMENT_TEMPLATE.format(title=title, slug=slug, manifest=MANIFEST_NAME), encoding="utf-8"
    )
    (exp_dir / "NOTEBOOK.md").write_text(
        _NOTEBOOK_TEMPLATE.format(title=title, slug=slug, manifest=MANIFEST_NAME), encoding="utf-8"
    )
    (exp_dir / ".gitignore").write_text(_GITIGNORE_TEMPLATE, encoding="utf-8")
    (exp_dir / "cell.yaml").write_text(_CELL_TEMPLATE, encoding="utf-8")
    (exp_dir / "gates.yaml").write_text(_GATES_TEMPLATE, encoding="utf-8")

    print(f"exp new: scaffolded {exp_dir.relative_to(root)} (type={exp_type}, status=draft)")
    print("  created: experiment.yaml, AMENDMENT.md, NOTEBOOK.md, cell.yaml, gates.yaml, .gitignore")
    print("  next: fill question/prediction/falsifier + instrument.configs, then `bin/exp sign`")
    return 0


def _has_surface_block(path: Path) -> bool:
    """True if a config file parses to a mapping with a top-level surface: block."""
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return False
    return isinstance(data, dict) and isinstance(data.get("surface"), dict)


def cmd_sign(root: Path, slug: str) -> int:
    mpath = manifest_path_for(root, slug)
    if not mpath.is_file():
        raise ExpError(f"no manifest at {mpath}")
    data = load_manifest(mpath)

    if data.get("status") != "draft":
        raise ExpError(
            f"{slug}: status is {data.get('status')!r}; only a draft experiment can be signed"
        )
    for field in ("prediction", "falsifier"):
        val = data.get(field)
        if not (isinstance(val, str) and val.strip()):
            raise ExpError(f"{slug}: {field} must be filled before signing")

    exp_dir = mpath.parent
    instrument = data.setdefault("instrument", {})
    configs = list(instrument.get("configs", []) or [])
    modules = list(instrument.get("modules", []) or [])
    pin_targets = [str(c) for c in configs] + [str(m) for m in modules]
    if not pin_targets:
        raise ExpError(
            f"{slug}: instrument.configs is empty; list the instrument files before signing"
        )

    pins: dict[str, str] = {}
    steer_cells: list[str] = []
    for rel in pin_targets:
        fpath = exp_dir / rel
        if not fpath.is_file():
            raise ExpError(f"{slug}: cannot pin missing file {rel}")
        pins[rel] = _sha256(fpath)
        if _has_surface_block(fpath):
            steer_cells.append(rel)

    instrument["pins"] = pins
    data["status"] = "signed"
    _dump_manifest(mpath, data)

    print(f"exp sign: {slug} signed; pinned {len(pins)} file(s)")
    for rel, sha in pins.items():
        print(f"  {rel}: {sha}")
    for rel in steer_cells:
        print(
            f"  reminder: {rel} is a tuner steer cell. The pin above is a file-integrity "
            "hash of the YAML bytes, not the value surface.expected_config_sha checks "
            "(that compares against compute_config_sha over the parsed config, a "
            "different hash). To set expected_config_sha: run the cell once with it "
            "unset, copy the config_sha the tuner prints on completion "
            '("Steer cell complete. Output ..., config_sha <X>"), and hand-fill that value.'
        )
    return 0


def cmd_list(root: Path, status: str | None, exp_type: str | None) -> int:
    rows = []
    for slug, _mpath, data in iter_manifests(root):
        if status and data.get("status") != status:
            continue
        if exp_type and data.get("type") != exp_type:
            continue
        rows.append(
            (slug, str(data.get("type", "")), str(data.get("status", "")),
             str(data.get("question", "") or ""))
        )
    if not rows:
        print("(no experiments)")
        return 0
    widths = [max(len(r[i]) for r in ([("slug", "type", "status", "question")] + rows))
              for i in range(4)]
    header = ("slug", "type", "status", "question")
    print("  ".join(h.ljust(widths[i]) for i, h in enumerate(header)))
    print("  ".join("-" * widths[i] for i in range(4)))
    for r in rows:
        print("  ".join(r[i].ljust(widths[i]) for i in range(4)))
    return 0


def cmd_show(root: Path, slug: str) -> int:
    mpath = manifest_path_for(root, slug)
    if not mpath.is_file():
        raise ExpError(f"no manifest at {mpath}")
    data = load_manifest(mpath)
    exp_dir = mpath.parent
    print(f"# {slug}")
    print(yaml.safe_dump(data, sort_keys=False, allow_unicode=True).rstrip())
    print("\n# resolved paths")
    print(f"  dir: {exp_dir}")
    print(f"  manifest: {mpath}")
    for rel in (data.get("instrument", {}) or {}).get("configs", []) or []:
        target = exp_dir / str(rel)
        mark = "ok" if target.is_file() else "MISSING"
        print(f"  config: {target} [{mark}]")
    return 0


def cmd_resolve(root: Path, slug: str, verdict: str, status: str) -> int:
    if status not in RESOLVED_STATES:
        raise ExpError(f"resolve status must be one of {', '.join(sorted(RESOLVED_STATES))}")
    if not verdict.strip():
        raise ExpError("verdict must be a non-empty sentence")
    mpath = manifest_path_for(root, slug)
    if not mpath.is_file():
        raise ExpError(f"no manifest at {mpath}")
    data = load_manifest(mpath)
    data["status"] = status
    data["verdict"] = verdict.strip()
    _dump_manifest(mpath, data)

    print(f"exp resolve: {slug} -> {status}")
    print(f"  verdict: {verdict.strip()}")
    print("  kg-ingest checklist:")
    print("    1. ingest the result as typed KG nodes (claim/mechanism/evidence) via the kg-ingest skill")
    print("    2. record the returned node ids in the manifest `kg:` list")
    print("    3. run `bin/exp validate` to confirm the kg ids resolve")
    print("    4. run `bin/exp regen` and stage the updated registry")
    return 0


# --- argparse / main ---------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="exp", description="Experiments lifecycle CLI (draft -> sign -> run -> resolve)."
    )
    parser.add_argument(
        "--root", default=None,
        help="repo root (default: discovered by walking up to the git root).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_new = sub.add_parser("new", help="scaffold a new experiment directory")
    p_new.add_argument("slug", nargs="?", help="experiment slug; defaults to slugified --title")
    p_new.add_argument("--title", help="human title for AMENDMENT.md / NOTEBOOK.md; also used to derive slug if omitted")
    p_new.add_argument("--type", required=True, choices=TYPES, dest="exp_type")

    p_sign = sub.add_parser("sign", help="pin instrument configs and flip draft->signed")
    p_sign.add_argument("slug")

    p_list = sub.add_parser("list", help="table of all experiments")
    p_list.add_argument("--status", choices=STATUSES, default=None)
    p_list.add_argument("--type", choices=TYPES, default=None, dest="exp_type")

    p_show = sub.add_parser("show", help="pretty-print one manifest and resolved paths")
    p_show.add_argument("slug")

    p_resolve = sub.add_parser("resolve", help="stamp a verdict and flip to a terminal status")
    p_resolve.add_argument("slug")
    p_resolve.add_argument("--verdict", required=True)
    p_resolve.add_argument(
        "--status", default="resolved", choices=sorted(RESOLVED_STATES),
        help="terminal status (default: resolved)",
    )

    sub.add_parser("validate", help="validate every manifest under experiments/")

    p_regen = sub.add_parser("regen", help="regenerate the registry files")
    p_regen.add_argument("--check", action="store_true",
                         help="fail if the committed registry is stale")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        root = Path(args.root).resolve() if args.root else find_repo_root()
        if args.command == "new":
            return cmd_new(root, args.slug, args.exp_type, title=args.title)
        if args.command == "sign":
            return cmd_sign(root, args.slug)
        if args.command == "list":
            return cmd_list(root, args.status, args.exp_type)
        if args.command == "show":
            return cmd_show(root, args.slug)
        if args.command == "resolve":
            return cmd_resolve(root, args.slug, args.verdict, args.status)
        if args.command == "validate":
            return validate(root)
        if args.command == "regen":
            return regen(root, check=args.check)
    except ExpError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    parser.error(f"unknown command {args.command!r}")  # pragma: no cover
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
