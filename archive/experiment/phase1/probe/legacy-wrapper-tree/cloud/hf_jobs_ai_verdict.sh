#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "${SCRIPT_DIR}/../../../.." && pwd)"

exec bash "${REPO}/experiments/probe-as-reward/cloud/hf_jobs_ai_verdict.sh" "$@"
