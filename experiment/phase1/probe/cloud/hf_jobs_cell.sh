#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "${SCRIPT_DIR}/../../../.." && pwd)"

exec bash "${REPO}/experiments/common/cloud/hf_jobs_cell.sh" "$@"
