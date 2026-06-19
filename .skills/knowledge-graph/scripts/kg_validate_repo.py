#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


REQUIRED_ROOT_FILES = (
    ".githooks/pre-commit",
    "bin/search",
    "bin/search.py",
    "bin/search.cmd",
    "bin/sync_skills.py",
)
REQUIRED_SKILL_FILES = (
    "SKILL.md",
    "references/edge-ontology.yaml",
    "references/relationship-schema.md",
    "scripts/kg_index.py",
    "scripts/kg_search.py",
    "scripts/kg_feedback.py",
    "scripts/kg_validate_repo.py",
    "tests/test_kg_scripts.py",
)
MIRROR_SKILL_ROOTS = (
    ".agents/skills/knowledge-graph",
    ".claude/skills/knowledge-graph",
)


@dataclass(frozen=True)
class Finding:
    severity: str
    check: str
    message: str


def repo_root(start: Path) -> Path:
    for path in (start.resolve(), *start.resolve().parents):
        if (path / "bin" / "sync_skills.py").is_file() and (path / ".skills").is_dir():
            return path
    raise FileNotFoundError("could not find repo root owning bin/sync_skills.py and .skills/")


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def check_required_files(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for rel in REQUIRED_ROOT_FILES:
        if not (root / rel).is_file():
            findings.append(Finding("ERROR", "required-files", f"missing root file: {rel}"))
    for skill_root in (".skills/knowledge-graph", *MIRROR_SKILL_ROOTS):
        for rel in REQUIRED_SKILL_FILES:
            path = root / skill_root / rel
            if not path.is_file():
                findings.append(Finding("ERROR", "required-files", f"missing {skill_root}/{rel}"))
    if os.name != "nt":
        search_path = root / "bin" / "search"
        if search_path.exists() and not os.access(search_path, os.X_OK):
            findings.append(Finding("ERROR", "required-files", "bin/search shim is not executable"))
    return findings


def check_sync(root: Path) -> list[Finding]:
    proc = subprocess.run(
        [sys.executable, str(root / "bin" / "sync_skills.py"), "--check", "--skill", "knowledge-graph"],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if proc.returncode == 0:
        return []
    output = (proc.stdout + proc.stderr).strip()
    return [Finding("ERROR", "skill-sync", output or "knowledge-graph skill mirrors drifted")]


def check_hook_installation(root: Path) -> list[Finding]:
    proc = subprocess.run(
        ["git", "config", "--get", "core.hooksPath"],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    hooks_path = proc.stdout.strip().replace("\\", "/").rstrip("/")
    if hooks_path == ".githooks":
        return []
    if hooks_path:
        message = f"core.hooksPath is {hooks_path!r}; expected '.githooks'"
    else:
        message = "core.hooksPath is not set; run: git config core.hooksPath .githooks"
    return [Finding("ERROR", "pre-commit-hook", message)]


def check_source_invariants(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    scripts = root / ".skills" / "knowledge-graph" / "scripts"
    sys.path.insert(0, str(scripts))
    try:
        kg_index = load_module(scripts / "kg_index.py", "kg_index_validate_repo")
        kg_search = load_module(scripts / "kg_search.py", "kg_search_validate_repo")
    except Exception as exc:
        return [Finding("ERROR", "source-invariants", f"failed to import KG scripts: {exc}")]
    finally:
        try:
            sys.path.remove(str(scripts))
        except ValueError:
            pass

    if ".skills" not in getattr(kg_index, "INDEXED_DOT_DIRS", set()):
        findings.append(Finding("ERROR", "source-invariants", ".skills is not allowlisted for indexing"))
    if not kg_index.should_ignore(".hidden/note.md"):
        findings.append(Finding("ERROR", "source-invariants", "dot-directories are not ignored by default"))
    if kg_index.should_ignore(".skills/demo/SKILL.md"):
        findings.append(Finding("ERROR", "source-invariants", ".skills is ignored despite being procedural memory"))

    labels = dict(kg_index.memory_labels_for_path(".skills/demo/SKILL.md", "markdown"))
    if labels.get("procedural", 0.0) < 0.9:
        findings.append(Finding("ERROR", "source-invariants", ".skills paths are not strongly procedural"))

    match_query = kg_search.build_match_query("how do I run experiment matrix", mode="and")
    if "how" in match_query.casefold() or " do " in f" {match_query.casefold()} ":
        findings.append(Finding("ERROR", "source-invariants", "search query builder is not dropping stopwords"))
    return findings


def check_temp_index(root: Path) -> list[Finding]:
    scripts = root / ".skills" / "knowledge-graph" / "scripts"
    sys.path.insert(0, str(scripts))
    try:
        kg_index = load_module(scripts / "kg_index.py", "kg_index_validate_temp")
    except Exception as exc:
        return [Finding("ERROR", "temp-index", f"failed to import kg_index.py: {exc}")]
    finally:
        try:
            sys.path.remove(str(scripts))
        except ValueError:
            pass

    with tempfile.TemporaryDirectory() as tmp:
        temp_root = Path(tmp)
        hidden = temp_root / ".hidden"
        hidden.mkdir()
        (hidden / "note.md").write_text("# Hidden\n\nconcealed\n", encoding="utf-8")
        skill = temp_root / ".skills" / "demo"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text("# Demo\n\nprocedural\n", encoding="utf-8")
        db = temp_root / ".kg" / "index.sqlite"
        try:
            summary = kg_index.index_root(temp_root, db)
            conn = sqlite3.connect(db)
            conn.row_factory = sqlite3.Row
            labels = {
                (row["path"], row["memory_type"])
                for row in conn.execute("SELECT path, memory_type FROM path_memory_labels")
            }
            conn.close()
        except Exception as exc:
            return [Finding("ERROR", "temp-index", f"temp index smoke failed: {exc}")]
    findings: list[Finding] = []
    if summary["files"] != 1:
        findings.append(Finding("ERROR", "temp-index", f"expected only .skills test file indexed, got {summary['files']}"))
    if (".skills/demo/SKILL.md", "procedural") not in labels:
        findings.append(Finding("ERROR", "temp-index", "temp .skills file was not labeled procedural"))
    return findings


def validate(
    root: Path,
    *,
    skip_sync: bool = False,
    skip_hook_installation: bool = False,
    skip_temp_index: bool = False,
) -> list[Finding]:
    findings = check_required_files(root)
    if not skip_sync:
        findings.extend(check_sync(root))
    if not skip_hook_installation:
        findings.extend(check_hook_installation(root))
    findings.extend(check_source_invariants(root))
    if not skip_temp_index:
        findings.extend(check_temp_index(root))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate KG search/source invariants for this repo.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to current directory or ancestor.")
    parser.add_argument("--skip-sync", action="store_true", help="Skip sync_skills.py drift check.")
    parser.add_argument("--skip-hook-installation", action="store_true", help="Skip core.hooksPath installation check.")
    parser.add_argument("--skip-temp-index", action="store_true", help="Skip temp index smoke test.")
    parser.add_argument("--json", action="store_true", help="Emit JSON findings.")
    args = parser.parse_args()

    try:
        root = repo_root(Path(args.root))
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    findings = validate(
        root,
        skip_sync=args.skip_sync,
        skip_hook_installation=args.skip_hook_installation,
        skip_temp_index=args.skip_temp_index,
    )
    if args.json:
        print(json.dumps([asdict(finding) for finding in findings], indent=2, sort_keys=True))
    elif findings:
        print("KG repo validation failed:")
        for finding in findings:
            print(f"- {finding.severity} [{finding.check}] {finding.message}")
    else:
        print("KG repo validation passed.")
    return 1 if any(finding.severity == "ERROR" for finding in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
