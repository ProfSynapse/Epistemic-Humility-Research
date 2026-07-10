#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "${SCRIPT_DIR}/../../../.." && pwd)"

exec bash "${REPO}/experiments/diag-item11-batched-steering-equivalence/cloud/runpod_diag_gpu_equiv.sh" "$@"
