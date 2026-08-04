#!/usr/bin/env bash
# PreToolUse guard (Bash): `main` is protected in the Epistemic-Humility-Research
# repo. Experiment/feature work goes on a branch in its own worktree and merges
# via PR. Block a `git commit` / `git push` when the target branch is `main`.
#
# STANDING RULE (pr-workflow skill): branches + worktrees + PR merge. Repeated
# failure mode: the lead (esp. after compaction, when the current-branch context
# is gone) runs `git commit` while parked on main in the canonical checkout.
#
# NOT AN ABSOLUTE WALL. The experiment-wrapup workflow legitimately commits
# LIVING TRACKING DOCS (registries, family-layer-map, scoreboard) directly to
# main. So this is a speed-bump: it stops the agent and forces a conscious
# "is this a sanctioned direct-to-main commit, or should it be on a branch?"
# To proceed, prefix the command with the acknowledgement token:
#     EHR_MAIN_OK=1 git commit -m '...'
#
# FALSE-POSITIVE DISCIPLINE: fires ONLY when (a) the leading git subcommand is
# commit/push, AND (b) the branch at the command's real target dir is exactly
# `main`, AND (c) that repo is Epistemic-Humility-Research (so unrelated repos'
# main is untouched). It resolves the target dir from a leading `cd <path>` or a
# `git -C <path>` in the command, else the payload cwd (AGENTS.md convention is
# to `cd` to the canonical checkout explicitly). Exit 2 -> blocked.
set -u

payload=$(cat)
verdict=$(HOOK_PAYLOAD="$payload" python3 - <<'PYEOF'
import os, json, shlex, subprocess

try:
    d = json.loads(os.environ.get("HOOK_PAYLOAD", ""))
except Exception:
    print("ALLOW"); raise SystemExit
ti = d.get("tool_input") or {}
cmd = (ti.get("command") or "")
cwd = d.get("cwd") or os.getcwd()
if not cmd.strip():
    print("ALLOW"); raise SystemExit

if "EHR_MAIN_OK=" in cmd:
    print("ALLOW"); raise SystemExit

# Tokenize each top-level segment; find a `git commit`/`git push` invocation and
# any `git -C <dir>`. Also capture a leading `cd <dir>` used as the branch ctx.
import re
segments = re.split(r'&&|\|\||;|\n|\|', cmd)

def toks_of(s):
    try:
        return shlex.split(s)
    except Exception:
        return s.split()

target_dir = cwd
is_commit_or_push = False
git_c_dir = None
saw_cd = None

for seg in segments:
    t = toks_of(seg)
    if not t:
        continue
    # leading env assignments / wrappers
    j = 0
    while j < len(t) and ("=" in t[j] and not t[j].startswith("-")
                          and "/" not in t[j].split("=", 1)[0]):
        j += 1
    while j < len(t) and t[j] in ("command", "time", "nice", "nohup", "sudo", "env"):
        j += 1
    t = t[j:]
    if not t:
        continue
    if t[0] == "cd" and len(t) > 1 and saw_cd is None:
        saw_cd = t[1]
    if t[0] == "git":
        rest = t[1:]
        k = 0
        while k < len(rest):
            if rest[k] == "-C" and k + 1 < len(rest):
                git_c_dir = rest[k + 1]
                k += 2
                continue
            if rest[k].startswith("-"):
                k += 1
                continue
            break
        sub = rest[k] if k < len(rest) else ""
        if sub in ("commit", "push"):
            is_commit_or_push = True

if not is_commit_or_push:
    print("ALLOW"); raise SystemExit

# Resolve the branch-context dir: git -C wins, else a leading cd, else cwd.
if git_c_dir:
    target_dir = git_c_dir
elif saw_cd:
    target_dir = saw_cd
target_dir = os.path.expanduser(target_dir)
if not os.path.isabs(target_dir):
    target_dir = os.path.normpath(os.path.join(cwd, target_dir))

def git(*a):
    try:
        return subprocess.run(["git", "-C", target_dir, *a],
                              capture_output=True, text=True, timeout=5).stdout.strip()
    except Exception:
        return ""

top = git("rev-parse", "--show-toplevel")
if not top:
    print("ALLOW"); raise SystemExit  # not a git repo we can read -> fail open
branch = git("rev-parse", "--abbrev-ref", "HEAD")
# Confirm this is the EHR repo (so other repos' main is untouched). Match the
# git COMMON dir against the real EHR root: the canonical checkout and every
# worktree of it share the common dir /home/profsynapse/code/Epistemic-Humility-
# Research/.git . This is exact — no substring false positives from an unrelated
# repo that merely sits under a path containing the project name.
EHR_ROOT = "/home/profsynapse/code/Epistemic-Humility-Research"
common = git("rev-parse", "--git-common-dir")
common_abs = os.path.abspath(os.path.join(target_dir, common)) if common else ""
is_ehr = common_abs == EHR_ROOT or common_abs.startswith(EHR_ROOT + os.sep)

if branch == "main" and is_ehr:
    print("BLOCK"); raise SystemExit
print("ALLOW")
PYEOF
)

case "$verdict" in
  BLOCK*)
    echo "BLOCKED: this is a git commit/push while on the PROTECTED 'main' branch of Epistemic-Humility-Research. Experiment/feature work goes on a BRANCH in its own worktree and merges via PR (pr-workflow skill):
  git worktree add /home/profsynapse/code/ehr-worktrees/<name> -b <type>/<slug> main
  # ...do the work in that worktree, commit there, then open a PR
If this is a SANCTIONED direct-to-main commit of a LIVING TRACKING DOC (registry / family-layer-map / prediction-scoreboard, per the experiment-wrapup workflow), proceed consciously by prefixing the command with the token:
  EHR_MAIN_OK=1 <your git command>" >&2
    exit 2 ;;
esac
exit 0
