#!/usr/bin/env bash
# Amendment AA — Stage-1 causal confidence-steering queue (Qwen3.5-4B).
# Cells AA-1..AA-8 per experiments/causal-confidence-steering/AMENDMENT.md
# (SIGNED 2026-07-01; Stage-1 launch approved: AA-1..AA-8, Qwen3.5-4B, local
# Docker GPU lane, sequential).
#
# Order: smoke (tier-3 preflight) -> AA-1, AA-3 (sweeps) -> select alpha* per the
# locked rule -> AA-2, AA-4 (off-position at alpha*) -> AA-5..AA-8 (Arm B).
#
# alpha* rule (from the amendment, applied mechanically): the smallest |alpha| on
# the sweep whose vs-alpha=0 contrast passes the cell's effect gate (gate cells:
# abstention_unknown delta >= +0.15 with CI excluding 0 AND answer_rate_known
# delta >= -0.05; dial cells: revision_discrimination delta >= +0.10 with CI
# excluding 0) AND whose per-alpha coherence_floor_ok is true. Ties at the same
# |alpha| resolve to the larger effect delta. PRE-STATED FALLBACK (descriptive
# only, decided before any result exists): if NO alpha qualifies, the
# off-position cell still runs at the coherent alpha with the largest effect
# delta, labeled ALPHA_STAR_FALLBACK in the log — AA-G5 only gates combinations
# whose effect gate passed, so a fallback run adds descriptive data and cannot
# create a pass.
#
# Run from repo root:  bash experiment/phase1/probe/steering/amendment_aa_queue.sh
set -uo pipefail

REPO_WIN='F:\Code\Epistemic-Humility-Research'
IMAGE='unsloth-z:latest'
STEER='experiment/phase1/probe/steering'
MODEL='Qwen/Qwen3.5-4B'
GATE_ROWS='/workspace/repo/experiment/phase1/probe/qwen3-4b-clean-sft-grpo-v2-seed1-selfaware/hidden_states_selfaware_clean_sft_grpo_v2_full/extraction__55254a04aa1f/rows.jsonl'
DIR_GATE="/workspace/repo/experiments/common/artifacts/two_signal_probe_directions/qwen3.5-4b/direction_gate.json"
DIR_DIAL="/workspace/repo/experiments/common/artifacts/two_signal_probe_directions/qwen3.5-4b/direction_dial.json"
RESULTS="$STEER/results"
LOG_DIR="$STEER/aa_logs"
mkdir -p "$LOG_DIR" "$RESULTS"
LOG="$LOG_DIR/PROGRESS.log"
log() { echo "[$(date -u +%H:%M:%S)] $*" | tee -a "$LOG"; }

SEED=20260701
DECODE_ARGS=(--temperature 0.7 --top-p 0.9 --datasets-root /workspace/repo/datasets)
SWEEP='-4,-2,-1,0,1,2,4'

dgpu() {
  docker.exe run --rm --gpus all --ipc=host --user 0:0 --entrypoint python \
    -e HF_HOME=/workspace/repo/.cache/hf \
    -e HUGGINGFACE_HUB_CACHE=/workspace/repo/.cache/hf/hub \
    -v "${REPO_WIN}:/workspace/repo" -w /workspace/repo \
    "$IMAGE" "$@"
}

# select_alpha_star <cell_json> <gate|dial>  -> prints alpha* (exit 3 = fallback)
select_alpha_star() {
  python3 - "$1" "$2" <<'PY'
import json, sys
r = json.load(open(sys.argv[1])); kind = sys.argv[2]
per, vs = r["summary"]["per_alpha"], r["summary"]["vs_control"]
def ok(a):
    if not per[a].get("coherence_floor_ok"): return False
    c = vs.get(a, {})
    if kind == "gate":
        eff = c.get("abstention_unknown") or {}
        floor = c.get("answer_rate_known") or {}
        return (eff.get("delta", 0) >= 0.15 and eff.get("ci_excludes_zero")
                and floor.get("delta", 0) >= -0.05)
    eff = c.get("revision_discrimination") or {}
    return eff.get("delta", 0) >= 0.10 and eff.get("ci_excludes_zero")
def effect(a):
    m = "abstention_unknown" if kind == "gate" else "revision_discrimination"
    return (vs.get(a, {}).get(m) or {}).get("delta", 0.0)
cands = [a for a in vs if float(a) != 0.0]
passing = sorted((a for a in cands if ok(a)), key=lambda a: (abs(float(a)), -effect(a)))
if passing:
    print(passing[0]); sys.exit(0)
coherent = [a for a in cands if per[a].get("coherence_floor_ok")]
fb = max(coherent, key=effect) if coherent else None
print(fb if fb is not None else "0.0"); sys.exit(3)
PY
}

log "=== Amendment AA Stage-1 queue START (model $MODEL, image $IMAGE, seed $SEED) ==="

# ---- tier-3 preflight smoke (tiny; validates GPU path + JSON end-to-end) ----
log "SMOKE: Arm A gate/anchor (n 12+12, alphas -2,0,2, boot 200) ..."
dgpu /workspace/repo/$STEER/run_arm_a.py \
    --model "$MODEL" --direction "$DIR_GATE" --position anchor \
    --alpha-sweep=-2,0,2 --eval-pool gate --n-unknown 12 --n-known 12 \
    --gate-rows "$GATE_ROWS" --cell AA-smoke-a --seed "$SEED" --n-boot 200 \
    "${DECODE_ARGS[@]}" --device cuda --out "/workspace/repo/$RESULTS/aa_smoke_arm_a.json" >>"$LOG" 2>&1
if [ ! -f "$RESULTS/aa_smoke_arm_a.json" ]; then
  log "SMOKE ARM A FAILED (no output JSON) — queue ABORTED"; exit 1
fi
log "SMOKE: Arm B gate/early (n 8+8, boot 200) ..."
dgpu /workspace/repo/$STEER/run_arm_b.py \
    --model "$MODEL" --direction "$DIR_GATE" --signal gate --position early \
    --eval-pool gate --n-unknown 8 --n-known 8 \
    --gate-rows "$GATE_ROWS" --cell AA-smoke-b --seed "$SEED" --n-boot 200 \
    "${DECODE_ARGS[@]}" --device cuda --out "/workspace/repo/$RESULTS/aa_smoke_arm_b.json" >>"$LOG" 2>&1
if [ ! -f "$RESULTS/aa_smoke_arm_b.json" ]; then
  log "SMOKE ARM B FAILED (no output JSON) — queue ABORTED"; exit 1
fi
log "SMOKE OK (both arms) — starting cells"

# ---- AA-1: Arm A, gate, anchor, alpha sweep ----
log "AA-1: Arm A gate@anchor sweep $SWEEP (300+300) ..."
dgpu /workspace/repo/$STEER/run_arm_a.py \
    --model "$MODEL" --direction "$DIR_GATE" --position anchor \
    --alpha-sweep="$SWEEP" --eval-pool gate --n-unknown 300 --n-known 300 \
    --gate-rows "$GATE_ROWS" --cell AA-1 --seed "$SEED" \
    "${DECODE_ARGS[@]}" --device cuda --out "/workspace/repo/$RESULTS/aa1_gate_anchor.json" >>"$LOG" 2>&1
[ -f "$RESULTS/aa1_gate_anchor.json" ] && log "AA-1 DONE" || { log "AA-1 FAILED"; }

# ---- AA-3: Arm A, dial, end, alpha sweep ----
log "AA-3: Arm A dial@end sweep $SWEEP (500 answerable) ..."
dgpu /workspace/repo/$STEER/run_arm_a.py \
    --model "$MODEL" --direction "$DIR_DIAL" --position end \
    --alpha-sweep="$SWEEP" --eval-pool dial --n-answerable 500 \
    --cell AA-3 --seed "$SEED" \
    "${DECODE_ARGS[@]}" --device cuda --out "/workspace/repo/$RESULTS/aa3_dial_end.json" >>"$LOG" 2>&1
[ -f "$RESULTS/aa3_dial_end.json" ] && log "AA-3 DONE" || { log "AA-3 FAILED"; }

# ---- alpha* selection (mechanical, rule pre-stated above) ----
ASTAR_GATE=""; ASTAR_DIAL=""
if [ -f "$RESULTS/aa1_gate_anchor.json" ]; then
  ASTAR_GATE=$(select_alpha_star "$RESULTS/aa1_gate_anchor.json" gate); RC=$?
  [ $RC -eq 3 ] && log "AA-1: no qualifying alpha* — ALPHA_STAR_FALLBACK=$ASTAR_GATE (descriptive only)" \
                || log "AA-1: alpha* = $ASTAR_GATE"
fi
if [ -f "$RESULTS/aa3_dial_end.json" ]; then
  ASTAR_DIAL=$(select_alpha_star "$RESULTS/aa3_dial_end.json" dial); RC=$?
  [ $RC -eq 3 ] && log "AA-3: no qualifying alpha* — ALPHA_STAR_FALLBACK=$ASTAR_DIAL (descriptive only)" \
                || log "AA-3: alpha* = $ASTAR_DIAL"
fi

# ---- AA-2: Arm A, gate, END (off-position) at alpha* ----
if [ -n "$ASTAR_GATE" ] && [ "$ASTAR_GATE" != "0.0" ]; then
  log "AA-2: Arm A gate@end at alpha*=$ASTAR_GATE ..."
  dgpu /workspace/repo/$STEER/run_arm_a.py \
      --model "$MODEL" --direction "$DIR_GATE" --position end \
      --alpha "$ASTAR_GATE" --eval-pool gate --n-unknown 300 --n-known 300 \
      --gate-rows "$GATE_ROWS" --cell AA-2 --seed "$SEED" \
      "${DECODE_ARGS[@]}" --device cuda --out "/workspace/repo/$RESULTS/aa2_gate_end.json" >>"$LOG" 2>&1
  [ -f "$RESULTS/aa2_gate_end.json" ] && log "AA-2 DONE" || log "AA-2 FAILED"
else
  log "AA-2 SKIPPED (no usable alpha* from AA-1)"
fi

# ---- AA-4: Arm A, dial, ANCHOR (off-position) at alpha* ----
if [ -n "$ASTAR_DIAL" ] && [ "$ASTAR_DIAL" != "0.0" ]; then
  log "AA-4: Arm A dial@anchor at alpha*=$ASTAR_DIAL ..."
  dgpu /workspace/repo/$STEER/run_arm_a.py \
      --model "$MODEL" --direction "$DIR_DIAL" --position anchor \
      --alpha "$ASTAR_DIAL" --eval-pool dial --n-answerable 500 \
      --cell AA-4 --seed "$SEED" \
      "${DECODE_ARGS[@]}" --device cuda --out "/workspace/repo/$RESULTS/aa4_dial_anchor.json" >>"$LOG" 2>&1
  [ -f "$RESULTS/aa4_dial_anchor.json" ] && log "AA-4 DONE" || log "AA-4 FAILED"
else
  log "AA-4 SKIPPED (no usable alpha* from AA-3)"
fi

# ---- Arm B cells (real+placebo paired internally) ----
run_arm_b_cell() {  # $1 cell  $2 direction  $3 signal  $4 position  $5 pool-args...  $6 out
  local CELL="$1" DIR="$2" SIG="$3" POS="$4" OUT="$5"; shift 5
  log "$CELL: Arm B $SIG@$POS (real+placebo) ..."
  dgpu /workspace/repo/$STEER/run_arm_b.py \
      --model "$MODEL" --direction "$DIR" --signal "$SIG" --position "$POS" \
      --cell "$CELL" --seed "$SEED" "${DECODE_ARGS[@]}" --device cuda \
      --out "/workspace/repo/$RESULTS/$OUT" "$@" >>"$LOG" 2>&1
  [ -f "$RESULTS/$OUT" ] && log "$CELL DONE" || log "$CELL FAILED"
}
GATE_POOL=(--eval-pool gate --n-unknown 300 --n-known 300 --gate-rows "$GATE_ROWS")
DIAL_POOL=(--eval-pool dial --n-answerable 500)

run_arm_b_cell AA-5 "$DIR_GATE" gate early aa5_gate_early.json "${GATE_POOL[@]}"
run_arm_b_cell AA-6 "$DIR_GATE" gate late  aa6_gate_late.json  "${GATE_POOL[@]}"
run_arm_b_cell AA-7 "$DIR_DIAL" dial late  aa7_dial_late.json  "${DIAL_POOL[@]}"
run_arm_b_cell AA-8 "$DIR_DIAL" dial early aa8_dial_early.json "${DIAL_POOL[@]}"

log "=== Amendment AA Stage-1 queue COMPLETE ==="
