#!/usr/bin/env bash
# Cloud-lane cell wrapper: one Arm B CoT-injection cell (Amendment AB) inside
# an HF Job. Sibling of hf_jobs_cell.sh (same positional contract, same
# durable-log pattern); runs run_arm_b.py instead of the extract->score pair.
#
# Runs AFTER the launcher's bootstrap has cloned this repo at a pinned commit
# and cd'd into it. Uploads the small artifacts only: result JSON + durable
# per-incarnation logs to the results dataset repo under the run tag.
#
# Usage:
#   hf_jobs_arm_b.sh <model> <gate-rows-relpath> <results-repo> <run-tag> \
#       [extra run_arm_b.py args: --direction --signal --position \
#        --note-variant --eval-pool --n-* --seed --temperature --top-p ...]
#
# The gate-rows path is forwarded for gate-pool cells and harmlessly ignored
# by dial-pool cells (steering_common.build_eval_pool reads it only for the
# gate branch). Requires: HF_TOKEN in env (job secret) for uploads only.
set -euo pipefail

MODEL="$1"; GATE_ROWS="$2"; RESULTS_REPO="$3"; RUN_TAG="$4"; shift 4

PROBE="experiment/phase1/probe"
CLOUD="experiments/common/cloud"
OUT="/tmp/cell_${RUN_TAG}"
mkdir -p "${OUT}"

# Durable log capture (see hf_jobs_cell.sh: HF preemption restarts a job from
# scratch and wipes its log stream; two boot-id files under one run tag IS the
# restart evidence).
BOOT_ID="$(date -u +%Y%m%dT%H%M%SZ)"
JOB_LOG="${OUT}/job_log_${BOOT_ID}.txt"
exec > >(tee -a "${JOB_LOG}") 2>&1

(
    while sleep "${LOG_PUSH_INTERVAL:-600}"; do
        python "${CLOUD}/upload_result.py" \
            --repo "${RESULTS_REPO}" \
            --path-prefix "${RUN_TAG}/logs" \
            --file "${JOB_LOG}" >/dev/null 2>&1 || true
    done
) &
LOG_PUSHER_PID=$!
trap 'kill "${LOG_PUSHER_PID}" 2>/dev/null || true' EXIT

echo "[arm-b-cell] boot=${BOOT_ID} model=${MODEL} run_tag=${RUN_TAG}"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader || true

python "${PROBE}/steering/run_arm_b.py" \
    --model "${MODEL}" \
    --gate-rows "${GATE_ROWS}" \
    --datasets-root datasets \
    --device cuda \
    --out "${OUT}/result.json" \
    "$@"

test -f "${OUT}/result.json" || { echo "[arm-b-cell] FATAL: no result.json"; exit 1; }

python "${CLOUD}/upload_result.py" \
    --repo "${RESULTS_REPO}" \
    --path-prefix "${RUN_TAG}" \
    --file "${OUT}/result.json"
python "${CLOUD}/upload_result.py" \
    --repo "${RESULTS_REPO}" \
    --path-prefix "${RUN_TAG}/logs" \
    --file "${JOB_LOG}" || true

echo "[arm-b-cell] DONE run_tag=${RUN_TAG}"
