#!/usr/bin/env bash
# Diagnostics bundle cell 4 (TODO item 9) — cross-checkpoint caution "assembly
# timeline". Lab-notebook diagnostic (tier L): no amendment, no gates.
#
# WHAT
#   Pre-generation anchor extraction (full layer stack L0..L36, prompt_len-1)
#   on ONE fixed pool, run once per checkpoint of the training regimen so the
#   CPU-side analysis can fit/read the caution direction per stage and plot
#   AUROC + direction cosine vs training stage. Pure forward-only extraction,
#   no generation, no intervention.
#
# CHECKPOINTS (one --stage extract pass each, same pool, same layers):
#   raw       : unsloth/Qwen3-4B-bnb-4bit                                 (no adapter)
#   clean-sft : ...-clean-sft-seed1-merged-16bit                          (no adapter; merged)
#   grpo-v2   : ...-clean-sft-seed1-merged-16bit + clean-sft-grpo-seed1-lora
#   par-true  : ...-clean-sft-seed1-merged-16bit + clean-sft-grpo-par-true-seed1-lora
#   (the caller passes the (base, adapter, adapter_rev, stage_tag) tuple; this
#    script runs exactly one stage per invocation so a pod can chain them.)
#
# BATCH POLICY: pure extraction, forward-only, deterministic anchor — batchable
# in principle, but the shared engine (amendment_ai_verdict_extract_gen.py) runs
# batch-1 anchor forwards, which is fine at this pool size. No parity lock.
#
# Runs AFTER runpod_run_job.py cloned the repo at a pinned commit and cd'd in.
# Requires HF_TOKEN in the pod env (forwarded by the launcher, never embedded)
# for the private base/adapter/pool downloads and the staging upload.
#
# Usage:
#   experiments/diag-item9-caution-assembly-timeline/cloud/runpod_diag_caution_timeline.sh <staging_repo> <base_model> <adapter_repo> \
#       <adapter_revision> <pool_path_in_repo> <stage_tag> [run_tag] [num_layers]
#   Pass adapter_repo="-" and adapter_revision="-" for the no-adapter stages
#   (raw, clean-sft merged).
set -euo pipefail

STAGING_REPO="$1"; BASE_MODEL="$2"; ADAPTER_REPO="$3"
ADAPTER_REV="$4"; POOL_IN_REPO="$5"; STAGE_TAG="$6"
RUN_TAG="${7:-diag-item9-${STAGE_TAG}-r1}"
NUM_LAYERS="${8:-36}"

PROBE="experiment/phase1/probe"
CLOUD="experiments/common/cloud"
OUT="/tmp/${RUN_TAG}"
mkdir -p "${OUT}"

BOOT_ID="$(date -u +%Y%m%dT%H%M%SZ)"
JOB_LOG="${OUT}/job_log_${BOOT_ID}.txt"
exec > >(tee -a "${JOB_LOG}") 2>&1

# Periodic log push so a dead pod still leaves a trail (RunPod has no logs API).
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

echo "[diag-item9] boot=${BOOT_ID} run_tag=${RUN_TAG} stage=${STAGE_TAG}"
echo "[diag-item9] base=${BASE_MODEL} adapter=${ADAPTER_REPO}@${ADAPTER_REV}"
echo "[diag-item9] staging=${STAGING_REPO} pool=${POOL_IN_REPO} layers=L0..L${NUM_LAYERS}"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader || true

POOL_LOCAL="${OUT}/pool.jsonl"
python - "$STAGING_REPO" "$POOL_IN_REPO" "$POOL_LOCAL" <<'PY'
import sys, shutil
from huggingface_hub import hf_hub_download
repo, path_in_repo, dest = sys.argv[1:4]
p = hf_hub_download(repo_id=repo, filename=path_in_repo, repo_type="dataset")
shutil.copyfile(p, dest)
print(f"[diag-item9] fetched pool {repo}:{path_in_repo} -> {dest}")
PY

LAYER_LIST="$(python - "$NUM_LAYERS" <<'PY'
import sys
print(",".join(f"L{i}" for i in range(int(sys.argv[1]) + 1)))
PY
)"

# --adapter args only when an adapter is supplied ("-" == no adapter stage).
ADAPTER_ARGS=()
if [ "${ADAPTER_REPO}" != "-" ]; then
    ADAPTER_ARGS+=(--adapter-repo "${ADAPTER_REPO}")
    if [ "${ADAPTER_REV}" != "-" ]; then
        ADAPTER_ARGS+=(--adapter-revision "${ADAPTER_REV}")
    fi
fi

# ---- full-stack pre-gen extraction for this checkpoint stage ----
python "${PROBE}/amendment_ai_verdict_extract_gen.py" \
    --stage extract --surface union --pool "${POOL_LOCAL}" \
    --base-model "${BASE_MODEL}" \
    "${ADAPTER_ARGS[@]}" \
    --layers "${LAYER_LIST}" \
    --out-dir "${OUT}/extract/data"
test -f "${OUT}/extract/data/manifest.json" || { echo "[diag-item9] FATAL: no extract manifest"; exit 1; }

# ---- upload: extract dir as one tarball, namespaced by stage tag ----
TARBALL="${OUT}/extract_data_${STAGE_TAG}.tar.gz"
tar -C "${OUT}/extract" -czf "${TARBALL}" data
python "${CLOUD}/upload_result.py" \
    --repo "${STAGING_REPO}" --path-prefix "${RUN_TAG}/extract" --file "${TARBALL}"

# final log push
python "${CLOUD}/upload_result.py" \
    --repo "${STAGING_REPO}" --path-prefix "${RUN_TAG}/logs" --file "${JOB_LOG}" || true
echo "[diag-item9] DONE stage=${STAGE_TAG}"
