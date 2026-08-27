#!/usr/bin/env bash
# PreToolUse guard (Bash): a worktree may hold the SOLE COPY of gitignored
# experiment run data (runlogs with generation text, shard id maps, salts,
# staged pools). Removing the worktree destroys it silently.
#
# INCIDENT THIS PREVENTS: 2026-08-26, the lead merged the wide-rescore PR,
# synced main with `git pull --rebase` (which does NOT fire the post-merge
# harvest hook -- rebase fires post-rewrite), then ran
# `git worktree remove --force`, deleting the only copy of the run's
# row-level generation text before the data-exhaust step ran. The harvester
# (bin/harvest_worktree_data.py, built for the 2026-07-17 incident of the
# same class) existed but nothing forced it to run before the removal.
#
# BEHAVIOR: block `git worktree remove <path>` and `rm -r/-rf <path>` when
# <path> is a repo worktree (under ehr-worktrees/ or .worktrees/) that still
# holds unharvested gitignored experiment data. The scoped check is
# bin/harvest_worktree_data.py --check --worktree <path>, run from the main
# checkout; ANY nonzero exit blocks (fail closed -- an error must not
# greenlight deletion).
#
# REMEDY on block: run  python3 bin/harvest_worktree_data.py  from the main
# checkout (harvests every worktree, idempotent), then retry the removal.
# To deliberately destroy unharvested data instead, acknowledge with:
#     EHR_WT_DATA_OK=1 git worktree remove --force <path>
#
# FALSE-POSITIVE DISCIPLINE: fires only when (a) the command contains
# `git worktree remove` or `rm` with a recursive flag, (b) an argument
# resolves to an existing directory under */ehr-worktrees/* or
# */.worktrees/*, and (c) the scoped check finds unharvested data (or
# errors). Everything else is allowed untouched. Exit 2 -> blocked.
set -u

payload=$(cat)
result=$(HOOK_PAYLOAD="$payload" python3 - <<'PYEOF'
import json, os, re, shlex, subprocess
from pathlib import Path

def allow():
    print("ALLOW"); raise SystemExit

try:
    d = json.loads(os.environ.get("HOOK_PAYLOAD", ""))
except Exception:
    allow()
cmd = ((d.get("tool_input") or {}).get("command") or "")
cwd = d.get("cwd") or os.getcwd()
if not cmd.strip():
    allow()
if "EHR_WT_DATA_OK=" in cmd:
    allow()

# Cheap textual pre-filter before any parsing.
if not re.search(r"worktree\s+remove|\brm\b", cmd):
    allow()

try:
    tokens = shlex.split(cmd, posix=True)
except ValueError:
    tokens = cmd.split()

def is_wt_path(p: str) -> Path | None:
    try:
        rp = Path(p if os.path.isabs(p) else os.path.join(cwd, p)).resolve()
    except Exception:
        return None
    s = str(rp)
    if ("/ehr-worktrees/" in s or "/.worktrees/" in s) and rp.is_dir():
        return rp
    return None

targets: list[Path] = []
n = len(tokens)
for i, t in enumerate(tokens):
    if t == "worktree" and i + 1 < n and tokens[i + 1] == "remove":
        for a in tokens[i + 2:]:
            if a.startswith("-"):
                continue
            if a in (";", "&&", "||", "|"):
                break
            p = is_wt_path(a)
            if p:
                targets.append(p)
    if t == "rm":
        seg = []
        for a in tokens[i + 1:]:
            if a in (";", "&&", "||", "|"):
                break
            seg.append(a)
        flags = [a for a in seg if a.startswith("-")]
        if any("r" in f or "R" in f for f in flags if not f.startswith("--")) or "--recursive" in flags:
            for a in seg:
                if a.startswith("-"):
                    continue
                p = is_wt_path(a)
                if p:
                    targets.append(p)

if not targets:
    allow()

# Locate the main checkout from the target worktree's own git metadata.
def main_checkout(wt: Path) -> Path | None:
    try:
        out = subprocess.run(
            ["git", "worktree", "list", "--porcelain"], cwd=wt,
            check=True, capture_output=True, text=True, timeout=15,
        ).stdout
        first = out.splitlines()[0]
        if first.startswith("worktree "):
            return Path(first.split(" ", 1)[1])
    except Exception:
        return None
    return None

for wt in targets:
    main = main_checkout(wt)
    if main is None:
        # Not a resolvable repo worktree -> cannot verify -> fail closed.
        print(f"BLOCK|{wt}|could not resolve the main checkout to verify harvest state")
        raise SystemExit
    harvester = main / "bin" / "harvest_worktree_data.py"
    if not harvester.is_file():
        print(f"BLOCK|{wt}|harvester missing at {harvester}; cannot verify")
        raise SystemExit
    try:
        r = subprocess.run(
            ["python3", str(harvester), "--check", "--quiet", "--worktree", str(wt)],
            cwd=main, capture_output=True, text=True, timeout=90,
        )
    except Exception as e:
        print(f"BLOCK|{wt}|scoped harvest check errored: {e}")
        raise SystemExit
    if r.returncode != 0:
        detail = (r.stderr or r.stdout or "").strip().splitlines()
        tail = detail[-3:] if detail else ["(no detail)"]
        print(f"BLOCK|{wt}|unharvested gitignored experiment data (or check error): " + " / ".join(tail))
        raise SystemExit

allow()
PYEOF
)

case "$result" in
  ALLOW*) exit 0 ;;
  BLOCK*)
    wt=$(printf '%s' "$result" | cut -d'|' -f2)
    why=$(printf '%s' "$result" | cut -d'|' -f3-)
    cat >&2 <<EOF
BLOCKED: removing worktree with unharvested experiment run data.
  worktree: $wt
  reason:   $why

This worktree may hold the SOLE COPY of gitignored row-level run data
(runlogs with generation text, shard id maps, salts, staged pools).
Deleting it loses that data permanently -- this exact mistake destroyed
the wide-rescore row text on 2026-08-26.

Fix: from the MAIN checkout run
    python3 bin/harvest_worktree_data.py
(idempotent; copies every worktree's gitignored experiment data into the
main checkout), verify it reports 0 conflicts, then retry the removal.

Only if you INTEND to destroy unharvested data, acknowledge with:
    EHR_WT_DATA_OK=1 <original command>
EOF
    exit 2
    ;;
  *) exit 0 ;;
esac
