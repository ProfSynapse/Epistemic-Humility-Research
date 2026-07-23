#!/usr/bin/env python3
"""Harvest gitignored experiment data from every worktree into the MAIN
checkout, so merged-and-removed worktrees never take sole-copy row-level
data (runlogs, pools, graded rows) with them.

Invoked automatically by .githooks/post-merge (fires on every `git pull`
that merges, in any worktree) and runnable by hand:

    python3 bin/harvest_worktree_data.py            # harvest + report
    python3 bin/harvest_worktree_data.py --check    # report only, exit 1 if
                                                    # any worktree holds
                                                    # unharvested data
    python3 bin/harvest_worktree_data.py --quiet    # hook mode

Semantics (deliberately conservative):
- Scope: files reported by `git ls-files --others --ignored
  --exclude-standard` under experiments/ in each non-main worktree.
- Destination: the SAME relative path inside the main checkout.
- Never overwrites: identical files (size+mtime, hash on suspicion) are
  skipped; a differing destination file is left untouched and the source is
  copied to <dest>.harvest-conflict-<utc-stamp> with a loud warning.
- Symlinks are materialized: the link TARGET's content is copied (real
  file), because symlinked staging into sibling worktrees is exactly the
  failure mode this exists to prevent. Dangling links are reported, not
  fatal.
- Exit code is always 0 in hook mode so a harvest problem can never block
  or corrupt a merge; problems go to stderr and the harvest log.

A manifest of every action is appended to
<main>/analysis/harvest/harvest_log.jsonl (gitignored).

Incident that motivated this: 2026-07-17, a merged-worktree cleanup sweep
deleted the gitignored staging pools that margin-mapping (M1) symlinked,
plus row-level runlogs of resolved experiments. Committed evidence was
safe; the data-exhaust layer was not. See the session note of that date.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

SCOPE_PREFIXES = ("experiments/",)

# Regenerable build/tool caches are not data; never harvest them.
EXCLUDE_PARTS = {"__pycache__", ".pytest_cache", "unsloth_compiled_cache", ".mypy_cache", ".ruff_cache"}
EXCLUDE_SUFFIXES = (".pyc", ".pyo")


def excluded(rel: str) -> bool:
    parts = rel.split("/")
    return bool(EXCLUDE_PARTS.intersection(parts)) or rel.endswith(EXCLUDE_SUFFIXES)


def sh(args: list[str], cwd: Path | None = None) -> str:
    return subprocess.run(
        args, cwd=cwd, check=True, capture_output=True, text=True
    ).stdout


def main_checkout() -> Path:
    # First entry of `git worktree list --porcelain` is the main working tree.
    out = sh(["git", "worktree", "list", "--porcelain"])
    first = out.splitlines()[0]
    assert first.startswith("worktree "), first
    return Path(first.split(" ", 1)[1])


def all_worktrees() -> list[Path]:
    out = sh(["git", "worktree", "list", "--porcelain"])
    return [Path(l.split(" ", 1)[1]) for l in out.splitlines() if l.startswith("worktree ")]


def ignored_data_files(wt: Path) -> list[str]:
    try:
        out = sh(
            ["git", "ls-files", "--others", "--ignored", "--exclude-standard", "--"]
            + list(SCOPE_PREFIXES),
            cwd=wt,
        )
    except subprocess.CalledProcessError:
        return []
    return [l for l in out.splitlines() if l]


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def same_content(a: Path, b: Path) -> bool:
    sa, sb = a.stat(), b.stat()
    if sa.st_size != sb.st_size:
        return False
    if int(sa.st_mtime) == int(sb.st_mtime):
        return True
    return sha256_of(a) == sha256_of(b)


def harvest(check_only: bool, quiet: bool) -> int:
    main = main_checkout()
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    log_dir = main / "analysis" / "harvest"
    actions: list[dict] = []
    unharvested = 0

    def note(**kw):
        actions.append({"ts": stamp, **kw})
        if not quiet:
            print(f"[harvest] {kw['action']:>9}  {kw.get('worktree','')}  {kw['path']}", file=sys.stderr)

    for wt in all_worktrees():
        if wt == main:
            continue
        if not wt.is_dir():
            continue
        for rel in ignored_data_files(wt):
            if excluded(rel):
                continue
            # An experiments/<slug>/ dir may only be created in main once the
            # experiment is merged (exp validate requires experiment.yaml);
            # pre-merge harvests park under analysis/harvest/pending/ and are
            # re-homed by a later harvest after the merge lands.
            parts = rel.split("/")
            unmerged_experiment = (
                len(parts) > 2
                and parts[0] == "experiments"
                and not (main / "experiments" / parts[1] / "experiment.yaml").is_file()
            )
            src = wt / rel
            if unmerged_experiment:
                dest = main / "analysis" / "harvest" / "pending" / rel
            else:
                dest = main / rel
            wt_name = wt.name
            if src.is_symlink():
                target = src.resolve()
                if not target.is_file():
                    note(action="dangling", worktree=wt_name, path=rel)
                    continue
                src = target  # materialize content
            elif not src.is_file():
                continue
            if dest.exists():
                if same_content(src, dest):
                    continue
                unharvested += 1
                if check_only:
                    note(action="conflict", worktree=wt_name, path=rel)
                    continue
                conflict = dest.with_name(dest.name + f".harvest-conflict-{stamp}")
                if src.stat().st_mtime > dest.stat().st_mtime:
                    # live worktree copy is newer: it supersedes the backup,
                    # but the old backup is preserved, never destroyed.
                    shutil.copy2(dest, conflict)
                    shutil.copy2(src, dest)
                    note(action="updated", worktree=wt_name, path=rel)
                else:
                    shutil.copy2(src, conflict)
                    note(action="conflict", worktree=wt_name, path=rel)
                continue
            unharvested += 1
            if check_only:
                note(action="pending", worktree=wt_name, path=rel)
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            note(action="copied", worktree=wt_name, path=rel)

    if actions and not check_only:
        log_dir.mkdir(parents=True, exist_ok=True)
        with open(log_dir / "harvest_log.jsonl", "a", encoding="utf-8") as f:
            for a in actions:
                f.write(json.dumps(a) + "\n")

    copied = sum(1 for a in actions if a["action"] in ("copied", "updated"))
    conflicts = sum(1 for a in actions if a["action"] == "conflict")
    dangling = sum(1 for a in actions if a["action"] == "dangling")
    if not quiet or conflicts or dangling:
        print(
            f"[harvest] done: {copied} copied, {conflicts} conflicts, "
            f"{dangling} dangling symlinks, main={main}",
            file=sys.stderr,
        )
    if check_only and unharvested:
        return 1
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report only; exit 1 if unharvested data exists")
    ap.add_argument("--quiet", action="store_true", help="hook mode: only summarize problems")
    args = ap.parse_args()
    try:
        raise SystemExit(harvest(args.check, args.quiet))
    except Exception as e:  # a harvest failure must never block git
        print(f"[harvest] ERROR (non-fatal to git): {e}", file=sys.stderr)
        raise SystemExit(0)
