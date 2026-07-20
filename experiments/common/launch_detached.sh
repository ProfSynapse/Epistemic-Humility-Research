#!/usr/bin/env bash
# Launch a command fully detached from the invoking shell/session, with a
# recoverable PID and exit code.
#
# Why this exists: a signed CPU/GPU analysis run launched as a harness-tracked
# background Bash task is torn down when the session that launched it ends,
# even though nothing about the underlying process required that. A bare
# `setsid nohup cmd &` avoids the teardown but loses the exit code, because
# nothing survives to observe $? once the process is fully detached and the
# launching shell exits. This script fixes both: it launches via
# `setsid` + `nohup` so the child is immune to the launching session's
# HUP/exit, and it wraps the command in a subshell that captures and echoes
# its own $? to a sidecar file, so the exit code is recoverable after the
# fact instead of lost the moment the process detaches.
#
# Usage:
#   experiments/common/launch_detached.sh <log_path> <command> [args...]
#
# Effects:
#   - <log_path>            stdout+stderr of <command>, appended.
#   - <log_path>.pid        the PID of the detached subshell wrapper
#                            (the actual child of this script, not this
#                            script's own PID). This is the PID to check for
#                            liveness (`kill -0`) and to SIGKILL for a
#                            kill-resume drill.
#   - <log_path>.exit_code  written once <command> exits, containing its exit
#                            code. Absent while the command is still running
#                            or has not started; any stale copy from a prior
#                            launch at the same log path is removed up front
#                            so its absence is a reliable "not done yet"
#                            signal.
#
# The PID recorded is the wrapper subshell's PID, not necessarily the PID of
# any further children <command> itself forks. Because the wrapper runs
# under `setsid`, it is its own process group leader, so SIGKILL to the whole
# group (note the leading '-') reliably reaches <command> and any children it
# spawned in that group, not just the wrapper:
#
#   PID=$(experiments/common/launch_detached.sh /tmp/run.log python3 harness.py --n 100)
#   kill -0 "$PID"                 # still running?
#   kill -9 -"$PID"                # hard-kill the whole detached process group
#   wait "$PID" 2>/dev/null         # only works if PID is still this shell's child; after
#                                    # detach, poll /tmp/run.log.exit_code instead:
#   cat /tmp/run.log.exit_code      # recover the exit code once it appears
#
# Kill-resume smoke drill example (see the mechinterp-cells
# reference/organization.md "Kill-resume smoke drill" section):
#
#   LOG=experiments/<slug>/analysis/smoke/harness.log
#   PID=$(experiments/common/launch_detached.sh "$LOG" python3 experiments/<slug>/harness.py --smoke)
#   # ... wait for at least one checkpointed item, then:
#   kill -9 -"$PID"
#   # ... relaunch the identical command and confirm it resumes from the
#   # checkpoint rather than restarting from item zero.
#   PID2=$(experiments/common/launch_detached.sh "$LOG" python3 experiments/<slug>/harness.py --smoke)

set -eu

if [ "$#" -lt 2 ]; then
    echo "usage: $(basename "$0") <log_path> <command> [args...]" >&2
    exit 2
fi

LOG_PATH="$1"
shift

LOG_DIR="$(dirname "$LOG_PATH")"
mkdir -p "$LOG_DIR"

PID_FILE="${LOG_PATH}.pid"
EXIT_FILE="${LOG_PATH}.exit_code"

# Clear stale sidecars from a prior launch at this same log path so their
# absence/presence is a trustworthy signal for this launch.
rm -f "$PID_FILE" "$EXIT_FILE"

# The subshell is the piece that makes the exit code recoverable: it runs the
# real command, captures its $? immediately, and persists that value before
# the process tree fully exits and there is nothing left to observe it. The
# exit-file path is passed as a positional argument rather than interpolated
# into the script text, so it never needs its own quoting inside the
# single-quoted -c string. stdout/stderr redirection happens once, on the
# outer command, and the inner "$@" inherits those already-redirected
# descriptors.
setsid nohup bash -c '
    exit_file="$1"; shift
    "$@"
    echo "$?" > "$exit_file"
' _ "$EXIT_FILE" "$@" </dev/null >>"$LOG_PATH" 2>&1 &

CHILD_PID=$!
echo "$CHILD_PID" > "$PID_FILE"
disown "$CHILD_PID" 2>/dev/null || true

echo "$CHILD_PID"
