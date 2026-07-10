#!/usr/bin/env bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "${SCRIPT_DIR}/../../../.." && pwd)"

# shellcheck source=experiments/common/cloud/job_failure_trap.sh
source "${REPO}/experiments/common/cloud/job_failure_trap.sh"
