#!/usr/bin/env bash
# Diagnostics bundle cell 1 (TODO item 11, GPU half) — batched steering engine
# equivalence cell on the real checkpoint. Lab-notebook diagnostic (tier L):
# no amendment, no gates. Un-gates AK Stage 2 + backlog items 3/5 by proving the
# CPU-tested batched final-position + per-element-alpha edit matches a
# one-prompt-at-a-time reference on the real model's layer geometry and padding.
#
# WHAT
#   Runs experiment/phase1/probe/steering/gpu_equivalence_cell.py on a handful of
#   fixed prompts at the direction's best_layer, comparing batched vs unbatched
#   steered hidden states at each row's last real token. Expected result: the
#   model's own batched-vs-unbatched numeric floor (<< the steering magnitude).
#
# BATCH POLICY: this cell IS the batch-vs-loop parity check — it deliberately
# runs both a batched pass and a batch-1 loop and diffs them. That is the point;
# nothing to relax.
#
# INPUTS
#   The direction JSON is COMMITTED in-repo
#   (steering/directions/<tag>/direction_gate.json), so no pool fetch is needed.
#   Only the checkpoint is pulled from HF. The gpu cell requires the explicit
#   --i-know-this-runs-on-gpu acknowledgement flag (loud DO-NOT-RUN guard);
#   this wrapper passes it because the launch is the user's explicit approval.
#
# Runs AFTER runpod_run_job.py cloned the repo at a pinned commit and cd'd in.
# Requires HF_TOKEN in the pod env for the private base/adapter download and the
# staging upload.
#
# Usage:
#   runpod_diag_gpu_equiv.sh <staging_repo> <base_model> <direction_relpath> \
#       [adapter_repo] [adapter_revision] [run_tag]
#   base_model : HF repo id or local path of the checkpoint to load. The gpu
#       cell loads a single --model with NO adapter, so to test a LoRA lineage
#       pass a MERGED checkpoint here (see docs/preparation/diagnostics-bundle-launch-plan.md).
#   direction_relpath : repo-relative path to a direction_*.json with best_layer,
#       e.g. experiment/phase1/probe/steering/directions/qwen3.5-4b/direction_gate.json
set -euo pipefail

STAGING_REPO="$1"; BASE_MODEL="$2"; DIRECTION_RELPATH="$3"
RUN_TAG="${4:-diag-item11-gpuequiv-r1}"

PROBE="experiment/phase1/probe"
OUT="/tmp/${RUN_TAG}"
mkdir -p "${OUT}"

BOOT_ID="$(date -u +%Y%m%dT%H%M%SZ)"
JOB_LOG="${OUT}/job_log_${BOOT_ID}.txt"
exec > >(tee -a "${JOB_LOG}") 2>&1

(
    while sleep "${LOG_PUSH_INTERVAL:-120}"; do
        python "${PROBE}/cloud/upload_result.py" \
            --repo "${STAGING_REPO}" \
            --path-prefix "${RUN_TAG}/logs" \
            --file "${JOB_LOG}" >/dev/null 2>&1 || true
    done
) &
LOG_PUSHER_PID=$!
trap 'kill "${LOG_PUSHER_PID}" 2>/dev/null || true' EXIT

# shellcheck source=experiment/phase1/probe/cloud/job_failure_trap.sh
source "${PROBE}/cloud/job_failure_trap.sh"
FAIL_STAGING_REPO="${STAGING_REPO}"
FAIL_RUN_TAG="${RUN_TAG}"
FAIL_JOB_LOG="${JOB_LOG}"
FAIL_UPLOADER="${PROBE}/cloud/upload_result.py"
install_failure_trap

echo "[diag-item11] boot=${BOOT_ID} run_tag=${RUN_TAG}"
echo "[diag-item11] base=${BASE_MODEL} direction=${DIRECTION_RELPATH}"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader || true

RESULT="${OUT}/gpu_equiv_result.txt"
# The cell prints its parity report to stdout; capture it to a result file so the
# tiny artifact can be uploaded (the cell does not write a JSON of its own).
python "${PROBE}/steering/gpu_equivalence_cell.py" \
    --model "${BASE_MODEL}" \
    --direction "${DIRECTION_RELPATH}" \
    --device cuda --dtype bfloat16 \
    --i-know-this-runs-on-gpu | tee "${RESULT}"

test -s "${RESULT}" || { echo "[diag-item11] FATAL: empty result"; exit 1; }
grep -q "OVERALL max abs divergence" "${RESULT}" || {
    echo "[diag-item11] FATAL: cell did not report a divergence line"; exit 1; }

python "${PROBE}/cloud/upload_result.py" \
    --repo "${STAGING_REPO}" --path-prefix "${RUN_TAG}/result" --file "${RESULT}"
python "${PROBE}/cloud/upload_result.py" \
    --repo "${STAGING_REPO}" --path-prefix "${RUN_TAG}/logs" --file "${JOB_LOG}" || true
echo "[diag-item11] DONE"
