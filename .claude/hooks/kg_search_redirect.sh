#!/usr/bin/env bash
# PreToolUse guard (Grep|Glob): the native Grep/Glob tools bypass the Bash-only
# bin_search_guard, and they are the model's trained-in first reach. This hook
# closes that gap AND kills the round trip: instead of just saying "go run
# bin/search", it RUNS bin/search with terms extracted from the blocked pattern
# and returns the top KG hits inline in the block message. The model gets its
# candidate set in the same step it would have gotten raw grep output.
#
# FALSE-POSITIVE DISCIPLINE:
#   * Grep on an explicit FILE path is a targeted read, not exploration: ALLOW.
#   * Grep/Glob whose path is OUTSIDE the project dir (scratchpad, other
#     checkouts): the KG does not index it: ALLOW.
#   * Glob without a recursive `**` sweep (e.g. experiments/*/AMENDMENT.md) is
#     navigation, not search: ALLOW. Only `**` sweeps are blocked.
#   * Everything else is an exploratory sweep: BLOCK, with inline KG results.
#
# Escape hatch (when the KG genuinely does not index the target): use Bash with
# the existing conscious-bypass token, e.g. `EHR_SEARCH_OK=1 rg ...` (same
# token as bin_search_guard, one rule to remember).
set -u

payload=$(cat)
HOOK_PAYLOAD="$payload" python3 - <<'PYEOF'
import os, sys, json, re, subprocess

def allow():
    raise SystemExit(0)

try:
    d = json.loads(os.environ.get("HOOK_PAYLOAD", ""))
except Exception:
    allow()

tool = d.get("tool_name") or ""
ti = d.get("tool_input") or {}
proj = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
proj = os.path.realpath(proj)

pattern = ti.get("pattern") or ""
path = ti.get("path") or ""

if path:
    rp = os.path.realpath(path if os.path.isabs(path) else os.path.join(proj, path))
    if not (rp == proj or rp.startswith(proj + os.sep)):
        allow()                      # outside the project: KG does not index it
    if tool == "Grep" and os.path.isfile(rp):
        allow()                      # targeted read of a known file

if tool == "Glob" and "**" not in pattern:
    allow()                          # scoped navigation glob, not a sweep

# Extract KG query terms from the regex/glob pattern (best effort).
raw = re.sub(r"\\[a-zA-Z]", " ", pattern)          # \b \d \w ... -> space
toks = re.findall(r"[A-Za-z0-9_][A-Za-z0-9_\-\.]+", raw)
stop = {"py", "md", "yaml", "yml", "json", "txt", "sh", "csv"}
terms, seen = [], set()
for t in toks:
    t = t.strip("._-")
    if len(t) < 2 or t.isdigit() or t.lower() in stop or t.lower() in seen:
        continue
    seen.add(t.lower())
    terms.append(t)
terms = terms[:8]
query = " ".join(terms)

results = ""
if query:
    try:
        out = subprocess.run(
            [os.path.join(proj, "bin", "search"), *terms, "--limit", "8"],
            capture_output=True, text=True, timeout=25, cwd=proj,
        )
        results = (out.stdout or "").strip()[:6000]
    except Exception:
        results = ""

msg = [
    "BLOCKED (KG-first rule): raw %s sweep intercepted. The typed KG search is"
    " the required first move in this repo (AGENTS.md \"Search And Traversal\")."
    % tool,
]
if results:
    msg.append(
        "\nTo save you the round trip, bin/search ALREADY RAN with terms"
        " extracted from your pattern (query: %r). Results:\n\n%s" % (query, results)
    )
    msg.append(
        "\nNext moves:"
        "\n- Read the candidate files above, or Grep a SPECIFIC file from them"
        " (Grep with an explicit file path is allowed)."
        "\n- Wrong terms? Re-run yourself: bin/search <better terms> --limit 10"
    )
else:
    msg.append(
        "\nNo usable KG query could be extracted from your pattern. Run:"
        "\n  bin/search <query terms> --limit 10"
    )
msg.append(
    "\nIf the KG genuinely does not index this target (logs, node_modules, raw"
    " data dirs), bypass consciously via Bash: EHR_SEARCH_OK=1 rg ..."
)
sys.stderr.write("\n".join(msg) + "\n")
raise SystemExit(2)
PYEOF
exit $?
