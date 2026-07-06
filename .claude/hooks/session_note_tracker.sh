#!/usr/bin/env bash
# Session-note cadence nudge (project-local).
# USER DIRECTIVE 2026-07-06: nudge to write/update a session note every N
# conversation turns, because the lead had drifted for many turns without one.
#
# Two modes (arg $1):
#   prompt : UserPromptSubmit. Increment a per-session turn counter; when it
#            reaches N, print a reminder (stdout is added to the model's context)
#            and reset, so the nudge repeats every N turns until a note is written.
#   wrote  : PostToolUse (Write|Edit|MultiEdit). If the written file is under
#            docs/sessions/, reset the counter (a note was just written/updated).
#
# Counter state is ephemeral per session in TMPDIR (not committed; no git noise).
set -u
N=15
mode="${1:-prompt}"

payload=$(cat)
sid=$(HOOK_PAYLOAD="$payload" python3 - <<'PYEOF'
import os, json
try:
    d = json.loads(os.environ.get("HOOK_PAYLOAD", ""))
except Exception:
    print(""); raise SystemExit
print(d.get("session_id") or "nosession")
PYEOF
)

state_dir="${TMPDIR:-/tmp}/ehr_snote"
mkdir -p "$state_dir" 2>/dev/null || true
counter="$state_dir/$sid"

if [ "$mode" = "wrote" ]; then
  wpath=$(HOOK_PAYLOAD="$payload" python3 - <<'PYEOF'
import os, json
try:
    d = json.loads(os.environ.get("HOOK_PAYLOAD", ""))
except Exception:
    print(""); raise SystemExit
ti = d.get("tool_input") or {}
print(ti.get("file_path") or ti.get("path") or "")
PYEOF
)
  case "$wpath" in
    */docs/sessions/*) printf '0' > "$counter" ;;
  esac
  exit 0
fi

# mode=prompt: increment and maybe nudge.
n=0
[ -f "$counter" ] && n=$(cat "$counter" 2>/dev/null || echo 0)
case "$n" in ''|*[!0-9]*) n=0 ;; esac
n=$((n + 1))
if [ "$n" -ge "$N" ]; then
  printf '0' > "$counter"
  echo "[session-note reminder] It has been $N turns since the last session-note write. Capture the current arc in a session note so it stays KG-findable and in-repo: append a checkpoint with .agents/skills/experiment-runner/scripts/research_session.py checkpoint --session docs/sessions/<NNNN...> --summary '...' (or 'init' for a new one). Record decisions, verdicts, and next steps; this replaces agent memory, which is disabled in this repo."
else
  printf '%s' "$n" > "$counter"
fi
exit 0
