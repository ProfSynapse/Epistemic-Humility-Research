#!/usr/bin/env python3
"""Read-only audit for experiment/session provenance migration.

This inventories legacy amendment files, experiments-first manifests, session
note identity issues, and Markdown links that will need updating during a full
migration into the experiments-first layout. It never edits files.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import yaml

SESSION_DIR = Path("docs") / "sessions"
LEGACY_PROTOCOL_DIR = Path("experiment") / "protocol"
EXPERIMENTS_DIR = Path("experiments")
LEGACY_AMENDMENT_RE = re.compile(r"^AMENDMENT-([A-Z0-9]+)-(.+)\.md$")
LEGACY_SESSION_FILENAME_RE = re.compile(r"^(\d{4}) - .+\.md$")
TIMESTAMP_SESSION_FILENAME_RE = re.compile(r"^\d{8}T\d{6}Z-.+\.md$")
SERIAL_ID_RE = re.compile(r"^\d+$")
FRONTMATTER_RE = re.compile(r"\A---[ \t]*\r?\n(?P<body>.*?)\r?\n---(?:\r?\n|\Z)", re.S)
LEGACY_LINK_RE = re.compile(r"experiment/protocol/AMENDMENT-[A-Z0-9][A-Za-z0-9-]*\.md")
EXPERIMENT_LINK_RE = re.compile(r"experiments/[a-z0-9][a-z0-9-]*/AMENDMENT\.md")
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
    ".kg",
    ".cache",
    ".mypy_cache",
    ".pytest_cache",
    "__pycache__",
    "synaptic-tuner",
}


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _frontmatter(path: Path) -> dict[str, Any]:
    try:
        text = _read_text(path)
    except OSError:
        return {}
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}
    data = yaml.safe_load(match.group("body")) or {}
    return data if isinstance(data, dict) else {}


def _first_heading(path: Path) -> str:
    try:
        for line in _read_text(path).splitlines():
            if line.startswith("# "):
                return line[2:].strip()
    except OSError:
        pass
    return ""


def _git_files(root: Path) -> list[Path]:
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


def _walk_files(root: Path) -> list[Path]:
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


def _iter_reference_files(root: Path) -> list[Path]:
    files = {path.resolve() for path in _git_files(root)}
    files.update(path.resolve() for path in _walk_files(root))
    return sorted(
        path
        for path in files
        if path.is_file()
        and path.suffix in REFERENCE_SUFFIXES
        and not any(part in SKIP_DIRS for part in path.relative_to(root).parts)
    )


def _area(rel: str) -> str:
    first = rel.split("/", 1)[0]
    if first == "library":
        return "library"
    if first == "experiment":
        return "experiment"
    if first == "experiments":
        return "experiments"
    if first == "docs":
        return "docs"
    if first in {".skills", ".agents", ".claude"}:
        return first
    return "other"


def _session_audit(root: Path) -> dict[str, Any]:
    session_dir = root / SESSION_DIR
    files = sorted(session_dir.glob("*.md")) if session_dir.is_dir() else []
    sequence_numbers: dict[str, list[str]] = defaultdict(list)
    session_ids: dict[str, list[str]] = defaultdict(list)
    legacy_filenames: list[str] = []
    serial_only_ids: list[dict[str, str]] = []
    nonstandard_filenames: list[str] = []

    for path in files:
        rel = path.relative_to(root).as_posix()
        sequence_match = LEGACY_SESSION_FILENAME_RE.match(path.name)
        if sequence_match:
            number = sequence_match.group(1)
            sequence_numbers[number].append(rel)
            legacy_filenames.append(rel)
        elif not TIMESTAMP_SESSION_FILENAME_RE.match(path.name):
            nonstandard_filenames.append(rel)

        session_id = _frontmatter(path).get("session_id")
        if isinstance(session_id, str):
            session_ids[session_id].append(rel)
            if SERIAL_ID_RE.match(session_id):
                serial_only_ids.append({"session_id": session_id, "path": rel})

    return {
        "count": len(files),
        "legacy_filename_count": len(legacy_filenames),
        "legacy_filenames": legacy_filenames,
        "nonstandard_filenames": nonstandard_filenames,
        "duplicate_sequence_numbers": {
            number: paths for number, paths in sorted(sequence_numbers.items()) if len(paths) > 1
        },
        "duplicate_session_ids": {
            session_id: paths for session_id, paths in sorted(session_ids.items()) if len(paths) > 1
        },
        "serial_only_session_ids": serial_only_ids,
    }


def _legacy_amendment_audit(root: Path) -> dict[str, Any]:
    protocol_dir = root / LEGACY_PROTOCOL_DIR
    files = sorted(protocol_dir.glob("AMENDMENT-*.md")) if protocol_dir.is_dir() else []
    records: list[dict[str, str]] = []
    labels: set[str] = set()
    for path in files:
        rel = path.relative_to(root).as_posix()
        match = LEGACY_AMENDMENT_RE.match(path.name)
        label = match.group(1) if match else ""
        if label:
            labels.add(label)
        fm = _frontmatter(path)
        stem_slug = match.group(2).removesuffix(".md") if match else path.stem
        records.append(
            {
                "label": str(fm.get("amendment") or label),
                "slug": str(fm.get("slug") or stem_slug),
                "status": str(fm.get("status") or ""),
                "path": rel,
                "title": _first_heading(path),
            }
        )
    return {"count": len(records), "labels": sorted(labels), "records": records}


def _experiments_audit(root: Path, legacy_labels: set[str]) -> dict[str, Any]:
    base = root / EXPERIMENTS_DIR
    manifests = sorted(base.glob("*/experiment.yaml")) if base.is_dir() else []
    records: list[dict[str, Any]] = []
    legacy_label_like: list[dict[str, str]] = []
    for manifest in manifests:
        rel = manifest.relative_to(root).as_posix()
        data = yaml.safe_load(_read_text(manifest)) or {}
        slug = str(data.get("slug") or manifest.parent.name)
        prefix = slug.split("-", 1)[0].upper() if "-" in slug else ""
        record = {
            "slug": slug,
            "title": str(data.get("title") or ""),
            "type": str(data.get("type") or ""),
            "status": str(data.get("status") or ""),
            "created_at": str(data.get("created_at") or ""),
            "path": rel,
        }
        records.append(record)
        # Single-letter labels (B-Z) collide with ordinary semantic prefixes
        # like j-space; only warn on multi-character legacy-like prefixes.
        if len(prefix) >= 2 and prefix in legacy_labels:
            legacy_label_like.append({"slug": slug, "prefix": prefix, "path": rel})
    return {
        "count": len(records),
        "records": records,
        "legacy_label_like_slugs": legacy_label_like,
    }


def _pinned_files(root: Path) -> set[str]:
    pinned: set[str] = set()
    base = root / EXPERIMENTS_DIR
    for manifest in sorted(base.glob("*/experiment.yaml")) if base.is_dir() else []:
        try:
            data = yaml.safe_load(_read_text(manifest)) or {}
        except (OSError, yaml.YAMLError):
            continue
        instrument = data.get("instrument") if isinstance(data, dict) else None
        pins = instrument.get("pins") if isinstance(instrument, dict) else None
        if not isinstance(pins, dict):
            continue
        for rel in pins:
            pinned.add((manifest.parent / str(rel)).resolve().relative_to(root).as_posix())
    return pinned


def _is_compatibility_legacy_link_file(rel: str, pinned_files: set[str]) -> bool:
    if rel == "docs/migration/experiment-path-map.json":
        return True
    if rel == "experiments/registry.json":
        return True
    if rel.startswith("experiments/") and rel.endswith("/experiment.yaml"):
        return True
    if rel in pinned_files:
        return True
    parts = rel.split("/")
    if len(parts) >= 4 and parts[0] in {".skills", ".agents", ".claude"} and "tests" in parts:
        return True
    return False


def _link_audit(root: Path) -> dict[str, Any]:
    legacy_counts: Counter[str] = Counter()
    experiment_counts: Counter[str] = Counter()
    area_counts: Counter[str] = Counter()
    active_legacy_counts: Counter[str] = Counter()
    active_legacy_by_file: dict[str, list[str]] = {}
    compatibility_legacy_by_file: dict[str, list[str]] = {}
    by_file: dict[str, dict[str, list[str]]] = {}
    pinned_files = _pinned_files(root)
    for path in _iter_reference_files(root):
        rel = path.relative_to(root).as_posix()
        try:
            text = _read_text(path)
        except UnicodeDecodeError:
            continue
        legacy = sorted(set(LEGACY_LINK_RE.findall(text)))
        current = sorted(set(EXPERIMENT_LINK_RE.findall(text)))
        if legacy or current:
            area_counts[_area(rel)] += 1
            by_file[rel] = {"legacy_amendment_links": legacy, "experiment_links": current}
            legacy_counts.update(legacy)
            experiment_counts.update(current)
            if legacy:
                if _is_compatibility_legacy_link_file(rel, pinned_files):
                    compatibility_legacy_by_file[rel] = legacy
                else:
                    active_legacy_by_file[rel] = legacy
                    active_legacy_counts.update(legacy)
    return {
        "files_with_links": len(by_file),
        "legacy_link_target_count": len(legacy_counts),
        "active_legacy_link_target_count": len(active_legacy_counts),
        "experiment_link_target_count": len(experiment_counts),
        "legacy_links": dict(sorted(legacy_counts.items())),
        "active_legacy_links": dict(sorted(active_legacy_counts.items())),
        "experiment_links": dict(sorted(experiment_counts.items())),
        "files_by_area": dict(sorted(area_counts.items())),
        "active_legacy_by_file": active_legacy_by_file,
        "compatibility_legacy_by_file": compatibility_legacy_by_file,
        "by_file": by_file,
    }


def audit(root: Path) -> dict[str, Any]:
    root = root.resolve()
    legacy = _legacy_amendment_audit(root)
    experiments = _experiments_audit(root, set(legacy["labels"]))
    sessions = _session_audit(root)
    links = _link_audit(root)
    return {
        "root": root.as_posix(),
        "sessions": sessions,
        "legacy_amendments": legacy,
        "experiments": experiments,
        "links": links,
    }


def render_text(report: dict[str, Any]) -> str:
    sessions = report["sessions"]
    legacy = report["legacy_amendments"]
    experiments = report["experiments"]
    links = report["links"]
    lines = [
        "# Provenance audit",
        "",
        f"root: {report['root']}",
        "",
        "## Sessions",
        f"- session files: {sessions['count']}",
        f"- legacy numbered filenames: {sessions['legacy_filename_count']}",
        f"- duplicate filename numbers: {len(sessions['duplicate_sequence_numbers'])}",
        f"- duplicate session ids: {len(sessions['duplicate_session_ids'])}",
        f"- serial-only session ids: {len(sessions['serial_only_session_ids'])}",
        f"- nonstandard filenames: {len(sessions['nonstandard_filenames'])}",
        "",
        "## Experiments",
        f"- experiments-first manifests: {experiments['count']}",
        f"- legacy amendment files: {legacy['count']}",
        f"- slugs that look like legacy labels: {len(experiments['legacy_label_like_slugs'])}",
        "",
        "## Links",
        f"- reference files with experiment/amendment links: {links['files_with_links']}",
        f"- linked files by area: {links['files_by_area']}",
        f"- distinct legacy amendment link targets: {links['legacy_link_target_count']}",
        f"- active legacy amendment link targets: {links['active_legacy_link_target_count']}",
        f"- distinct experiments-first link targets: {links['experiment_link_target_count']}",
    ]
    if sessions["duplicate_sequence_numbers"]:
        lines.append("")
        lines.append("## Duplicate Session Filename Numbers")
        for number, paths in sessions["duplicate_sequence_numbers"].items():
            lines.append(f"- {number}: " + "; ".join(paths))
    if sessions["duplicate_session_ids"]:
        lines.append("")
        lines.append("## Duplicate Session IDs")
        for session_id, paths in sessions["duplicate_session_ids"].items():
            lines.append(f"- {session_id}: " + "; ".join(paths))
    if experiments["legacy_label_like_slugs"]:
        lines.append("")
        lines.append("## Legacy-Like Experiment Slugs")
        for item in experiments["legacy_label_like_slugs"]:
            lines.append(f"- {item['slug']} ({item['prefix']}): {item['path']}")
    return "\n".join(lines) + "\n"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read-only provenance migration audit.")
    parser.add_argument("--root", default=".", help="repo root (default: cwd)")
    parser.add_argument("--json", action="store_true", help="emit full machine-readable JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    report = audit(Path(args.root))
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text(report), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
