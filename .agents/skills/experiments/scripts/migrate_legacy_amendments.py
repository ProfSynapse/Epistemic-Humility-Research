#!/usr/bin/env python3
"""Migrate legacy protocol amendments into experiments-first directories.

Default mode is a dry run. With --apply, this script:

- creates experiments/<slug>/ for each legacy experiment/protocol/AMENDMENT-*.md
- writes experiment.yaml, AMENDMENT.md, NOTEBOOK.md, and .gitignore
- removes the legacy amendment file
- rewrites references across tracked text/reference files from old path to new path
- writes docs/migration/experiment-path-map.json

The migrated manifest uses status: historical. The source AMENDMENT.md prose
remains the governed provenance record; the manifest is a navigation/index layer.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

LEGACY_DIR = Path("experiment") / "protocol"
EXPERIMENTS_DIR = Path("experiments")
MIGRATION_DIR = Path("docs") / "migration"
PATH_MAP = MIGRATION_DIR / "experiment-path-map.json"
LEGACY_RE = re.compile(r"^AMENDMENT-([A-Z0-9]+)-(.+)\.md$")
FRONTMATTER_RE = re.compile(r"\A---[ \t]*\r?\n(?P<body>.*?)\r?\n---(?:\r?\n|\Z)", re.S)
REFERENCE_SUFFIXES = {
    ".md",
    ".py",
    ".yaml",
    ".yml",
    ".json",
    ".jsonl",
    ".txt",
    ".csv",
    ".tsv",
    ".toml",
    ".sh",
    ".ps1",
    ".cmd",
}
SKIP_DIRS = {".git", ".kg", ".cache", ".mypy_cache", ".pytest_cache", "__pycache__", "synaptic-tuner"}


class MigrationError(Exception):
    pass


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def repo_root(start: Path | None = None) -> Path:
    here = (start or Path.cwd()).resolve()
    for candidate in (here, *here.parents):
        if (candidate / ".git").exists():
            return candidate
    raise MigrationError(f"no git repo root found above {here}")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def frontmatter(path: Path) -> dict[str, Any]:
    text = read_text(path)
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}
    data = yaml.safe_load(match.group("body")) or {}
    return data if isinstance(data, dict) else {}


def title_from_markdown(path: Path) -> str:
    for line in read_text(path).splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem


def legacy_records(root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in sorted((root / LEGACY_DIR).glob("AMENDMENT-*.md")):
        match = LEGACY_RE.match(path.name)
        if not match:
            continue
        label, filename_slug = match.groups()
        data = frontmatter(path)
        slug = str(data.get("slug") or filename_slug)
        old_rel = path.relative_to(root).as_posix()
        new_rel = (EXPERIMENTS_DIR / slug / "AMENDMENT.md").as_posix()
        records.append(
            {
                "label": str(data.get("amendment") or label),
                "slug": slug,
                "title": title_from_markdown(path),
                "old_path": old_rel,
                "new_path": new_rel,
                "frontmatter": data,
            }
        )
    return records


def git_files(root: Path) -> list[Path]:
    try:
        proc = subprocess.run(
            ["git", "ls-files"],
            cwd=root,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.CalledProcessError):
        return []
    return [root / line for line in proc.stdout.splitlines() if line]


def walk_files(root: Path) -> list[Path]:
    out: list[Path] = []
    stack = [root]
    while stack:
        current = stack.pop()
        try:
            children = list(current.iterdir())
        except OSError:
            continue
        for child in children:
            if child.is_dir():
                if child.name not in SKIP_DIRS:
                    stack.append(child)
            else:
                out.append(child)
    return out


def reference_files(root: Path) -> list[Path]:
    files = {path.resolve() for path in git_files(root)}
    files.update(path.resolve() for path in walk_files(root))
    return sorted(
        path
        for path in files
        if path.is_file()
        and path.suffix in REFERENCE_SUFFIXES
        and not any(part in SKIP_DIRS for part in path.relative_to(root).parts)
    )


def manifest_for(record: dict[str, Any]) -> dict[str, Any]:
    data = record["frontmatter"]
    prediction = data.get("predictions")
    if isinstance(prediction, str):
        prediction_text = prediction
    elif prediction is None:
        prediction_text = ""
    else:
        prediction_text = yaml.safe_dump(prediction, sort_keys=False, allow_unicode=True).strip()
    outcome = str(data.get("outcome") or "")
    return {
        "slug": record["slug"],
        "title": record["title"],
        "type": "historical-amendment",
        "status": "historical",
        "registered": True,
        "created_at": now_utc(),
        "legacy": {
            "label": record["label"],
            "path": record["old_path"],
            "migrated_to": record["new_path"],
        },
        "migration": {
            "needs_manual_review": [
                "falsifier",
                "experiment_type",
                "instrument_configs",
                "kg_ids",
            ],
            "notes": (
                "Imported from legacy amendment prose. Do not infer missing "
                "machine fields without hand-reading AMENDMENT.md."
            ),
        },
        "question": str(data.get("question") or record["title"]),
        "prediction": prediction_text,
        "falsifier": "",
        "checkpoint": {"repo": "", "revision": ""},
        "instrument": {"configs": [], "modules": [], "pins": {}},
        "inputs": [],
        "verdict": outcome or "Historical legacy amendment migrated; see AMENDMENT.md.",
        "kg": [],
    }


def notebook_for(record: dict[str, Any]) -> str:
    return (
        f"# {record['title']} notebook\n\n"
        "Historical migration notebook.\n\n"
        "## Entries\n\n"
        f"- {now_utc()}: migrated legacy amendment `{record['old_path']}` into "
        f"`experiments/{record['slug']}/`.\n"
    )


def gitignore_text() -> str:
    return (
        "# Fitted directions and other large local data for this experiment.\n"
        "directions/\n"
        "# Local analysis scratch; keep untracked, promote real outputs deliberately.\n"
        "analysis/\n"
    )


def path_map(records: list[dict[str, Any]]) -> dict[str, str]:
    return {record["old_path"]: record["new_path"] for record in records}


def planned_rewrites(root: Path, mapping: dict[str, str]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for path in reference_files(root):
        try:
            text = read_text(path)
        except UnicodeDecodeError:
            continue
        hits = [old for old in mapping if old in text]
        if hits:
            out[path.relative_to(root).as_posix()] = hits
    return out


def validate_plan(root: Path, records: list[dict[str, Any]], apply: bool) -> None:
    seen_slugs: set[str] = set()
    for record in records:
        slug = record["slug"]
        if slug in seen_slugs:
            raise MigrationError(f"duplicate legacy slug would collide: {slug}")
        seen_slugs.add(slug)
        exp_dir = root / EXPERIMENTS_DIR / slug
        if exp_dir.exists():
            raise MigrationError(f"target already exists for {record['old_path']}: {exp_dir}")
    if apply and not records:
        raise MigrationError("no legacy amendments to migrate")


def apply_migration(root: Path, records: list[dict[str, Any]], mapping: dict[str, str]) -> None:
    (root / MIGRATION_DIR).mkdir(parents=True, exist_ok=True)
    for record in records:
        old = root / record["old_path"]
        exp_dir = root / EXPERIMENTS_DIR / record["slug"]
        exp_dir.mkdir(parents=True)
        (exp_dir / "AMENDMENT.md").write_text(read_text(old), encoding="utf-8")
        (exp_dir / "NOTEBOOK.md").write_text(notebook_for(record), encoding="utf-8")
        (exp_dir / ".gitignore").write_text(gitignore_text(), encoding="utf-8")
        old.unlink()

    for path in reference_files(root):
        try:
            text = read_text(path)
        except UnicodeDecodeError:
            continue
        new_text = text
        for old, new in mapping.items():
            new_text = new_text.replace(old, new)
        if new_text != text:
            path.write_text(new_text, encoding="utf-8")

    (root / PATH_MAP).write_text(
        json.dumps(mapping, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    # Write manifests after path rewrites so legacy.path remains the original
    # provenance path rather than being rewritten to the new canonical path.
    for record in records:
        exp_dir = root / EXPERIMENTS_DIR / record["slug"]
        (exp_dir / "experiment.yaml").write_text(
            yaml.safe_dump(manifest_for(record), sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )


def render_summary(root: Path, records: list[dict[str, Any]], rewrites: dict[str, list[str]]) -> str:
    lines = [
        "# Legacy amendment migration plan",
        "",
        f"legacy amendments: {len(records)}",
        f"reference files to rewrite: {len(rewrites)}",
        "",
        "## Targets",
    ]
    for record in records:
        lines.append(f"- {record['old_path']} -> {record['new_path']}")
    if rewrites:
        lines.append("")
        lines.append("## Reference Files")
        for path, hits in sorted(rewrites.items()):
            lines.append(f"- {path}: {len(hits)} old path(s)")
    return "\n".join(lines) + "\n"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Migrate legacy amendments into experiments/ layout.")
    parser.add_argument("--root", default=None, help="repo root (default: discovered from cwd)")
    parser.add_argument("--apply", action="store_true", help="write files and rewrite references")
    parser.add_argument("--json", action="store_true", help="emit plan JSON instead of text summary")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    root = Path(args.root).resolve() if args.root else repo_root()
    try:
        records = legacy_records(root)
        validate_plan(root, records, apply=args.apply)
        mapping = path_map(records)
        rewrites = planned_rewrites(root, mapping)
        payload = {"records": records, "path_map": mapping, "rewrites": rewrites}
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True, default=str))
        else:
            print(render_summary(root, records, rewrites), end="")
        if args.apply:
            apply_migration(root, records, mapping)
            print(f"migrated {len(records)} legacy amendment(s)")
        return 0
    except MigrationError as exc:
        print(f"error: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
