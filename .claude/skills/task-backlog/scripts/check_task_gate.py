#!/usr/bin/env python3
"""Enforce change -> task traceability (the commit gate).

Port of syntunia's ``scripts/check-task-link.mjs`` behavior to this repo's
task-backlog schema. A "gated" file (see GATED_PREFIXES / docs/ carve-out
below) may only change when:

  1. an active task (in-progress / in-review) covers it -- via ``files:``,
     ``new_files:`` (trailing-slash prefix match), or ``component:`` prefix
     ('.' covers the whole repo), and
  2. that task's own file changed too -- or, in --staged mode, its
     ``updated_date`` is today.

Modes:
    --staged            pre-commit: checks `git diff --cached`
    --range <a...b>     CI: checks a PR diff range

Escape hatch: EHR_TASK_OK=1 (visible in the commit shell, greppable in CI logs).

Everything outside the gated scope is exempt, including: experiments/,
backlog/, TODO.md, docs/sessions/, generated skill mirrors (.agents/,
.claude/skills/), the synaptic-tuner submodule pointer, .claude/settings.json,
and analysis/.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import task as task_mod  # noqa: E402

# Gated scope: everything else is exempt.
GATED_PREFIXES = ("papers/", "bin/", ".skills/", ".githooks/", ".claude/hooks/")
DOCS_PREFIX = "docs/"
DOCS_SESSIONS_PREFIX = "docs/sessions/"

# Explicit exemptions, listed even where already non-overlapping with
# GATED_PREFIXES, so the exemption list is self-documenting.
EXEMPT_PREFIXES = ("experiments/", "backlog/", ".agents/", ".claude/skills/", "analysis/")
EXEMPT_FILES = frozenset({"TODO.md", ".claude/settings.json", "synaptic-tuner"})


def is_gated(f: str) -> bool:
    if f in EXEMPT_FILES:
        return False
    if f.startswith(EXEMPT_PREFIXES):
        return False
    if f.startswith(DOCS_PREFIX):
        return not f.startswith(DOCS_SESSIONS_PREFIX)
    return f.startswith(GATED_PREFIXES)


def covers(t: dict, f: str) -> bool:
    for s in (t.get("files") or []) + (t.get("new_files") or []):
        if s.endswith("/"):
            if f.startswith(s):
                return True
        elif s == f:
            return True
    component = t.get("component") or ""
    if component == ".":
        return True
    if component and (f == component or f.startswith(component.rstrip("/") + "/")):
        return True
    return False


def is_fresh(root: Path, t: dict, changed: set[str], today: str, staged_mode: bool) -> bool:
    task_rel = Path(t["_path"]).resolve().relative_to(root).as_posix()
    if task_rel in changed:
        return True
    # The "updated today" fallback only makes sense for the live pre-commit
    # check; a CI --range diff over historical commits has no "today".
    return staged_mode and t.get("updated_date") == today


def check(root: Path, changed: list[str], *, staged_mode: bool) -> list[str]:
    tasks = task_mod.iter_tasks(root)
    active = [t for t in tasks if t.get("status") in ("in-progress", "in-review")]
    today = task_mod.today()
    changed_set = set(changed)

    errors: list[str] = []
    for f in changed:
        if not is_gated(f):
            continue
        covering = [t for t in active if covers(t, f)]
        if not covering:
            errors.append(
                f"{f}: no active task covers this file.\n"
                "    -> claim one (`bin/task claim <id> --as @you`) or create "
                f'one (`bin/task new "..." --tier P --file {f}`), then retry.'
            )
            continue
        fresh = [t for t in covering if is_fresh(root, t, changed_set, today, staged_mode)]
        if not fresh:
            ids = ", ".join(t["id"] for t in covering)
            errors.append(
                f"{f}: covered by {ids}, but no covering task was updated "
                "with this change.\n"
                f"    -> stage the task file too, or run `bin/task review "
                f"{covering[0]['id']}` (or another status verb) to bump its "
                "updated_date to today."
            )
    return errors


def _git_lines(root: Path, args: list[str]) -> list[str]:
    out = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=True
    ).stdout
    return [line for line in out.splitlines() if line]


def main(argv: list[str] | None = None) -> int:
    if os.environ.get("EHR_TASK_OK") == "1":
        print("check_task_gate: skipped via EHR_TASK_OK=1")
        return 0

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=None)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--staged", action="store_true", help="pre-commit: check `git diff --cached`")
    mode.add_argument("--range", dest="range_spec", default=None, metavar="A...B", help="CI: check a diff range")
    args = ap.parse_args(argv)

    root = Path(args.root).resolve() if args.root else task_mod.find_repo_root()

    if args.staged:
        changed = _git_lines(root, ["diff", "--cached", "--name-only"])
        staged_mode = True
    else:
        changed = _git_lines(root, ["diff", "--name-only", args.range_spec])
        staged_mode = False

    gated_count = sum(1 for f in changed if is_gated(f))
    if gated_count == 0:
        return 0

    errors = check(root, changed, staged_mode=staged_mode)
    if errors:
        print("check_task_gate: changes are not traceable to an active task:\n", file=sys.stderr)
        for e in errors:
            print(f"  x {e}\n", file=sys.stderr)
        print("  (escape hatch for genuine emergencies: EHR_TASK_OK=1 git commit ...)", file=sys.stderr)
        return 1

    print(f"check_task_gate: OK -- {gated_count} gated file(s) traceable to an active task")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
