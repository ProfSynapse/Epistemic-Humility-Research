#!/usr/bin/env bash
# PreToolUse guard (Bash): the KG search (`bin/search`) is the required FIRST
# move for exploring this repo. Block a raw exploratory code search (ripgrep, a
# recursive/globbed grep, or a find-by-name) when it is the leading command, and
# point back to `bin/search` first.
#
# STANDING RULE (AGENTS.md "Search And Traversal"): "Before reaching for rg,
# grep, or an Explore/general-purpose search subagent, run the local KG search
# first." Repeated failure mode: the lead (esp. after compaction) opens with a
# raw rg/grep sweep and never runs bin/search.
#
# FALSE-POSITIVE DISCIPLINE (this hook fires on EVERY Bash call, so it must not
# cry wolf). It blocks ONLY the exploratory-search shape and ONLY as the leading
# command:
#   * `rg ...`                      (ripgrep is, by construction, a code search)
#   * `grep`/`egrep`/`fgrep` with a recursive flag (-r/-R/--recursive/--include*)
#     or a directory argument      (an exploratory sweep, not a targeted read)
#   * `find <path> ... -name/-iname/-path/-ipath/-regex/-iregex ...`  (locating)
#   * the same three behind an `rtk` proxy prefix (`rtk grep ...`, `rtk rg ...`)
# It does NOT block: a piped filter (`cmd | grep ...` — grep is not the leading
# token), a targeted `grep PATTERN file` on a known file, `git grep` (git-native),
# `bin/search`, or a `find` used for anything other than locating by name/path
# (-delete, -exec, bare -type listings, etc.).
#
# Conscious bypass (the intended path when bin/search genuinely does not cover
# the target — e.g. sweeping logs, node_modules, or a non-indexed data dir):
# prefix the command with the acknowledgement token, e.g.
#     EHR_SEARCH_OK=1 grep -rn TODO node_modules/
# The token is a speed-bump, not a wall: it forces a conscious "the KG doesn't
# index this" decision. Exit 2 -> tool call blocked, stderr shown to the model.
set -u

payload=$(cat)
verdict=$(HOOK_PAYLOAD="$payload" python3 - <<'PYEOF'
import os, json, shlex

try:
    d = json.loads(os.environ.get("HOOK_PAYLOAD", ""))
except Exception:
    print("ALLOW"); raise SystemExit
cmd = ((d.get("tool_input") or {}).get("command") or "")
if not cmd.strip():
    print("ALLOW"); raise SystemExit

# Conscious bypass anywhere in the command line.
if "EHR_SEARCH_OK=" in cmd:
    print("ALLOW"); raise SystemExit

# Isolate the FIRST top-level command segment. A search that is fed by a pipe
# (`... | grep`) is a filter, not an exploration, so only the leading segment
# matters. Split on the first top-level |, &&, ||, ;, or newline.
seg = cmd
for sep in ("\n", "&&", "||", "|", ";"):
    i = seg.find(sep)
    if i != -1:
        seg = seg[:i]
seg = seg.strip()

try:
    toks = shlex.split(seg)
except Exception:
    toks = seg.split()
# Drop leading VAR=val env assignments and a couple of transparent wrappers.
while toks and ("=" in toks[0] and not toks[0].startswith("-")
                and "/" not in toks[0].split("=", 1)[0]):
    toks.pop(0)
while toks and toks[0] in ("command", "time", "nice", "nohup", "sudo", "env"):
    toks.pop(0)
if not toks:
    print("ALLOW"); raise SystemExit

# Peel an `rtk` proxy prefix so `rtk grep ...` is judged as `grep ...`.
if toks[0] == "rtk" and len(toks) > 1:
    toks = toks[1:]

prog = os.path.basename(toks[0])
args = toks[1:]

def is_flag(a, *names):
    return a in names

if prog == "rg":
    print("BLOCK rg"); raise SystemExit

if prog in ("grep", "egrep", "fgrep"):
    recursive = any(
        a in ("-r", "-R", "--recursive", "--dereference-recursive")
        or a.startswith("--include") or a.startswith("--exclude")
        or (a.startswith("-") and not a.startswith("--")
            and ("r" in a[1:] or "R" in a[1:]))
        for a in args)
    # A directory argument (non-flag path that is a dir) also signals a sweep.
    dir_arg = False
    for a in args:
        if a.startswith("-"):
            continue
        if os.path.isdir(a):
            dir_arg = True
            break
    if recursive or dir_arg:
        print("BLOCK grep"); raise SystemExit
    print("ALLOW"); raise SystemExit

if prog == "find":
    if any(is_flag(a, "-name", "-iname", "-path", "-ipath", "-regex", "-iregex")
           for a in args):
        print("BLOCK find"); raise SystemExit
    print("ALLOW"); raise SystemExit

print("ALLOW")
PYEOF
)

case "$verdict" in
  ALLOW*) exit 0 ;;
esac

echo "BLOCKED: raw exploratory code search is not the first move in this repo. Run the typed knowledge-graph search FIRST, then fall back to scoped text search only over its candidate set:
  bin/search <query terms> --limit 10
AGENTS.md (\"Search And Traversal\"): the KG is the default entry point for ALL exploration — locating papers, concepts, claims, mechanisms, experiment artifacts, or code. Do not open with a broad rg/grep/find sweep or a fan-out search agent.
If the KG genuinely does not index this target (logs, node_modules, a raw data dir), proceed consciously by prefixing the command with the bypass token:
  EHR_SEARCH_OK=1 <your command>" >&2
exit 2
