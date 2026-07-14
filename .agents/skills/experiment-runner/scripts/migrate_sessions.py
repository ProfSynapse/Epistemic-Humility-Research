#!/usr/bin/env python3
"""Migrate legacy numbered research-session notes to timestamped filenames.

Default mode is dry-run. With --apply this script:

- renames docs/sessions/0001 - title.md to docs/sessions/YYYYMMDDTHHMMSSZ-title.md
- updates frontmatter session_id to the new filename stem
- preserves old identity under legacy_session
- rewrites exact old session paths across repo reference files
- writes docs/migration/session-path-map.json

Numeric shorthand references such as docs/sessions/0026 are reported. They are
not rewritten here because duplicate sequence numbers make some ambiguous.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

import yaml

SESSION_DIR = Path("docs") / "sessions"
MIGRATION_DIR = Path("docs") / "migration"
PATH_MAP = MIGRATION_DIR / "session-path-map.json"
LEGACY_FILENAME_RE = re.compile(r"^(?P<number>\d{4}) - (?P<title>[a-z0-9][a-z0-9-]*)\.md$")
TIMESTAMP_FILENAME_RE = re.compile(r"^\d{8}T\d{6}Z-[a-z0-9][a-z0-9_.-]*\.md$")
FRONTMATTER_RE = re.compile(r"\A---[ \t]*\r?\n(?P<body>.*?)\r?\n---(?:\r?\n|\Z)", re.S)
SHORTHAND_RE = re.compile(r"docs/sessions/(?P<number>\d{4})(?!\s-)(?:\b|[#/])")
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
SKIP_DIRS = {
    ".git",
    ".codex",
    ".kg",
    ".cache",
    ".mypy_cache",
    ".pytest_cache",
    "__pycache__",
    "synaptic-tuner",
}


class SessionMigrationError(Exception):
    pass


def repo_root(start: Path | None = None) -> Path:
    here = (start or Path.cwd()).resolve()
    for candidate in (here, *here.parents):
        if (candidate / ".git").exists():
            return candidate
    raise SessionMigrationError(f"no git repo root found above {here}")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def split_frontmatter(path: Path) -> tuple[dict[str, Any], str]:
    text = read_text(path)
    match = FRONTMATTER_RE.match(text)
    if not match:
        raise SessionMigrationError(f"session missing frontmatter: {path}")
    data = yaml.safe_load(match.group("body")) or {}
    if not isinstance(data, dict):
        raise SessionMigrationError(f"session frontmatter is not a mapping: {path}")
    return data, text[match.end():]


def render_frontmatter(data: dict[str, Any]) -> str:
    return "---\n" + yaml.safe_dump(data, sort_keys=False, allow_unicode=False).strip() + "\n---\n"


def compact_timestamp(value: str) -> str:
    match = re.match(r"^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})Z$", str(value))
    if not match:
        raise SessionMigrationError(f"created_at must be UTC ISO timestamp, got {value!r}")
    return "".join(match.groups()[:3]) + "T" + "".join(match.groups()[3:]) + "Z"


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


def session_records(root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in sorted((root / SESSION_DIR).glob("*.md")):
        if TIMESTAMP_FILENAME_RE.match(path.name):
            continue
        match = LEGACY_FILENAME_RE.match(path.name)
        if not match:
            continue
        data, _body = split_frontmatter(path)
        title_slug = match.group("title")
        stamp = compact_timestamp(str(data.get("created_at")))
        new_name = f"{stamp}-{title_slug}.md"
        old_rel = path.relative_to(root).as_posix()
        new_rel = (SESSION_DIR / new_name).as_posix()
        records.append(
            {
                "old_path": old_rel,
                "new_path": new_rel,
                "old_session_id": str(data.get("session_id") or ""),
                "new_session_id": new_name.removesuffix(".md"),
                "number": match.group("number"),
                "title": str(data.get("title") or title_slug),
            }
        )
    return records


def validate_plan(root: Path, records: list[dict[str, Any]], apply: bool) -> None:
    new_paths: set[str] = set()
    for record in records:
        if record["new_path"] in new_paths:
            raise SessionMigrationError(f"new path collision: {record['new_path']}")
        new_paths.add(record["new_path"])
        target = root / record["new_path"]
        if target.exists():
            raise SessionMigrationError(f"target already exists: {target}")
    if apply and not records:
        raise SessionMigrationError("no legacy session files to migrate")


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


def shorthand_refs(root: Path) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for path in reference_files(root):
        try:
            text = read_text(path)
        except UnicodeDecodeError:
            continue
        hits = sorted({match.group(0).rstrip("/#") for match in SHORTHAND_RE.finditer(text)})
        if hits:
            out[path.relative_to(root).as_posix()] = hits
    return out


def is_compatibility_shorthand(path: str) -> bool:
    """Return true for intentional legacy examples in the migration tool itself."""
    return bool(
        re.match(
            r"^(?:\.skills|\.agents/skills|\.claude/skills)/experiment-runner/"
            r"(?:scripts/migrate_sessions\.py|tests/test_migrate_sessions\.py)$",
            path,
        )
    )


def apply_migration(root: Path, records: list[dict[str, Any]], mapping: dict[str, str]) -> None:
    migrated_records: dict[str, dict[str, Any]] = {}
    for record in records:
        old = root / record["old_path"]
        new = root / record["new_path"]
        data, body = split_frontmatter(old)
        data["session_id"] = record["new_session_id"]
        data["legacy_session"] = {
            "id": record["old_session_id"],
            "path": record["old_path"],
        }
        migrated_records[record["new_path"]] = record
        new.write_text(render_frontmatter(data) + body.lstrip(), encoding="utf-8")
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

    (root / MIGRATION_DIR).mkdir(parents=True, exist_ok=True)
    (root / PATH_MAP).write_text(json.dumps(mapping, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    # Restore only legacy_session.path after the reference rewrite pass. Other
    # references inside migrated session notes should point at the new paths.
    for new_rel, record in migrated_records.items():
        path = root / new_rel
        data, body = split_frontmatter(path)
        legacy_session = data.setdefault("legacy_session", {})
        if not isinstance(legacy_session, dict):
            legacy_session = {}
            data["legacy_session"] = legacy_session
        legacy_session["path"] = record["old_path"]
        path.write_text(render_frontmatter(data) + body.lstrip(), encoding="utf-8")


def render_summary(records: list[dict[str, Any]], rewrites: dict[str, list[str]], shorthand: dict[str, list[str]]) -> str:
    active_shorthand = {
        path: hits for path, hits in shorthand.items() if not is_compatibility_shorthand(path)
    }
    compatibility_shorthand = {
        path: hits for path, hits in shorthand.items() if is_compatibility_shorthand(path)
    }
    lines = [
        "# Session migration plan",
        "",
        f"legacy session files: {len(records)}",
        f"exact reference files to rewrite: {len(rewrites)}",
        f"active files with numeric shorthand refs: {len(active_shorthand)}",
        f"compatibility files with numeric shorthand refs: {len(compatibility_shorthand)}",
        "",
        "## Targets",
    ]
    for record in records:
        lines.append(f"- {record['old_path']} -> {record['new_path']}")
    if rewrites:
        lines.append("")
        lines.append("## Exact Reference Files")
        for path, hits in sorted(rewrites.items()):
            lines.append(f"- {path}: {len(hits)} old path(s)")
    if active_shorthand:
        lines.append("")
        lines.append("## Numeric Shorthand References (manual review)")
        for path, hits in sorted(active_shorthand.items()):
            lines.append(f"- {path}: {', '.join(hits)}")
    if compatibility_shorthand:
        lines.append("")
        lines.append("## Compatibility Shorthand References")
        for path, hits in sorted(compatibility_shorthand.items()):
            lines.append(f"- {path}: {', '.join(hits)}")
    return "\n".join(lines) + "\n"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Migrate numbered session notes to timestamped filenames.")
    parser.add_argument("--root", default=None, help="repo root (default: discovered from cwd)")
    parser.add_argument("--apply", action="store_true", help="write files and rewrite exact path references")
    parser.add_argument("--json", action="store_true", help="emit plan JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    root = Path(args.root).resolve() if args.root else repo_root()
    try:
        records = session_records(root)
        validate_plan(root, records, apply=args.apply)
        mapping = path_map(records)
        rewrites = planned_rewrites(root, mapping)
        shorthand = shorthand_refs(root)
        payload = {
            "records": records,
            "path_map": mapping,
            "rewrites": rewrites,
            "shorthand_refs": shorthand,
        }
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True, default=str))
        else:
            print(render_summary(records, rewrites, shorthand), end="")
        if args.apply:
            apply_migration(root, records, mapping)
            print(f"migrated {len(records)} session note(s)")
        return 0
    except SessionMigrationError as exc:
        print(f"error: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
