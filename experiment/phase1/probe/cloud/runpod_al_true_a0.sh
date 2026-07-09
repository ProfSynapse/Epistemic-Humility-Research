#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "${SCRIPT_DIR}/../../../.." && pwd)"

exec bash "${REPO}/experiments/radial-anti-propensity-steering/cloud/runpod_al_true_a0.sh" "$@"
