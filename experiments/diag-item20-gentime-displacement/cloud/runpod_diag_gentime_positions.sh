#!/usr/bin/env bash
# Diagnostics bundle cell 3 (TODO item 20 / AK Stage 1 read) — generation-time
# position-sweep extraction. Lab-notebook diagnostic (tier L): no gates.
#
# WHAT
#   Runs amendment_ak_gentime_positions_extract.py: greedy generation per row,
#   then a faithful re-forward of [prompt + answer] capturing the residual stream
#   at anchor / first_vis / mid25 / mid50 / mid75 / answer_end for all layers.
#   Feeds the CPU-side doubt/caution-plane re-decomposition (item 20) and the AK
#   Stage 1 crystallization / doubt-trajectory curves.
#
# SCOPING NOTE (read docs/preparation/diagnostics-bundle-launch-plan.md): this is a COARSE position sweep via
# the validated Amendment S/R re-forward path, NOT the full per-token decode-step
# capture that AK-2 (task #76) specifies. It answers item 20 (does the off-axis
# geometry hold mid-generation) and gives AK Stage 1 its position curve at 6
# points; a token-granular AK-2 runner is separate, larger work.
#
# BATCH POLICY: generation is greedy batch-1 (parity-locked to the AH/AI serving
# path); the re-forward is forward-only batch-1. Do NOT batch — parity-locked.
#
# CHECKPOINT: the AF/AG prime surface = deployed clean-SFT->GRPO-v2
#   base    : professorsynapse/eh-qwen3-4b-clean-sft-seed1-merged-16bit
#   adapter : professorsynapse/eh-qwen3-4b-clean-sft-grpo-seed1-lora
# (caller passes them; axes are refit per checkpoint downstream, per Amendment T.)
#
# Runs AFTER runpod_run_job.py cloned the repo at a pinned commit and cd'd in.
# Requires HF_TOKEN in the pod env for the private base/adapter/pool downloads
# and the staging upload.
#
# Usage:
#   experiments/diag-item20-gentime-displacement/cloud/runpod_diag_gentime_positions.sh <staging_repo> <base_model> <adapter_repo> \
#       <adapter_revision> <pool_path_in_repo> [run_tag] [limit]
set -euo pipefail

STAGING_REPO="$1"; BASE_MODEL="$2"; ADAPTER_REPO="$3"
ADAPTER_REV="$4"; POOL_IN_REPO="$5"
RUN_TAG="${6:-diag-item20-gentime-r1}"
LIMIT="${7:-600}"

PROBE="experiment/phase1/probe"
CLOUD="experiments/common/cloud"
OUT="/tmp/${RUN_TAG}"
mkdir -p "${OUT}"

BOOT_ID="$(date -u +%Y%m%dT%H%M%SZ)"
JOB_LOG="${OUT}/job_log_${BOOT_ID}.txt"
exec > >(tee -a "${JOB_LOG}") 2>&1

(
    while sleep "${LOG_PUSH_INTERVAL:-300}"; do
        python "${CLOUD}/upload_result.py" \
            --repo "${STAGING_REPO}" \
            --path-prefix "${RUN_TAG}/logs" \
            --file "${JOB_LOG}" >/dev/null 2>&1 || true
    done
) &
LOG_PUSHER_PID=$!
trap 'kill "${LOG_PUSHER_PID}" 2>/dev/null || true' EXIT

# shellcheck source=experiments/common/cloud/job_failure_trap.sh
source "${CLOUD}/job_failure_trap.sh"
FAIL_STAGING_REPO="${STAGING_REPO}"
FAIL_RUN_TAG="${RUN_TAG}"
FAIL_JOB_LOG="${JOB_LOG}"
FAIL_UPLOADER="${CLOUD}/upload_result.py"
install_failure_trap

echo "[diag-item20] boot=${BOOT_ID} run_tag=${RUN_TAG} limit=${LIMIT}"
echo "[diag-item20] base=${BASE_MODEL} adapter=${ADAPTER_REPO}@${ADAPTER_REV}"
echo "[diag-item20] staging=${STAGING_REPO} pool=${POOL_IN_REPO}"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader || true

POOL_LOCAL="${OUT}/pool.jsonl"
python - "$STAGING_REPO" "$POOL_IN_REPO" "$POOL_LOCAL" <<'PY'
import sys, shutil
from huggingface_hub import hf_hub_download
repo, path_in_repo, dest = sys.argv[1:4]
p = hf_hub_download(repo_id=repo, filename=path_in_repo, repo_type="dataset")
shutil.copyfile(p, dest)
print(f"[diag-item20] fetched pool {repo}:{path_in_repo} -> {dest}")
PY

# NO --keep-answer-text: the A0/AH pools may include NO-LICENSE source text;
# answer_text stays out of the shipped rows unless a licensed pool is confirmed.
python "${PROBE}/amendment_ak_gentime_positions_extract.py" \
    --pool "${POOL_LOCAL}" \
    --base-model "${BASE_MODEL}" \
    --adapter-repo "${ADAPTER_REPO}" --adapter-revision "${ADAPTER_REV}" \
    --limit "${LIMIT}" \
    --out-dir "${OUT}/gentime/data"
test -f "${OUT}/gentime/data/manifest.json" || { echo "[diag-item20] FATAL: no manifest"; exit 1; }

TARBALL="${OUT}/gentime_data.tar.gz"
tar -C "${OUT}/gentime" -czf "${TARBALL}" data
python "${CLOUD}/upload_result.py" \
    --repo "${STAGING_REPO}" --path-prefix "${RUN_TAG}/gentime" --file "${TARBALL}"

python "${CLOUD}/upload_result.py" \
    --repo "${STAGING_REPO}" --path-prefix "${RUN_TAG}/logs" --file "${JOB_LOG}" || true
echo "[diag-item20] DONE"
