#!/usr/bin/env bash
# One signed capture, then the CPU construction. Halts at the first failure.
# Launch through experiments/common/launch_detached.sh; the log is the output.
set -euo pipefail
P=/mnt/e/SynapticResearch/preparation/astra-r1-cpu-20261103
M=/mnt/e/Models/Epistemic-Humility-Research/base/Qwen3.5-4B/851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a
S=qwen35-4b-hs20-native-weight-edit
MOUNT=/workspace/.synaptic/artifacts/$S/base_model
IMAGE=sha256:408fecc6e644cfb62f028ff064a226eab1fe2b24dbc5853a82ed0d20b039d224
REV=851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a
export DOCKER_HOST=unix:///var/run/docker.sock
COMMON=(--rm --network none --entrypoint python -v "$P:/workspace" -v "$M:$MOUNT:ro" -w /workspace
  -e PYTHONPATH=/workspace/experiments/$S -e EHR_RUNTIME_IMAGE_ID="$IMAGE" -e HF_HUB_OFFLINE=1
  -e HS20NWE_RENDER_MODEL="$MOUNT" -e HS20NWE_RENDER_REVISION=$REV
  -e GIT_CONFIG_COUNT=1 -e GIT_CONFIG_KEY_0=safe.directory -e GIT_CONFIG_VALUE_0=/workspace)
echo "capture start $(date -Is)"
docker run --name ehr-astra-capture "${COMMON[@]}" --gpus all --shm-size=8g "$IMAGE" -m hs20_nwe.astra_run capture --model "$MOUNT" --gpu-ack
echo "capture complete $(date -Is)"
docker run --name ehr-astra-construct "${COMMON[@]}" "$IMAGE" /workspace/experiments/$S/runtime/drive_construction_cpu.py
echo "CONSTRUCTION_COMPLETE $(date -Is)"
