#!/usr/bin/env bash
# Amendment SR — sampled-decode seed-robustness queue.
# Re-runs the Z training-free two-signal readout under SAMPLED decoding
# (temp 0.7 / top_p 0.9) across 3 seeds on the 4 confirmatory families.
# Mirrors the Z queue: per-family compat smoke (greedy, loader/shape gate) once,
# then per-seed sampled extraction (docker GPU) + CPU scoring (host).
#
# Pre-reg: experiments/sampled-decode-seed-robustness/AMENDMENT.md
# Scope: dial + veto only (gate is decode-invariant; emitted as invariance check).
# NOT to be run without explicit user launch approval.
#
# Run from repo root:  bash experiment/phase1/probe/amendment_sr_queue.sh
set -uo pipefail

REPO_WIN='F:\Code\Epistemic-Humility-Research'
IMAGE='unsloth-z:latest'
PROBE='experiment/phase1/probe'
GATE_ROWS='/workspace/repo/experiment/phase1/probe/qwen3-4b-clean-sft-grpo-v2-seed1-selfaware/hidden_states_selfaware_clean_sft_grpo_v2_full/extraction__55254a04aa1f/rows.jsonl'
LOG_DIR="$PROBE/sr_logs"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/PROGRESS.log"
log() { echo "[$(date -u +%H:%M:%S)] $*" | tee -a "$LOG"; }

# family_tag | HF repo   (tags match _safe_model_tag output)
MODELS=(
  "llama-3.2-3b|unsloth/Llama-3.2-3B-Instruct"
  "ministral-3-3b|mistralai/Ministral-3-3B-Instruct-2512"
  "qwen3.5-4b|Qwen/Qwen3.5-4B"
  "gemma-4-e4b|google/gemma-4-E4B-it"
)
SEEDS=(20260701 20260702 20260703)
TEMP=0.7
TOP_P=0.9

# docker run wrapper (GPU); $* = python-script + args, executed in-container.
dgpu() {
  docker.exe run --rm --gpus all --ipc=host --entrypoint python \
    -e HF_HOME=/workspace/repo/.cache/hf \
    -e HUGGINGFACE_HUB_CACHE=/workspace/repo/.cache/hf/hub \
    -v "${REPO_WIN}:/workspace/repo" -w /workspace/repo \
    "$IMAGE" "$@"
}

log "=== Amendment SR sampled-decode seed-robustness queue START (image $IMAGE, temp $TEMP top_p $TOP_P) ==="

for entry in "${MODELS[@]}"; do
  TAG="${entry%%|*}"; REPO="${entry##*|}"
  log "----- FAMILY $TAG ($REPO) -----"

  # 1) compat smoke (greedy, small) — loader + hidden-states shape + non-degenerate pool
  SMOKE="$PROBE/sr_smoke_${TAG}"
  log "$TAG: smoke (greedy, max-attempts 80, n-answerable 200) ..."
  dgpu /workspace/repo/$PROBE/amendment_x_cross_model_extract.py \
      --base-model "$REPO" --gate-rows "$GATE_ROWS" \
      --out-dir "/workspace/repo/$SMOKE" \
      --max-attempts 80 --n-answerable 200 --seed 20260701 >>"$LOG" 2>&1
  if [ ! -f "$SMOKE/manifest.json" ]; then
    log "$TAG: SMOKE FAILED (no manifest) -> INELIGIBLE, skipping family"
    continue
  fi
  HD=$(python3 -c "import json;print(json.load(open('$SMOKE/manifest.json')).get('hidden_dim','?'))" 2>/dev/null)
  log "$TAG: smoke OK hidden_dim=$HD"

  # 2) per-seed sampled extraction + CPU score
  for SEED in "${SEEDS[@]}"; do
    OUT="$PROBE/sr_${TAG}_seed${SEED}"
    RES="experiments/sampled-decode-seed-robustness/artifacts/amendment_sr_${TAG}_seed${SEED}_result.json"
    log "$TAG seed=$SEED: sampled extraction (temp $TEMP top_p $TOP_P, max-attempts 3000, n-answerable 2000) ..."
    dgpu /workspace/repo/$PROBE/amendment_x_cross_model_extract.py \
        --base-model "$REPO" --gate-rows "$GATE_ROWS" \
        --out-dir "/workspace/repo/$OUT" \
        --do-sample --temperature "$TEMP" --top-p "$TOP_P" \
        --max-attempts 3000 --n-answerable 2000 --seed "$SEED" \
        --wrong-floor 30 --hallucination-floor 50 >>"$LOG" 2>&1
    if [ ! -f "$OUT/manifest.json" ]; then
      log "$TAG seed=$SEED: EXTRACTION FAILED (no manifest), skipping seed"
      continue
    fi
    log "$TAG seed=$SEED: scoring (local CPU) ..."
    python3 "$PROBE/amendment_x_cross_model_score.py" \
        --x-dir "$OUT" --out "$RES" --seed "$SEED" >>"$LOG" 2>&1
    if [ -f "$RES" ]; then
      python3 - "$RES" <<'PY' | tee -a "$LOG"
import json,sys
r=json.load(open(sys.argv[1]))
gate=r["X_G1_gate"]["answerability_auroc"]
dial=r["X_G2_dial"]["auroc_correct_vs_wrong"]
dpass=r["X_G2_dial"]["pass_ge_0.65_ci_excl_0.50"]
veto=r["X_G3_veto_PRIMARY"]["auroc_correct_vs_hallucination"]
vpass=r["X_G3_veto_PRIMARY"]["pass_ge_0.65_ci_excl_0.50"]
adq=r.get("data_adequacy_ok")
print(f"   -> {sys.argv[1].split('/')[-1]}  gate={gate}  dial={dial}(pass={dpass})  "
      f"veto={veto}(pass={vpass})  adequacy={adq}  [gate=invariance-check only]")
PY
    else
      log "$TAG seed=$SEED: SCORING FAILED (no result json)"
    fi
  done
done

log "=== Amendment SR queue COMPLETE ==="
