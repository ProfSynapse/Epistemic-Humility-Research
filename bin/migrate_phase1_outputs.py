#!/usr/bin/env python3
"""Classify and (optionally) move the untracked experiment/ output tree.

The tree at repo-root ``experiment/`` (~100GB, entirely untracked) mixes three
kinds of content that accreted while the Phase 1 pipeline ran and while
amendment cells reused it for scratch: per-amendment analysis/eval outputs
that belong with their owning ``experiments/<slug>/``, shared Phase 1
infrastructure (checkpoint probe extraction, run records, data staging,
configs, logs) that has no single owning amendment, and disposable build
junk (Python bytecode caches, a marimo dashboard export, and directories left
empty once that junk is removed).

This script is a deterministic classifier + mover:

* ``--dry-run`` (default): walks the tree, classifies every entry, and writes
  a JSON manifest plus prints a summary. Moves nothing, deletes nothing.
* ``--execute``: performs the moves/deletions the same classifier produced.
  Idempotent: entries whose source no longer exists are skipped as
  already-migrated; entries whose destination already exists are reported as
  a collision and left untouched rather than overwritten.

Classification rules (see docs/migrations/phase1-outputs-migration-20260712.md
for the full rationale) are keyed off directory-name shape, matched against
the amendment letter -> slug mapping built from ``experiments/registry.json``
(``legacy.label`` field). A directory only becomes PER-AMENDMENT when its
name's leading token matches a mapped letter exactly; anything else is SHARED
rather than guessed.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EXPERIMENT_ROOT = REPO_ROOT / "experiment"
PHASE1_ROOT = EXPERIMENT_ROOT / "phase1"
EXPERIMENTS_ROOT = REPO_ROOT / "experiments"
ARCHIVE_SHARED_ROOT = REPO_ROOT / "archive" / "experiment" / "phase1-data"
REGISTRY_PATH = REPO_ROOT / "experiments" / "registry.json"

# Marimo dashboard export + PWA boilerplate under experiment/phase1/probe/
# directly. Matches the precedent already established for the frozen legacy
# copy at archive/experiment/phase1/probe/ (.gitignore lines documenting it
# as "marimo dashboard runtime cache + exported web bundle boilerplate
# (regenerable)") -- CLAUDE.md/.nojekyll/manifest.json are grouped there too.
PROBE_ROOT_JUNK_FILES = {
    ".nojekyll",
    "CLAUDE.md",
    "android-chrome-192x192.png",
    "android-chrome-512x512.png",
    "apple-touch-icon.png",
    "favicon-16x16.png",
    "favicon-32x32.png",
    "favicon.ico",
    "logo.png",
    "manifest.json",
    "sae_dashboard.html",
    "sae_dashboard.py",
    "site.webmanifest",
}
PROBE_ROOT_JUNK_DIRS = {"__marimo__"}
GLOBAL_JUNK_DIRNAME = "__pycache__"

# Bounded to 1-2 lowercase letters: every key in the letter->slug map is a
# single letter (B-Z) or a two-letter code (AA-AN, SR), so a longer prefix
# token (e.g. "current_clean_...", "radial_ceiling_...") can never resolve
# and is excluded up front rather than reported as a noisy false-positive
# "letter-shaped" candidate.
AMENDMENT_PREFIX_RE = re.compile(r"^amendment_([a-z]{1,2})(?:_|$)")
RESULTS_AMENDMENT_PREFIX_RE = re.compile(r"^results_amendment_([a-z]{1,2})(?:_|$)")
GENERIC_FIRST_TOKEN_RE = re.compile(r"^([a-z]{1,2})_")


def load_letter_map() -> dict[str, str]:
    """Letter -> slug, built from experiments/registry.json legacy.label."""
    data = json.loads(REGISTRY_PATH.read_text())
    mapping: dict[str, str] = {}
    for exp in data["experiments"]:
        legacy = exp.get("legacy") or {}
        label = legacy.get("label")
        slug = exp.get("slug")
        if label and slug:
            mapping[label] = slug
    return mapping


def extract_letter(name: str, mode: str) -> str | None:
    if mode == "amendment_prefix":
        m = AMENDMENT_PREFIX_RE.match(name)
    elif mode == "results_amendment_prefix":
        m = RESULTS_AMENDMENT_PREFIX_RE.match(name)
    elif mode == "generic_first_token":
        m = GENERIC_FIRST_TOKEN_RE.match(name)
    else:
        raise ValueError(mode)
    return m.group(1).upper() if m else None


@dataclass
class Entry:
    src: Path
    kind: str  # "per-amendment" | "shared" | "junk-delete"
    dest: Path | None
    size_bytes: int = 0
    file_count: int = 0
    slug: str | None = None
    candidate_letter: str | None = None  # letter-shaped token that did NOT map
    note: str = ""
    status: str = "planned"  # planned | collision | already-migrated | moved | deleted


def du_bytes(path: Path) -> tuple[int, int]:
    """Total size and file count of path (file or directory), via os.scandir."""
    if path.is_file():
        return path.stat().st_size, 1
    total_size = 0
    total_files = 0
    stack = [path]
    while stack:
        cur = stack.pop()
        try:
            with __import__("os").scandir(cur) as it:
                for e in it:
                    if e.is_dir(follow_symlinks=False):
                        stack.append(Path(e.path))
                    elif e.is_file(follow_symlinks=False):
                        total_files += 1
                        total_size += e.stat(follow_symlinks=False).st_size
        except FileNotFoundError:
            continue
    return total_size, total_files


def has_any_file(path: Path) -> bool:
    if path.is_file():
        return True
    for _root, _dirs, files in __import__("os").walk(path):
        if files:
            return True
    return False


def classify_probe_analysis_child(name: str, letter_map: dict[str, str]) -> tuple[str | None, str | None]:
    letter = extract_letter(name, "amendment_prefix")
    if letter is None:
        letter = extract_letter(name, "generic_first_token")
    if letter and letter in letter_map:
        return letter_map[letter], None
    return None, letter


def classify_probe_root_child(name: str, letter_map: dict[str, str]) -> tuple[str | None, str | None]:
    letter = extract_letter(name, "generic_first_token")
    if letter and letter in letter_map:
        return letter_map[letter], None
    return None, letter


def classify_eval_child(name: str, letter_map: dict[str, str]) -> tuple[str | None, str | None]:
    letter = extract_letter(name, "results_amendment_prefix")
    if letter and letter in letter_map:
        return letter_map[letter], None
    return None, letter


def per_amendment_dest(slug: str, rel_under_phase1: Path) -> Path:
    return EXPERIMENTS_ROOT / slug / "analysis" / "phase1-migrated" / rel_under_phase1


def shared_dest(rel_under_phase1: Path) -> Path:
    return ARCHIVE_SHARED_ROOT / rel_under_phase1


def build_plan(letter_map: dict[str, str]) -> list[Entry]:
    entries: list[Entry] = []

    # --- global __pycache__ junk, anywhere under experiment/ ---
    pycache_dirs: list[Path] = []
    if EXPERIMENT_ROOT.is_dir():
        for root, dirs, _files in __import__("os").walk(EXPERIMENT_ROOT):
            if GLOBAL_JUNK_DIRNAME in dirs:
                pycache_dirs.append(Path(root) / GLOBAL_JUNK_DIRNAME)
                dirs.remove(GLOBAL_JUNK_DIRNAME)  # do not descend into it
    for p in pycache_dirs:
        entries.append(Entry(src=p, kind="junk-delete", dest=None, note="__pycache__"))

    # --- probe/ root junk (marimo export + PWA boilerplate) ---
    probe_root = PHASE1_ROOT / "probe"
    junk_probe_root_paths: set[Path] = set()
    if probe_root.is_dir():
        for fname in PROBE_ROOT_JUNK_FILES:
            p = probe_root / fname
            if p.exists():
                entries.append(Entry(src=p, kind="junk-delete", dest=None, note="probe-root boilerplate"))
                junk_probe_root_paths.add(p)
        for dname in PROBE_ROOT_JUNK_DIRS:
            p = probe_root / dname
            if p.exists():
                entries.append(Entry(src=p, kind="junk-delete", dest=None, note="probe-root boilerplate"))
                junk_probe_root_paths.add(p)

    junk_paths = set(pycache_dirs) | junk_probe_root_paths

    def is_junked(p: Path) -> bool:
        return p in junk_paths

    # --- probe/analysis/<child> ---
    probe_analysis = probe_root / "analysis"
    if probe_analysis.is_dir():
        for child in sorted(probe_analysis.iterdir()):
            if child.name == GLOBAL_JUNK_DIRNAME or is_junked(child):
                continue
            slug, cand = classify_probe_analysis_child(child.name, letter_map)
            rel = child.relative_to(PHASE1_ROOT)
            if slug:
                entries.append(Entry(src=child, kind="per-amendment", dest=per_amendment_dest(slug, rel), slug=slug))
            else:
                entries.append(Entry(src=child, kind="shared", dest=shared_dest(rel), candidate_letter=cand))

    # --- probe/<child> (excluding analysis, junk) ---
    if probe_root.is_dir():
        for child in sorted(probe_root.iterdir()):
            if child.name in {"analysis", GLOBAL_JUNK_DIRNAME}:
                continue
            if is_junked(child):
                continue
            slug, cand = classify_probe_root_child(child.name, letter_map)
            rel = child.relative_to(PHASE1_ROOT)
            if slug:
                entries.append(Entry(src=child, kind="per-amendment", dest=per_amendment_dest(slug, rel), slug=slug))
            else:
                entries.append(Entry(src=child, kind="shared", dest=shared_dest(rel), candidate_letter=cand))

    # --- eval/<child> ---
    eval_root = PHASE1_ROOT / "eval"
    if eval_root.is_dir():
        for child in sorted(eval_root.iterdir()):
            if child.name == GLOBAL_JUNK_DIRNAME or is_junked(child):
                continue
            slug, cand = classify_eval_child(child.name, letter_map)
            rel = child.relative_to(PHASE1_ROOT)
            if slug:
                entries.append(Entry(src=child, kind="per-amendment", dest=per_amendment_dest(slug, rel), slug=slug))
            else:
                entries.append(Entry(src=child, kind="shared", dest=shared_dest(rel), candidate_letter=cand))

    # --- data/, grpo/, run_records/, tools/ : always shared at this depth ---
    for sub in ("data", "grpo", "run_records", "tools"):
        sub_root = PHASE1_ROOT / sub
        if not sub_root.is_dir():
            continue
        for child in sorted(sub_root.iterdir()):
            if child.name == GLOBAL_JUNK_DIRNAME or is_junked(child):
                continue
            rel = child.relative_to(PHASE1_ROOT)
            entries.append(Entry(src=child, kind="shared", dest=shared_dest(rel)))

    # --- phase1/analysis/* (only __pycache__ observed; handled generically) ---
    p1_analysis = PHASE1_ROOT / "analysis"
    if p1_analysis.is_dir():
        for child in sorted(p1_analysis.iterdir()):
            if child.name == GLOBAL_JUNK_DIRNAME or is_junked(child):
                continue
            rel = child.relative_to(PHASE1_ROOT)
            entries.append(Entry(src=child, kind="shared", dest=shared_dest(rel)))

    # --- experiment/paper, experiment/experiment: no per-amendment content;
    #     any surviving (non-junk) file would be a real find worth a human
    #     look, so surface it as shared rather than silently dropping it. ---
    for extra in ("paper", "experiment"):
        extra_root = EXPERIMENT_ROOT / extra
        if not extra_root.is_dir():
            continue
        for root, dirs, files in __import__("os").walk(extra_root):
            root_path = Path(root)
            if GLOBAL_JUNK_DIRNAME in dirs:
                dirs.remove(GLOBAL_JUNK_DIRNAME)
            for f in files:
                fp = root_path / f
                rel = fp.relative_to(EXPERIMENT_ROOT)
                entries.append(Entry(src=fp, kind="shared", dest=ARCHIVE_SHARED_ROOT.parent / rel, note="outside phase1/"))

    # --- empty-directory cascade: anything left with zero files anywhere in
    #     its subtree, after the junk above is notionally removed, is junk. ---
    already_classified = {e.src for e in entries}

    def effectively_empty(path: Path) -> bool:
        for root, dirs, files in __import__("os").walk(path):
            root_path = Path(root)
            if root_path in already_classified and root_path != path:
                dirs[:] = []
                continue
            if any((root_path / f) for f in files) and files:
                # any real file not already claimed by a classified entry
                unclaimed = [f for f in files if (root_path / f) not in already_classified]
                if unclaimed:
                    return False
            dirs[:] = [d for d in dirs if (root_path / d) not in already_classified]
        return True

    empty_dir_entries: list[Entry] = []
    for candidate in (EXPERIMENT_ROOT / "experiment", EXPERIMENT_ROOT / "paper", PHASE1_ROOT / "analysis"):
        if candidate.is_dir() and effectively_empty(candidate):
            empty_dir_entries.append(Entry(src=candidate, kind="junk-delete", dest=None, note="empty after junk removal"))

    entries.extend(empty_dir_entries)

    return entries


def size_entries(entries: list[Entry]) -> None:
    for e in entries:
        if e.src.exists():
            e.size_bytes, e.file_count = du_bytes(e.src)


def check_collisions(entries: list[Entry]) -> None:
    for e in entries:
        if e.dest is not None and e.dest.exists():
            e.status = "collision"


def check_already_migrated(entries: list[Entry]) -> None:
    for e in entries:
        if not e.src.exists():
            e.status = "already-migrated"


def git_head_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True).strip()
    except Exception:
        return "unknown"


def git_blob_sha(path: Path) -> str:
    try:
        return subprocess.check_output(["git", "hash-object", str(path)], cwd=REPO_ROOT, text=True).strip()
    except Exception:
        return "unknown"


def to_manifest_dict(entries: list[Entry], letter_map: dict[str, str]) -> dict:
    def rel_to_repo(p: Path | None) -> str | None:
        if p is None:
            return None
        try:
            return str(p.relative_to(REPO_ROOT))
        except ValueError:
            return str(p)

    return {
        "provenance": {
            "repo_head_sha": git_head_sha(),
            "registry_json_blob_sha": git_blob_sha(REGISTRY_PATH),
            "letter_map_size": len(letter_map),
        },
        "letter_map": letter_map,
        "entries": [
            {
                "src": rel_to_repo(e.src),
                "kind": e.kind,
                "dest": rel_to_repo(e.dest),
                "slug": e.slug,
                "candidate_letter": e.candidate_letter,
                "size_bytes": e.size_bytes,
                "file_count": e.file_count,
                "note": e.note,
                "status": e.status,
            }
            for e in entries
        ],
    }


def print_summary(entries: list[Entry]) -> None:
    by_kind: dict[str, list[Entry]] = {}
    for e in entries:
        by_kind.setdefault(e.kind, []).append(e)

    def fmt_gb(n: int) -> str:
        return f"{n / (1024**3):.2f} GB"

    total_size = sum(e.size_bytes for e in entries)
    print(f"\n=== TOTAL: {len(entries)} entries, {fmt_gb(total_size)} ===")
    for kind in ("per-amendment", "shared", "junk-delete"):
        group = by_kind.get(kind, [])
        size = sum(e.size_bytes for e in group)
        print(f"  {kind}: {len(group)} entries, {fmt_gb(size)}")

    per_amend = by_kind.get("per-amendment", [])
    if per_amend:
        print("\n  per-amendment by slug:")
        by_slug: dict[str, list[Entry]] = {}
        for e in per_amend:
            by_slug.setdefault(e.slug or "?", []).append(e)
        for slug, group in sorted(by_slug.items()):
            size = sum(e.size_bytes for e in group)
            print(f"    {slug}: {len(group)} entries, {fmt_gb(size)}")

    unmapped = [e for e in entries if e.kind == "shared" and e.candidate_letter]
    if unmapped:
        print(f"\n  shared-but-letter-shaped (unmapped, review these): {len(unmapped)}")
        for e in unmapped:
            print(f"    {e.src.relative_to(REPO_ROOT)} (candidate_letter={e.candidate_letter})")

    collisions = [e for e in entries if e.status == "collision"]
    if collisions:
        print(f"\n  COLLISIONS ({len(collisions)}):")
        for e in collisions:
            print(f"    {e.src.relative_to(REPO_ROOT)} -> {e.dest.relative_to(REPO_ROOT)}")

    already = [e for e in entries if e.status == "already-migrated"]
    if already:
        print(f"\n  already-migrated (source gone, skipped): {len(already)}")


def execute_plan(entries: list[Entry]) -> None:
    # Deletions first (leaf-most junk, e.g. __pycache__, before any empty-dir
    # cascade entries that depend on them being gone), then moves.
    junk = [e for e in entries if e.kind == "junk-delete" and e.status == "planned"]
    junk.sort(key=lambda e: len(e.src.parts), reverse=True)
    for e in junk:
        if not e.src.exists():
            e.status = "already-migrated"
            continue
        if e.src.is_dir():
            shutil.rmtree(e.src)
        else:
            e.src.unlink()
        e.status = "deleted"
        print(f"DELETED {e.src.relative_to(REPO_ROOT)}")

    movable = [e for e in entries if e.kind in ("per-amendment", "shared") and e.status == "planned"]
    for e in movable:
        if not e.src.exists():
            e.status = "already-migrated"
            continue
        if e.dest.exists():
            e.status = "collision"
            print(f"COLLISION (left in place): {e.src.relative_to(REPO_ROOT)} -> {e.dest.relative_to(REPO_ROOT)}")
            continue
        e.dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(e.src), str(e.dest))
        e.status = "moved"
        print(f"MOVED {e.src.relative_to(REPO_ROOT)} -> {e.dest.relative_to(REPO_ROOT)}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", help="Perform moves/deletions. Default is dry-run.")
    parser.add_argument(
        "--manifest-out",
        type=Path,
        default=REPO_ROOT / "docs" / "migrations" / "phase1-outputs-migration-20260712.manifest.json",
        help="Where to write the JSON manifest.",
    )
    args = parser.parse_args()

    letter_map = load_letter_map()
    entries = build_plan(letter_map)
    size_entries(entries)
    check_collisions(entries)
    check_already_migrated(entries)

    if args.execute:
        execute_plan(entries)
        # sizes/collisions may have changed status during execution; re-derive
        # for the post-run manifest snapshot.
    else:
        print("DRY RUN: no files moved or deleted. Pass --execute to apply this plan.")

    print_summary(entries)

    manifest = to_manifest_dict(entries, letter_map)
    args.manifest_out.parent.mkdir(parents=True, exist_ok=True)
    args.manifest_out.write_text(json.dumps(manifest, indent=2, sort_keys=False) + "\n")
    print(f"\nManifest written to {args.manifest_out.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
