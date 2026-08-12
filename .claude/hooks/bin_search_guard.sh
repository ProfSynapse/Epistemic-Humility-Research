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
import os, json, shlex, re

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

# Isolate the first SEARCH-BEARING command segment.
#
# Two different things can precede the real command, and they are not the same:
#   * A PIPE (`cat x | grep y`) makes the search a FILTER over another command's
#     output, not an exploration. Still allowed -- so we never look past a `|`.
#   * A `cd` (`cd /repo && rg foo`) is pure harness noise: this session's shell
#     resets cwd between calls, so nearly every Bash call opens with a `cd`.
#     Treating `cd` as "the leading command" turned this guard off for the
#     dominant command shape -- `rg foo` was blocked while `cd X && rg foo`
#     sailed through. So we SKIP leading `cd` segments and judge what follows.
segments = re.split(r"&&|\|\||;|\n", cmd)
seg = ""
for s in segments:
    s = s.strip()
    if not s:
        continue
    try:
        probe = shlex.split(s)
    except Exception:
        probe = s.split()
    if probe and probe[0] == "cd":
        continue          # harness noise, keep looking
    seg = s
    break

# Never look past a pipe: beyond it, a search is a filter.
i = seg.find("|")
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

def to_query(s):
    # Best-effort: turn a regex/pattern into KG search terms.
    raw = re.sub(r"\\[a-zA-Z]", " ", s or "")
    stop = {"py", "md", "yaml", "yml", "json", "txt", "sh", "csv"}
    terms, seen = [], set()
    for t in re.findall(r"[A-Za-z0-9_][A-Za-z0-9_\-\.]+", raw):
        t = t.strip("._-")
        if len(t) < 2 or t.isdigit() or t.lower() in stop or t.lower() in seen:
            continue
        seen.add(t.lower())
        terms.append(t)
    return " ".join(terms[:8])

def first_pattern(args):
    for a in args:
        if not a.startswith("-"):
            return a
    return ""

if prog == "rg":
    print("BLOCK|" + to_query(first_pattern(args))); raise SystemExit

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
        print("BLOCK|" + to_query(first_pattern(args))); raise SystemExit
    print("ALLOW"); raise SystemExit

if prog == "find":
    for i, a in enumerate(args):
        if is_flag(a, "-name", "-iname", "-path", "-ipath", "-regex", "-iregex"):
            val = args[i + 1] if i + 1 < len(args) else ""
            print("BLOCK|" + to_query(val)); raise SystemExit
    print("ALLOW"); raise SystemExit

print("ALLOW")
PYEOF
)

case "$verdict" in
  ALLOW*) exit 0 ;;
esac

# No round trip: run the KG search HERE with terms guessed from the blocked
# pattern, and hand the candidate set back inline in the block message.
query="${verdict#BLOCK|}"
results=""
if [ -n "$query" ]; then
  proj="${CLAUDE_PROJECT_DIR:-$PWD}"
  results=$( cd "$proj" 2>/dev/null && ./bin/search $query --limit 8 2>/dev/null | head -c 6000 )
fi

echo "BLOCKED: raw exploratory code search is not the first move in this repo. The typed knowledge-graph search (bin/search) is the required entry point (AGENTS.md \"Search And Traversal\")." >&2
if [ -n "$results" ]; then
  echo "
To save you the round trip, bin/search ALREADY RAN with terms guessed from your pattern (query: '$query'). Results:

$results

Next moves:
- Read the candidate files above, or run a SCOPED grep over just those files (targeted grep on a known file is allowed).
- Wrong terms? Re-run yourself: bin/search <better terms> --limit 10" >&2
else
  echo "
No usable query terms could be guessed from your command. Run:
  bin/search <query terms> --limit 10" >&2
fi
echo "
If the KG genuinely does not index this target (logs, node_modules, a raw data dir), proceed consciously by prefixing the command with the bypass token:
  EHR_SEARCH_OK=1 <your command>" >&2
exit 2
