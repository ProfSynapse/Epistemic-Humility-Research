#!/usr/bin/env bash
# Cloud-lane cell wrapper: one cross-model readout cell inside an HF Job.
#
# Runs AFTER the launcher's bootstrap has cloned this repo at a pinned commit
# and cd'd into it. Executes the same extract -> score pair as the local
# dgpu lane (Amendments X/Z/SR), then uploads ONLY the small artifacts —
# result.json + manifest.json + rows.jsonl (~1.4 MB: per-question answers,
# grades, provenance SHAs; required for per-cell text-baseline controls and
# grading audits — the Y fleet discarded these and lost that analysis) — to a
# results dataset repo. The multi-hundred-MB hidden-state tensors stay on the
# ephemeral job disk (matches the untracked-outputs convention).
#
# Usage:
#   hf_jobs_cell.sh <base-model> <gate-rows-relpath> <results-repo> <run-tag> \
#       [extra amendment_x_cross_model_extract.py args...]
#
# Requires: HF_TOKEN in env (job secret) for the upload step only; the repo,
# pool files, and (ungated) models need no auth.
set -euo pipefail

MODEL="$1"; GATE_ROWS="$2"; RESULTS_REPO="$3"; RUN_TAG="$4"; shift 4

PROBE="experiment/phase1/probe"
CLOUD="experiments/common/cloud"
OUT="/tmp/cell_${RUN_TAG}"
mkdir -p "${OUT}"

# Durable log capture (post-mortem 2026-07-02: HF preemption restarts a job
# from scratch and WIPES its log stream, leaving no forensics). Tee everything
# to a per-incarnation file and push it to the results repo every 10 min. A
# restarted job gets a fresh BOOT_ID, so the preempted incarnation's last
# pushed log survives at <run-tag>/logs/job_log_<boot>.txt — two log files
# under one run tag IS the restart evidence, and the tail shows where it died.
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

echo "[cloud-cell] boot=${BOOT_ID} model=${MODEL} gate_rows=${GATE_ROWS} run_tag=${RUN_TAG}"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader || true

python "${PROBE}/amendment_x_cross_model_extract.py" \
    --base-model "${MODEL}" \
    --gate-rows "${GATE_ROWS}" \
    --out-dir "${OUT}" \
    "$@"

test -f "${OUT}/manifest.json" || { echo "[cloud-cell] FATAL: no manifest.json"; exit 1; }

python "${PROBE}/amendment_x_cross_model_score.py" \
    --x-dir "${OUT}" \
    --out "${OUT}/result.json"

test -f "${OUT}/result.json" || { echo "[cloud-cell] FATAL: no result.json"; exit 1; }

UPLOAD_FILES=(--file "${OUT}/result.json" --file "${OUT}/manifest.json")
if [ -f "${OUT}/rows.jsonl" ]; then
    UPLOAD_FILES+=(--file "${OUT}/rows.jsonl")
else
    echo "[cloud-cell] WARN: no rows.jsonl to upload (extractor variant without a row layer?)"
fi

python "${CLOUD}/upload_result.py" \
    --repo "${RESULTS_REPO}" \
    --path-prefix "${RUN_TAG}" \
    "${UPLOAD_FILES[@]}"

echo "[cloud-cell] DONE ${RUN_TAG}"

# Final log push so the completed incarnation's full log is durable too.
python "${CLOUD}/upload_result.py" \
    --repo "${RESULTS_REPO}" \
    --path-prefix "${RUN_TAG}/logs" \
    --file "${JOB_LOG}" || true
