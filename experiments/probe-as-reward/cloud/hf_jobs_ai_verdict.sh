#!/usr/bin/env bash
# Amendment AI verdict-eval cell wrapper (extract | generate) inside an HF Job.
#
# Distinct from hf_jobs_cell.sh (the X/Z/Y readout lane): this cell serves a
# PRIVATE clean-SFT base + a PRIVATE trained LoRA adapter, and its TENSORS are
# the deliverable (the CPU scorer refits a fresh probe on them), so it uploads
# whole extraction/generation dirs to a PRIVATE staging dataset repo rather than
# a few small files to the public results repo.
#
# Runs AFTER the launcher's bootstrap cloned the repo at a pinned commit and cd'd
# into it. The input pool (union rows or 400-row holdout) is fetched from the
# private staging repo because the union surface derives from NO-LICENSE FalseQA
# source text that never enters the public repo.
#
# Usage (positional, then passthrough args to the entry script):
#   experiments/probe-as-reward/cloud/hf_jobs_ai_verdict.sh <stage> <surface_or_-> <arm_tag> <staging_repo> \
#       <base_model> <adapter_repo> <adapter_revision> <pool_path_in_repo> \
#       [extra amendment_ai_verdict_extract_gen.py args...]
#
#   stage    : extract | generate
#   surface  : union | holdout  (use "-" for generate)
#   arm_tag  : true | permuted  (namespaces the staging upload prefix)
#
# Requires: HF_TOKEN in env (job secret) for the private base/adapter/pool
# downloads AND the upload.
set -euo pipefail

STAGE="$1"; SURFACE="$2"; ARM_TAG="$3"; STAGING_REPO="$4"
BASE_MODEL="$5"; ADAPTER_REPO="$6"; ADAPTER_REV="$7"; POOL_IN_REPO="$8"
shift 8

PROBE="archive/experiment/phase1/probe"
CLOUD="experiments/common/cloud"
RUN_TAG="ai-verdict-${ARM_TAG}-${STAGE}-${SURFACE}"
OUT="/tmp/${RUN_TAG}"
mkdir -p "${OUT}"

# Durable log capture (same rationale as hf_jobs_cell.sh: HF preemption wipes
# the live log stream; a fresh BOOT_ID per incarnation makes a restart visible
# as two log files under one run tag).
BOOT_ID="$(date -u +%Y%m%dT%H%M%SZ)"
JOB_LOG="${OUT}/job_log_${BOOT_ID}.txt"
exec > >(tee -a "${JOB_LOG}") 2>&1

(
    while sleep "${LOG_PUSH_INTERVAL:-600}"; do
        python "${CLOUD}/upload_result.py" \
            --repo "${STAGING_REPO}" \
            --path-prefix "${RUN_TAG}/logs" \
            --file "${JOB_LOG}" >/dev/null 2>&1 || true
    done
) &
LOG_PUSHER_PID=$!
trap 'kill "${LOG_PUSHER_PID}" 2>/dev/null || true' EXIT

echo "[ai-verdict] boot=${BOOT_ID} stage=${STAGE} surface=${SURFACE} arm=${ARM_TAG}"
echo "[ai-verdict] base=${BASE_MODEL} adapter=${ADAPTER_REPO}@${ADAPTER_REV}"
echo "[ai-verdict] staging=${STAGING_REPO} pool=${POOL_IN_REPO}"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader || true

# Fetch the input pool from the private staging repo (HF_TOKEN authorizes).
POOL_LOCAL="${OUT}/pool.jsonl"
python - "$STAGING_REPO" "$POOL_IN_REPO" "$POOL_LOCAL" <<'PY'
import sys, shutil
from huggingface_hub import hf_hub_download
repo, path_in_repo, dest = sys.argv[1:4]
p = hf_hub_download(repo_id=repo, filename=path_in_repo, repo_type="dataset")
shutil.copyfile(p, dest)
print(f"[ai-verdict] fetched pool {repo}:{path_in_repo} -> {dest}")
PY

STAGE_ARGS=(--stage "${STAGE}" --pool "${POOL_LOCAL}" \
            --base-model "${BASE_MODEL}" --out-dir "${OUT}/data")
if [ "${STAGE}" = "extract" ]; then
    STAGE_ARGS+=(--surface "${SURFACE}")
fi
if [ "${ADAPTER_REPO}" != "-" ]; then
    STAGE_ARGS+=(--adapter-repo "${ADAPTER_REPO}")
fi
if [ "${ADAPTER_REV}" != "-" ]; then
    STAGE_ARGS+=(--adapter-revision "${ADAPTER_REV}")
fi

python "${PROBE}/amendment_ai_verdict_extract_gen.py" "${STAGE_ARGS[@]}" "$@"

test -f "${OUT}/data/manifest.json" || { echo "[ai-verdict] FATAL: no manifest.json"; exit 1; }
test -f "${OUT}/data/rows.jsonl"   || { echo "[ai-verdict] FATAL: no rows.jsonl"; exit 1; }

# Upload the WHOLE data dir (tensors + rows.jsonl + manifest.json) to the
# private staging repo. The scorer consumes this dir verbatim as
# --*-fit-states / --*-holdout-states / --*-gen.
# HF rejects commits with >10,000 files in one repo directory, and the union
# extract writes one tensor file per row (18,496) — oversized dirs ship as a
# single tarball instead, which the scorer host untars back to the same layout.
N_FILES=$(find "${OUT}/data" -type f | wc -l)
if [ "${N_FILES}" -gt 9500 ]; then
    echo "[ai-verdict] data dir has ${N_FILES} files (>9500); uploading as tarball"
    TARBALL="${OUT}/data.tar.gz"
    tar -C "${OUT}" -czf "${TARBALL}" data
    python "${CLOUD}/upload_result.py" \
        --repo "${STAGING_REPO}" \
        --path-prefix "${RUN_TAG}" \
        --file "${TARBALL}"
else
    python "${CLOUD}/upload_folder.py" \
        --repo "${STAGING_REPO}" \
        --folder "${OUT}/data" \
        --path-in-repo "${RUN_TAG}/data" \
        --private
fi

echo "[ai-verdict] DONE ${RUN_TAG}"

# Final log push so the completed incarnation's full log is durable too.
python "${CLOUD}/upload_result.py" \
    --repo "${STAGING_REPO}" \
    --path-prefix "${RUN_TAG}/logs" \
    --file "${JOB_LOG}" || true
