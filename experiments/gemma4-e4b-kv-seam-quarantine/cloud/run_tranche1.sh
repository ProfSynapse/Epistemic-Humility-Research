#!/usr/bin/env bash
# Tranche 1 dispatcher for Phase B on Modal (B0..B15, nothing blocked_on_c1).
# User-approved launch 2026-07-30 ("confirm modal"); governed lane revision and
# launch record in AMENDMENT.md (commit c21a0439). Runs each stage via
# `modal run --detach ... --wait`: --detach so the spawned run_stage call
# survives a dropped client/network blip, --wait so main() blocks on the
# call's result and this script sees a real nonzero exit when a stage fails
# (a failed gate or crashed stage halts the tranche, it never skips ahead).
# Log: cloud/tranche1_dispatch.log
#
# FIXED 2026-07-30 (incident, $0 damage): the first version of this script
# ran `modal run cloud/modal_phase_b.py --stage "$s"` with NEITHER flag.
# modal_phase_b.py's local_entrypoint only calls run_stage.spawn(stage) and
# returns -- without --wait it returns immediately, and without --detach a
# plain `modal run` tears the ephemeral App down the instant the entrypoint
# returns, killing the just-spawned call before it runs anything. All 18
# stages "completed" in 26 seconds; `modal app list` showed every one of
# those apps stopped with Tasks: 0 and the volume unchanged beyond
# private-inputs/. Nothing ran, $0 spent, redispatch after this fix is safe
# (resume-skip logic in run_stage() makes a re-dispatch of an
# already-completed stage cheap regardless).
set -u
cd "$(dirname "$0")/.."
export EHR_LAUNCH_OK=gemma4-e4b-kv-seam-quarantine

STAGES=(
  b0_g0kv_preflight
  b1_extract_off_midband
  b2_extract_off_seampair
  b3_alin_part2
  b4_directions_a1
  b5_directions_a2
  b6_directions_a4
  b7_gatefit_a1
  b7_gatefit_a2
  b7_gatefit_a4
  b8_dose_a1
  b9_dose_a2
  b10_dose_a4
  b11_smoke_a1
  b12_smoke_a2
  b13_smoke_a4
  b14_full_a1
  b15_undosed_a1
)

LOG=cloud/tranche1_dispatch.log
: > "$LOG"

for s in "${STAGES[@]}"; do
  echo "=== [$(date -u +%FT%TZ)] dispatch $s ===" | tee -a "$LOG"
  modal run --detach cloud/modal_phase_b.py --stage "$s" --wait >>"$LOG" 2>&1
  rc=$?
  echo "=== [$(date -u +%FT%TZ)] $s exit=$rc ===" | tee -a "$LOG"
  if [ "$rc" -ne 0 ]; then
    echo "TRANCHE1 HALTED at $s (exit $rc); later stages NOT dispatched." | tee -a "$LOG"
    exit "$rc"
  fi
done
echo "TRANCHE1 COMPLETE: all ${#STAGES[@]} stages exited 0." | tee -a "$LOG"
