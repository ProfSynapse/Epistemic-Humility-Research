#!/usr/bin/env bash
# Runs the eight registered cells in the pinned pipeline order; the primary pair is first. Halts at the first
# failure. Each cell resumes from its durable output, so rerunning this script after
# a stop continues the work. Launch through experiments/common/launch_detached.sh.
set -euo pipefail
P=/mnt/e/SynapticResearch/preparation/astra-r1-cpu-20261103
M=/mnt/e/Models/Epistemic-Humility-Research/base/Qwen3.5-4B/851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a
S=qwen35-4b-hs20-native-weight-edit
MOUNT=/workspace/.synaptic/artifacts/$S/base_model
EDITED=/workspace/.synaptic/artifacts/$S/astra-r1/checkpoints/edited
IMAGE=sha256:408fecc6e644cfb62f028ff064a226eab1fe2b24dbc5853a82ed0d20b039d224
REV=851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a
export DOCKER_HOST=unix:///var/run/docker.sock
for cell in selfaware:P-struct:base selfaware:P-struct:edited selfaware:P-rc:base selfaware:P-rc:edited \
            ambigqa:P-struct:base ambigqa:P-struct:edited ambigqa:P-rc:base ambigqa:P-rc:edited; do
  IFS=: read -r surface prompt arm <<<"$cell"
  if [ -f "$P/.synaptic/artifacts/$S/astra-r1/evaluation/$surface/$prompt/$arm/final.manifest.json" ]; then
    echo "skip complete $cell"; continue
  fi
  echo "cell start $cell $(date -Is)"
  docker run --rm --name "ehr-astra-eval-$surface-$prompt-$arm" --gpus all --shm-size=8g --network none --entrypoint python \
    -v "$P:/workspace" -v "$M:$MOUNT:ro" -w /workspace -e PYTHONPATH=/workspace/experiments/$S \
    -e EHR_RUNTIME_IMAGE_ID="$IMAGE" -e HF_HUB_OFFLINE=1 -e HS20NWE_RENDER_MODEL="$MOUNT" -e HS20NWE_RENDER_REVISION=$REV \
    -e GIT_CONFIG_COUNT=1 -e GIT_CONFIG_KEY_0=safe.directory -e GIT_CONFIG_VALUE_0=/workspace \
    "$IMAGE" -m hs20_nwe.astra_run eval-cell --surface "$surface" --prompt "$prompt" --arm "$arm" \
    --base-model "$MOUNT" --edited-model "$EDITED" --gpu-ack
  echo "cell complete $cell $(date -Is)"
done
echo "EVALUATION_COMPLETE $(date -Is)"
