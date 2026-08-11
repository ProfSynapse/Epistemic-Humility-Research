#!/usr/bin/env bash
# Pinned-container launch wrapper for this cell's GPU stages, following the
# proven run pattern established in NOTEBOOK.md's feasibility-probe Stage B
# relaunch entries (read in full before writing this script) and the binding
# invariant in .skills/mechinterp-cells/reference/modal-launch.md "Local GPU
# runs execute in a pinned container".
#
# F3 fix: this script previously resolved and ran a *different* image
# entirely -- the local `mechinterp-runner:local` tag -- while only reading
# cell.yaml's `execution.runtime_image_digest` (the pinned
# `unsloth/unsloth@sha256:f21629b9...` digest) to print a WARNING on
# mismatch, never actually using it to select what runs. That is a silent
# instrument substitution: every GPU verb launched through the old script ran
# against an unrelated, unpinned image. This version resolves and runs the
# image BY THE REGISTERED DIGEST from cell.yaml, full stop, and exits 1 if
# that digest is not present in the local image store. It never falls back to
# mechinterp-runner or any tag-based resolution.
#
# F18 fix: this script is meant to run detached, under
# `experiments/common/launch_detached.sh` (setsid/nohup wrapper, no tty). The
# previous `docker run --rm -it` used `-it`, which is incompatible with a
# detached, stdin-redirected-from-/dev/null invocation and would hang or
# error under that wrapper. This version drops `-it`, adds a deterministic
# `--name` (so a stuck/orphaned container is identifiable and the "one GPU
# job at a time" invariant is checkable via `docker ps`), adds `--ipc=host`
# (required by the proven recipe; without it PyTorch's shared-memory
# multiprocessing primitives can fail inside the container), and fixes the HF
# cache mount path: `unsloth/unsloth:latest` runs as non-root uid 1001
# (`unsloth`, home `/home/unsloth`), not root, so mounting to
# `/root/.cache/huggingface` (the old path) put the cache somewhere the
# container's own HF client never reads from, silently disabling on-disk
# cache reuse and re-downloading every launch. HF_HOME/HUGGINGFACE_HUB_CACHE
# are also now set explicitly rather than relied upon implicitly, per the
# proven recipe in NOTEBOOK.md.
#
# Usage (from the repo root, i.e. the parent of synaptic-tuner/):
#   experiments/caution-install-bounded-site-sweep/docker_launch.sh \
#     extract_anchor.py --substrate trained --i-know-this-runs-on-gpu
#
# Detached usage (the intended real-run path):
#   experiments/common/launch_detached.sh /path/to/run.log \
#     experiments/caution-install-bounded-site-sweep/docker_launch.sh \
#     extract_anchor.py --substrate trained --i-know-this-runs-on-gpu
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$HERE/../.." && pwd)"

if [ "$#" -lt 1 ]; then
  echo "usage: $0 <stage_script.py> [args...]" >&2
  exit 2
fi

STAGE_SCRIPT="$1"
shift

# The registered digest is pinned as a bare sha256:... value; NOTEBOOK.md's
# proven launches establish it is unsloth/unsloth's digest, so the repo name
# is fixed here rather than re-derived (cell.yaml does not itself carry a
# separate image-repo field to read).
IMAGE_REPO="unsloth/unsloth"
PINNED_DIGEST="$(python3 - "$HERE/cell.yaml" <<'PY'
import sys, yaml
with open(sys.argv[1]) as f:
    cell = yaml.safe_load(f)
print(cell["execution"]["runtime_image_digest"])
PY
)"

if [ -z "${PINNED_DIGEST:-}" ]; then
  echo "ERROR: could not read execution.runtime_image_digest from $HERE/cell.yaml." >&2
  exit 1
fi

DOCKER_CTX="$(docker context show 2>/dev/null || echo unknown)"
if [ "$DOCKER_CTX" = "desktop-linux" ]; then
  echo "WARNING: active docker context is desktop-linux (a Windows npipe a "\
"WSL2 shell often cannot drive for --gpus all). If this launch fails at "\
"docker run with 'Failed to initialize: protocol not available' or --gpus "\
"is silently ignored, run: docker context use default (see "\
".skills/mechinterp-cells/reference/modal-launch.md 'One socket, two Docker "\
"daemons')." >&2
fi

if ! docker info 2>/dev/null | grep -qi nvidia; then
  echo "WARNING: 'docker info' does not list an nvidia runtime. --gpus all "\
"will fail at container start, not silently. Confirm the NVIDIA Container "\
"Toolkit is registered before proceeding." >&2
fi

# F3: resolve BY DIGEST, never by a mutable tag, and never substitute a
# different image. `docker image inspect` on a repo@sha256:... reference
# resolves purely from the local image store's own digest index -- it does
# NOT pull, so this fails closed (exit 1) rather than silently fetching an
# unverified image if the digest is not already present locally.
IMAGE_REF="${IMAGE_REPO}@${PINNED_DIGEST}"
if ! docker image inspect "$IMAGE_REF" >/dev/null 2>&1; then
  echo "ERROR: pinned image '$IMAGE_REF' is not present in the local image "\
"store. This script refuses to run any other image (no tag fallback, no "\
"substitution of a different image such as mechinterp-runner). Pull or "\
"load the exact pinned digest first, e.g.:" >&2
  echo "  docker pull ${IMAGE_REPO}@${PINNED_DIGEST}" >&2
  exit 1
fi

CONTAINER_NAME="caution-install-sweep-$(basename "$STAGE_SCRIPT" .py)-$(date -u +%Y%m%dT%H%M%SZ)"

echo "[docker_launch] repo_root=$REPO_ROOT stage_script=$STAGE_SCRIPT " \
     "image_ref=$IMAGE_REF container_name=$CONTAINER_NAME"

# F18: no -it (detached, no tty available under launch_detached.sh);
# --ipc=host and the /home/unsloth HF cache path/env vars per the proven
# recipe (NOTEBOOK.md Stage B relaunch entries); --entrypoint python3
# overrides the base image's own entrypoint the same way the proven launches
# did, which is also why sweep_lib.emit_provenance_line() (F17), not the
# mechinterp-runner image's own print_provenance.py entrypoint, is what
# emits this run's provenance JSON line into the log.
docker run --rm \
  --name "$CONTAINER_NAME" \
  --gpus all \
  --ipc=host \
  --entrypoint python3 \
  -v "$HOME/.cache/huggingface:/home/unsloth/.cache/huggingface" \
  -v "$REPO_ROOT:/workspace" \
  -w "/workspace/experiments/caution-install-bounded-site-sweep" \
  --env IMAGE_DIGEST="$PINNED_DIGEST" \
  --env HF_HOME="/home/unsloth/.cache/huggingface" \
  --env HUGGINGFACE_HUB_CACHE="/home/unsloth/.cache/huggingface" \
  --env HF_TOKEN \
  --env PYTHONPATH="/workspace/synaptic-tuner:/workspace/experiments/caution-install-bounded-site-sweep" \
  "$IMAGE_REF" \
  "$STAGE_SCRIPT" "$@"
