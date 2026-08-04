#!/bin/bash
# Runtime storage hygiene for the local 3090 lane.
#
# Born from the 2026-08-02 disk-full crash (root volume hit 100% mid-merge and
# truncated a safetensors shard). Run `stage` at every experiment stage
# boundary; run `scan` monthly or whenever free space drops below ~200G.
#
# Modes:
#   prune_runtime.sh stage   - safe boundary prune: stopped containers + dangling images
#   prune_runtime.sh scan    - report-only: HF cache sizes, merged-16bit dirs eligible
#                              for deletion per the retention policy, disk headroom
#
# Retention policy (docs/checkpoint-staging.md is the registry of record):
#   1. Docker: stopped containers and dangling <none> images are always safe to
#      prune at a stage boundary. NEVER `docker image prune -a` -- the pinned
#      training image (see .skills/experiment-runner/reference/local-runtime.md)
#      must survive; it was lost once this way and had to be re-pulled by digest.
#   2. HF cache: keep (a) base models named in any in-flight experiment's
#      cell.yaml/experiment.yaml, (b) anything referenced by files younger than
#      14 days under experiments/ or ~/code/ehr-worktrees/. Everything else is
#      re-downloadable and prunable.
#   3. merged-16bit dirs: once a run's adapter has a checkpoint-staging.md row
#      (staged on HF with a revision SHA), its merged-16bit is regenerable
#      (adapter + base + merge, ~15 min) and prunable UNLESS it is the training
#      source for a still-running multi-stage chain.
#   4. checkpoints/ rotation dirs are redundant once final_model exists and the
#      run is complete; prunable immediately post-completion.
#   5. Eval results_* dirs and probe/ hidden-state caches are NEVER pruned by
#      this script -- irreplaceable scored rows / extractions.

set -uo pipefail
export DOCKER_HOST="${DOCKER_HOST:-unix:///var/run/docker.sock}"
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
MODE="${1:-scan}"

case "$MODE" in
  stage)
    echo "== stage-boundary prune =="
    docker container prune -f
    docker image prune -f   # dangling only; never -a (protects the pinned image)
    df -h / | tail -1
    ;;
  scan)
    echo "== disk =="
    df -h / | tail -1
    echo
    echo "== HF cache (largest first; check against retention policy) =="
    /usr/bin/du -sh "$HOME"/.cache/huggingface/hub/models--* 2>/dev/null | sort -rh | head -20
    echo
    echo "== merged-16bit dirs on disk (candidates if adapter is HF-staged and not an active chain source) =="
    /usr/bin/find "$REPO/scratch" "$REPO/synaptic-tuner/toolset-training-artifacts" \
      -type d \( -name 'merged-16bit' -o -name 'merged-16bit-*' \) 2>/dev/null \
      | while read -r d; do /usr/bin/du -sh "$d"; done | sort -rh
    echo
    echo "== completed-run checkpoints/ rotation dirs (prunable when run complete) =="
    /usr/bin/find "$REPO/scratch" "$REPO/synaptic-tuner/toolset-training-artifacts" \
      -type d -name 'checkpoints' 2>/dev/null \
      | while read -r d; do /usr/bin/du -sh "$d"; done | sort -rh | head -15
    echo
    echo "Registry of record: docs/checkpoint-staging.md (never delete a run dir without a row there or lead sign-off)."
    ;;
  *)
    echo "usage: prune_runtime.sh {stage|scan}" >&2
    exit 2
    ;;
esac
