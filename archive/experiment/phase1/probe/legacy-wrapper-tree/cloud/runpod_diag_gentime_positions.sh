#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "${SCRIPT_DIR}/../../../.." && pwd)"

exec bash "${REPO}/experiments/diag-item20-gentime-displacement/cloud/runpod_diag_gentime_positions.sh" "$@"
