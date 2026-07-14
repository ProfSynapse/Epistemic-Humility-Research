#!/usr/bin/env python3
"""Compact open-worktree risk report, designed for the post-commit nudge.

Scans every git worktree of this repository and reports only the risky ones:
  DIRTY        uncommitted tracked changes or untracked non-ignored files
  UNPUSHED     commits ahead of the branch's upstream
  NEVER-PUSHED branch has no upstream at all (nothing on origin)

If everything is clean and pushed, prints a single all-clear line. Intended to
be cheap enough to run after every commit; set EHR_SKIP_WORKTREE_NUDGE=1 to
silence it (e.g. inside scripted commit batches).

Standalone use: python3 bin/worktree_status.py [--verbose]
--verbose lists every worktree, not just risky ones.
"""
import os
import subprocess
import sys


def git(args, cwd=None):
    out = subprocess.run(
        ["git"] + args, cwd=cwd, capture_output=True, text=True, timeout=30
    )
    return out.returncode, out.stdout.strip()


def main():
    if os.environ.get("EHR_SKIP_WORKTREE_NUDGE") == "1":
        return 0
    verbose = "--verbose" in sys.argv

    rc, porcelain = git(["worktree", "list", "--porcelain"])
    if rc != 0:
        return 0  # never make a hook noisy on failure

    worktrees = []
    current = {}
    for line in porcelain.splitlines():
        if line.startswith("worktree "):
            if current:
                worktrees.append(current)
            current = {"path": line.split(" ", 1)[1]}
        elif line.startswith("branch "):
            current["branch"] = line.split(" ", 1)[1].replace("refs/heads/", "")
        elif line == "detached":
            current["branch"] = "(detached)"
    if current:
        worktrees.append(current)

    risky = []
    lines_verbose = []
    for wt in worktrees:
        path = wt["path"]
        branch = wt.get("branch", "?")
        flags = []
        rc, status = git(["status", "--porcelain"], cwd=path)
        if rc == 0 and status:
            flags.append("DIRTY:%d" % len(status.splitlines()))
        rc, ahead = git(
            ["rev-list", "--count", "@{upstream}..HEAD"], cwd=path
        )
        if rc != 0:
            if branch not in ("main", "(detached)", "?"):
                flags.append("NEVER-PUSHED")
        elif ahead not in ("", "0"):
            flags.append("UNPUSHED:%s" % ahead)
        name = os.path.basename(path)
        if flags:
            risky.append("  %-32s %-48s %s" % (name, branch, " ".join(flags)))
        if verbose:
            lines_verbose.append(
                "  %-32s %-48s %s" % (name, branch, " ".join(flags) or "clean")
            )

    if verbose:
        print("worktrees (%d):" % len(worktrees))
        print("\n".join(lines_verbose))
        return 0

    if risky:
        print("worktree nudge: %d open, %d need attention" % (len(worktrees), len(risky)))
        print("\n".join(risky))
        print(
            "  (DIRTY = uncommitted work; NEVER-PUSHED = exists only on this"
            " disk. Commit/push or retire before it strands.)"
        )
    else:
        print(
            "worktree nudge: %d open, all clean and pushed" % len(worktrees)
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
