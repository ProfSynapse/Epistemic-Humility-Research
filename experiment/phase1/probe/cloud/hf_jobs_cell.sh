#!/usr/bin/env bash
# Cloud-lane cell wrapper: one cross-model readout cell inside an HF Job.
#
# Runs AFTER the launcher's bootstrap has cloned this repo at a pinned commit
# and cd'd into it. Executes the same extract -> score pair as the local
# dgpu lane (Amendments X/Z/SR), then uploads ONLY the small result JSON +
# manifest to a results dataset repo. The multi-hundred-MB extraction dir
# stays on the ephemeral job disk (matches the untracked-outputs convention).
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
OUT="/tmp/cell_${RUN_TAG}"

echo "[cloud-cell] model=${MODEL} gate_rows=${GATE_ROWS} run_tag=${RUN_TAG}"
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

python "${PROBE}/cloud/upload_result.py" \
    --repo "${RESULTS_REPO}" \
    --path-prefix "${RUN_TAG}" \
    --file "${OUT}/result.json" \
    --file "${OUT}/manifest.json"

echo "[cloud-cell] DONE ${RUN_TAG}"
