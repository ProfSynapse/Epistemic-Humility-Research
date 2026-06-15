#!/usr/bin/env python3
"""Canonical-source sync + drift-check for the experiment-runner skill tree.

Location: sync_skills.py (repo root — operates ACROSS the three skill trees and
    is NOT itself a synced skill file, so it lives above them).
Purpose: `.skills/` is the SINGLE canonical source for the experiment-runner
    skill. `.claude/skills/` and `.agents/skills/` are GENERATED MIRRORS of it.
    This script propagates the canonical source to both mirrors (`--write`) and
    verifies the three trees agree (`--check`, the drift-check / CI gate).

Why this exists (architecture §7): the two historical trees (`.agents/`,
    `.claude/`) drifted with no sync mechanism — `.agents/` was strictly AHEAD
    (extra script, bug-fixes, fuller SKILL.md). The fix is one canonical source
    (`.skills/`, seeded from `.agents/`) plus a mechanical sync so all new code
    is authored ONCE and propagated, never hand-edited into a single mirror.

rtk gotcha (architecture §7.1, recorded for operators): a `rtk`-proxied `diff`
    returns a FALSE `[ok] Files are identical` banner even when files differ.
    NEVER trust the proxied `diff` to compare these trees. This script compares
    via sha256 over CRLF-NORMALIZED content (see _content_sha), which is immune
    to both the proxied-diff false-positive and to line-ending churn.

Content-only / no-CRLF-churn discipline: `--write` LF-normalizes on copy, so the
    mirrors never gain CRLF that the canonical source lacks (honoring the
    content-only-diff constraint).

Usage:
    python3 sync_skills.py --check          # default: drift-check, exit 1 on drift
    python3 sync_skills.py --write          # propagate canonical -> both mirrors
    python3 sync_skills.py --check --skill experiment-runner   # scope to one skill
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

# Repo root is this script's own directory (sync_skills.py lives at repo root).
REPO_ROOT = Path(__file__).resolve().parent

# The canonical source tree and the two generated mirrors. The canonical source
# is authoritative; mirrors are overwritten by --write and never edited directly.
CANONICAL_ROOT = REPO_ROOT / ".skills"
MIRROR_ROOTS = (
    REPO_ROOT / ".claude" / "skills",
    REPO_ROOT / ".agents" / "skills",
)

# Transient / generated artifacts that are NOT part of the canonical skill source
# and must never be synced or counted as drift. pytest writes __pycache__/*.pyc
# into whichever tree it runs from; treating those as canonical files would copy
# them into the mirrors and make the drift-check flap. We track SOURCE only.
_IGNORED_DIR_NAMES = frozenset({"__pycache__", ".pytest_cache"})
_IGNORED_SUFFIXES = (".pyc", ".pyo")


def _is_ignored(rel_path: Path) -> bool:
    """True if a tree-relative path is a transient artifact, not skill source."""
    if any(part in _IGNORED_DIR_NAMES for part in rel_path.parts):
        return True
    return rel_path.suffix in _IGNORED_SUFFIXES


def _content_sha(path: Path) -> str:
    """sha256 over CRLF-normalized file bytes.

    Normalizing CRLF -> LF (and lone CR -> LF) before hashing makes the
    comparison line-ending-agnostic, so a tree that only differs by line endings
    is reported as IN SYNC (and --write never introduces CRLF). This is the
    rtk-proxied-diff-proof comparison the architecture mandates (§7.1).
    """
    raw = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(raw).hexdigest()


def _normalized_bytes(path: Path) -> bytes:
    """LF-normalized file bytes (the canonical on-disk form for every tree)."""
    return path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def _iter_skill_dirs(root: Path, skill: str | None) -> list[str]:
    """Return the skill subdir names under a tree root (optionally one skill)."""
    if not root.is_dir():
        return []
    if skill is not None:
        return [skill] if (root / skill).is_dir() else []
    return sorted(p.name for p in root.iterdir() if p.is_dir())


def _relative_files(skill_dir: Path) -> set[str]:
    """POSIX-relative paths of every file under a skill dir (stable, sorted)."""
    return {
        p.relative_to(skill_dir).as_posix()
        for p in skill_dir.rglob("*")
        if p.is_file() and not _is_ignored(p.relative_to(skill_dir))
    }


def write_skill(skill: str) -> int:
    """Copy canonical .skills/<skill>/** to every mirror, LF-normalized.

    Returns the number of files written across all mirrors. Mirror files that no
    longer exist in the canonical source are removed so the mirror is an exact
    image (no stale leftovers).
    """
    canonical_dir = CANONICAL_ROOT / skill
    if not canonical_dir.is_dir():
        raise FileNotFoundError(
            f"canonical source {canonical_dir} does not exist; author the skill "
            f"under .skills/ first, then sync"
        )
    canonical_files = _relative_files(canonical_dir)
    written = 0
    for mirror_root in MIRROR_ROOTS:
        mirror_dir = mirror_root / skill
        # Write/overwrite every canonical file (LF-normalized).
        for rel in sorted(canonical_files):
            src = canonical_dir / rel
            target = mirror_dir / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(_normalized_bytes(src))
            written += 1
        # Prune stale mirror files not present in the canonical source.
        if mirror_dir.is_dir():
            for rel in _relative_files(mirror_dir) - canonical_files:
                (mirror_dir / rel).unlink()
    return written


def check_skill(skill: str) -> list[str]:
    """Compare canonical vs every mirror for one skill (CRLF-normalized sha256).

    Returns a list of human-readable drift descriptions; an empty list means the
    skill is in sync across all three trees.
    """
    drift: list[str] = []
    canonical_dir = CANONICAL_ROOT / skill
    if not canonical_dir.is_dir():
        return [f"canonical source missing: {canonical_dir}"]
    canonical_files = _relative_files(canonical_dir)
    canonical_sha = {rel: _content_sha(canonical_dir / rel) for rel in canonical_files}

    for mirror_root in MIRROR_ROOTS:
        mirror_dir = mirror_root / skill
        if not mirror_dir.is_dir():
            drift.append(f"mirror missing entirely: {mirror_dir}")
            continue
        mirror_files = _relative_files(mirror_dir)
        for rel in sorted(canonical_files - mirror_files):
            drift.append(f"{mirror_dir / rel}: present in canonical, absent in mirror")
        for rel in sorted(mirror_files - canonical_files):
            drift.append(f"{mirror_dir / rel}: present in mirror, absent in canonical")
        for rel in sorted(canonical_files & mirror_files):
            if _content_sha(mirror_dir / rel) != canonical_sha[rel]:
                drift.append(f"{mirror_dir / rel}: content differs from canonical")
    return drift


def _resolve_skills(skill: str | None) -> list[str]:
    """The set of skills to operate on (canonical source is the SSOT for names)."""
    skills = _iter_skill_dirs(CANONICAL_ROOT, skill)
    if not skills:
        scope = f" {skill!r}" if skill else ""
        raise FileNotFoundError(
            f"no skill{scope} found under canonical source {CANONICAL_ROOT}"
        )
    return skills


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Sync the canonical .skills/ tree to .claude/ and .agents/, "
        "or drift-check that the three trees agree (sha256 on CRLF-normalized "
        "content — never the rtk-proxied diff)."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--check", action="store_true",
        help="(default) compare the trees; exit 1 on any drift.",
    )
    mode.add_argument(
        "--write", action="store_true",
        help="copy canonical .skills/ -> both mirrors (LF-normalized).",
    )
    parser.add_argument(
        "--skill", default=None,
        help="scope to one skill (default: every skill under .skills/).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    skills = _resolve_skills(args.skill)

    if args.write:
        total = 0
        for skill in skills:
            total += write_skill(skill)
        print(f"sync_skills: wrote {total} file(s) across "
              f"{len(MIRROR_ROOTS)} mirror(s) for skill(s): {', '.join(skills)}")
        return 0

    # Default mode is --check (drift-check / CI gate).
    all_drift: list[str] = []
    for skill in skills:
        all_drift.extend(check_skill(skill))
    if all_drift:
        print("sync_skills: DRIFT detected (run `python3 sync_skills.py --write`):")
        for line in all_drift:
            print(f"  - {line}")
        return 1
    print(f"sync_skills: in sync — canonical .skills/ matches both mirrors for "
          f"skill(s): {', '.join(skills)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
