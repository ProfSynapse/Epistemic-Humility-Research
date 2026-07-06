#!/usr/bin/env bash
# PreToolUse guard (Bash): before any cloud/GPU LAUNCH, force the operator to
# have updated the governing signed doc first.
#
# USER DIRECTIVE 2026-07-06: a Modal run (AK Stage 2) was launched with the
# user's approval, but the amendment doc was left saying "NOT LAUNCHED". The
# doc drifted from reality. This hook makes that failure mode loud: a launch
# command is blocked until the operator acknowledges that the target
# experiment's signed doc / experiment.yaml has been updated to reflect the
# launch and the recorded approval.
#
# Scope: only actual LAUNCH verbs (modal run|deploy, hf jobs run, sbatch).
# Read-only Modal ops (app list|logs|stop, volume ...) are NOT blocked.
#
# Bypass (the intended, conscious path): once the doc is updated, re-run the
# launch prefixed with an acknowledgement token, e.g.
#     EHR_LAUNCH_OK=<amendment-or-slug> modal run ...
# The token is a speed-bump, not a security control: it exists to force the
# operator to stop, update the signed doc + record the approval, and only then
# consciously proceed. Exit 2 -> tool call blocked, stderr shown to the model.
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

# Already acknowledged for this invocation -> allow.
case "$cmd" in
  *EHR_LAUNCH_OK=*) exit 0 ;;
esac

# Detect a launch verb. Keep this tight so read-only ops are not caught.
is_launch=""
case "$cmd" in
  *"modal run"*|*"modal deploy"*|*"modal app run"*) is_launch=1 ;;
  *"hf jobs run"*|*"huggingface-cli jobs run"*)       is_launch=1 ;;
  *"sbatch "*)                                         is_launch=1 ;;
esac

[ -z "$is_launch" ] && exit 0

echo "BLOCKED: this looks like a cloud/GPU LAUNCH, and launches must not run before the governing signed doc reflects them.
Standing user directive (2026-07-06): a launch drifted from its amendment doc once (AK Stage 2 ran while its doc still said NOT LAUNCHED). Before launching:
  1. Confirm the target experiment is SIGNED and the GPU spend has explicit user approval in THIS conversation (a teammate relay does not count).
  2. Update the governing doc FIRST: the amendment doc status line (experiment/protocol/AMENDMENT-*.md) or the experiment.yaml manifest (experiments/<slug>/) to LAUNCHED, recording the approval and the run identifier.
  3. Then re-run this exact command prefixed with the acknowledgement token naming the experiment, e.g.:
       EHR_LAUNCH_OK=<amendment-letter-or-slug> <your launch command>
This is a deliberate speed-bump so the signed record never lags reality again." >&2
exit 2
