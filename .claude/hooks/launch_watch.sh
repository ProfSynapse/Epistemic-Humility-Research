#!/usr/bin/env bash
# PostToolUse (Bash): AUTO-ARM a lead-owned completion watcher on every
# long-running job launch, and force-inject the arm-a-Monitor instruction
# into the model's context in the SAME turn.
#
# USER DIRECTIVE 2026-08-14: runner subagents have silently failed to report
# job completion at least six times, and the prose rule ("lead owns the
# completion watch") was violated across a compaction gap. The fix must be
# mechanical, not memorial: launching a job auto-creates the watcher.
#
# What this does on detecting a launch command:
#   1. For docker launches with --name: spawns a detached `docker wait` that
#      writes scratch/launch-watch/<container>.done (exit code + UTC time)
#      the moment the container exits. Survives this hook process ending.
#   2. Exits 2 so stderr is fed back to the model in the launch turn:
#      the LEAD must arm a Monitor on the .done file NOW; a subagent must
#      report the sentinel path to the lead in its report.
# Exit 2 on PostToolUse does not undo the tool call (the launch already ran);
# it only injects the instruction. Read-only docker ops are ignored.
set -u

payload=$(cat)
cmd=$(HOOK_PAYLOAD="$payload" python3 - <<'PYEOF'
import os, json
try:
    d = json.loads(os.environ.get("HOOK_PAYLOAD", ""))
except Exception:
    print(""); raise SystemExit
ti = d.get("tool_input") or {}
print(ti.get("command") or "")
PYEOF
)

[ -z "$cmd" ] && exit 0

# Detect a launch verb. Keep tight: read-only ops (ps, logs, inspect, wait,
# exec into a running container for a peek) must not trigger.
is_launch=""
case "$cmd" in
  *"docker ps"*|*"docker logs"*|*"docker inspect"*|*"docker wait"*|*"docker rm"*|*"docker stop"*|*"docker images"*) : ;;
  *"docker run"*|*"docker start "*) is_launch=docker ;;
esac
case "$cmd" in
  *"modal run"*|*"modal deploy"*|*"hf jobs run"*|*"huggingface-cli jobs run"*|*"sbatch "*) is_launch=cloud ;;
esac
# Local GPU runner launches (2026-08-25 gap: a builder's bare python realness-flag
# background launch matched no pattern, so neither the builder nor the lead got the
# watch instruction and a crashed run sat undetected until the user asked for progress).
# This repo's harness convention gates every real GPU run behind an explicit realness
# flag; detect those, plus nohup'd python as a generic long-run signature.
case "$cmd" in
  *"confirm-gpu-go"*|*"i-know-this-is-the-real"*) is_launch=local ;;
  *"nohup "*python*) is_launch=local ;;
esac

[ -z "$is_launch" ] && exit 0

watch_dir="${CLAUDE_PROJECT_DIR:-.}/scratch/launch-watch"
mkdir -p "$watch_dir" 2>/dev/null || true

sentinel=""
if [ "$is_launch" = "docker" ]; then
  # Extract the container name from --name <name> or --name=<name>.
  name=$(printf '%s' "$cmd" | /usr/bin/grep -oE -- '--name[= ][A-Za-z0-9._-]+' | head -1 | sed -E 's/--name[= ]//')
  if [ -n "$name" ]; then
    sentinel="$watch_dir/$name.done"
    rm -f "$sentinel" 2>/dev/null || true
    nohup bash -c "
      # Give the container a moment to register before waiting on it.
      for i in \$(seq 1 30); do
        docker inspect '$name' >/dev/null 2>&1 && break
        sleep 2
      done
      code=\$(docker wait '$name' 2>&1)
      printf 'container=%s exit=%s finished_utc=%s\n' '$name' \"\$code\" \"\$(date -u +%FT%TZ)\" > '$sentinel'
    " >/dev/null 2>&1 &
    disown 2>/dev/null || true
  fi
fi

{
  echo "LAUNCH DETECTED (launch_watch hook). This is automation, not a block: the job is running."
  if [ -n "$sentinel" ]; then
    echo "A detached docker-wait watcher was AUTO-ARMED. Completion sentinel (appears when the container exits, with its exit code):"
    echo "  $sentinel"
  else
    echo "No --name found (or cloud/local launch): no docker-wait could be auto-armed. Sentinel dir: $watch_dir"
    echo "For a LOCAL runner launch: the watch condition is the run's own log/summary artifact (log gone silent >10min = dead; summary file written = done)"
  fi
  echo "REQUIRED NOW, in this same turn:"
  echo "  - If you are the LEAD session: arm a Monitor on the sentinel path (or on the job's completion condition) so completion re-invokes you. Do not rely on any runner's report."
  echo "  - If you are a SUBAGENT: you cannot arm the lead's watcher. Include the sentinel path prominently in your report so the lead arms its own Monitor."
} >&2
exit 2
