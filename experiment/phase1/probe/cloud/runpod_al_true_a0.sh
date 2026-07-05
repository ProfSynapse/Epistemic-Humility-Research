#!/usr/bin/env bash
# Amendment AL prep — A0-style surface on the AI-TRUE checkpoint, RunPod lane.
#
# One pod, two stages on the SAME 1,662-row A0 pool (AH main-run pool_v21,
# question text joined in at staging time; KUQ/SelfAware/TriviaQA/PopQA only,
# no FalseQA):
#   1. generate : greedy batch-1 schema-contract generation (AH parity,
#                 max_new_tokens=96) with the TRUE LoRA applied. Grading
#                 (correct / confab_on_unanswerable via aliases) happens
#                 LOCALLY afterward from answer_text — the pod ships raw rows.
#   2. extract  : pre-generation states at the FULL layer stack L0..L36
#                 (closes the doubt-axis L35 gap; feeds the AL ceiling table
#                 and the hydra head census).
#
# This is also the first end-to-end smoke of the RunPod one-shot job lane
# (synaptic-tuner .skills/fine-tuning/scripts/runpod_run_job.py): the exact
# workload class (private base download + long extract + bulk upload) that
# repeatedly died on HF Jobs networking on 2026-07-04.
#
# Runs AFTER the launcher cloned the repo at a pinned commit and cd'd into it.
# Requires HF_TOKEN in the pod env (forwarded by the launcher, never embedded)
# for the private base/adapter/pool downloads and the staging upload.
#
# Usage:
#   runpod_al_true_a0.sh <staging_repo> <base_model> <adapter_repo> \
#       <adapter_revision> <pool_path_in_repo> [run_tag] [num_layers]
set -euo pipefail

STAGING_REPO="$1"; BASE_MODEL="$2"; ADAPTER_REPO="$3"
ADAPTER_REV="$4"; POOL_IN_REPO="$5"
RUN_TAG="${6:-al-prep-true-a0}"
NUM_LAYERS="${7:-36}"

PROBE="experiment/phase1/probe"
OUT="/tmp/${RUN_TAG}"
mkdir -p "${OUT}"

BOOT_ID="$(date -u +%Y%m%dT%H%M%SZ)"
JOB_LOG="${OUT}/job_log_${BOOT_ID}.txt"
exec > >(tee -a "${JOB_LOG}") 2>&1

(
    while sleep "${LOG_PUSH_INTERVAL:-300}"; do
        python "${PROBE}/cloud/upload_result.py" \
            --repo "${STAGING_REPO}" \
            --path-prefix "${RUN_TAG}/logs" \
            --file "${JOB_LOG}" >/dev/null 2>&1 || true
    done
) &
LOG_PUSHER_PID=$!
trap 'kill "${LOG_PUSHER_PID}" 2>/dev/null || true' EXIT

echo "[al-a0] boot=${BOOT_ID} run_tag=${RUN_TAG}"
echo "[al-a0] base=${BASE_MODEL} adapter=${ADAPTER_REPO}@${ADAPTER_REV}"
echo "[al-a0] staging=${STAGING_REPO} pool=${POOL_IN_REPO} layers=L0..L${NUM_LAYERS}"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader || true

POOL_LOCAL="${OUT}/pool.jsonl"
python - "$STAGING_REPO" "$POOL_IN_REPO" "$POOL_LOCAL" <<'PY'
import sys, shutil
from huggingface_hub import hf_hub_download
repo, path_in_repo, dest = sys.argv[1:4]
p = hf_hub_download(repo_id=repo, filename=path_in_repo, repo_type="dataset")
shutil.copyfile(p, dest)
print(f"[al-a0] fetched pool {repo}:{path_in_repo} -> {dest}")
PY

LAYER_LIST="$(python - "$NUM_LAYERS" <<'PY'
import sys
print(",".join(f"L{i}" for i in range(int(sys.argv[1]) + 1)))
PY
)"

# ---- stage 1: generation (raw rows incl. answer_text; graded locally) ----
python "${PROBE}/amendment_ai_verdict_extract_gen.py" \
    --stage generate --pool "${POOL_LOCAL}" \
    --base-model "${BASE_MODEL}" \
    --adapter-repo "${ADAPTER_REPO}" --adapter-revision "${ADAPTER_REV}" \
    --out-dir "${OUT}/gen/data"
test -f "${OUT}/gen/data/rows.jsonl" || { echo "[al-a0] FATAL: no gen rows"; exit 1; }

# ---- stage 2: full-stack pre-gen extraction ----
python "${PROBE}/amendment_ai_verdict_extract_gen.py" \
    --stage extract --surface union --pool "${POOL_LOCAL}" \
    --base-model "${BASE_MODEL}" \
    --adapter-repo "${ADAPTER_REPO}" --adapter-revision "${ADAPTER_REV}" \
    --layers "${LAYER_LIST}" \
    --out-dir "${OUT}/extract/data"
test -f "${OUT}/extract/data/manifest.json" || { echo "[al-a0] FATAL: no extract manifest"; exit 1; }

# ---- upload: gen dir as files, extract dir as one tarball ----
for f in "${OUT}/gen/data/rows.jsonl" "${OUT}/gen/data/manifest.json"; do
    python "${PROBE}/cloud/upload_result.py" \
        --repo "${STAGING_REPO}" --path-prefix "${RUN_TAG}/gen" --file "${f}"
done
TARBALL="${OUT}/extract_data.tar.gz"
tar -C "${OUT}/extract" -czf "${TARBALL}" data
python "${PROBE}/cloud/upload_result.py" \
    --repo "${STAGING_REPO}" --path-prefix "${RUN_TAG}/extract" --file "${TARBALL}"

# final log push
python "${PROBE}/cloud/upload_result.py" \
    --repo "${STAGING_REPO}" --path-prefix "${RUN_TAG}/logs" --file "${JOB_LOG}" || true
echo "[al-a0] DONE"
