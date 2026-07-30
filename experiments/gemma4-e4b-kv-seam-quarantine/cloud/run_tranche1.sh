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
# Optional resume: `run_tranche1.sh <stage_id>` skips every stage before
# <stage_id> (their volume ckpt provenance from the earlier run stands; the
# needs-restore in run_stage() consumes it regardless of which dispatch run
# produced it). No argument = full sequence with a fresh log.
START="${1:-}"
if [ -z "$START" ]; then
  : > "$LOG"
fi
skipping=0
[ -n "$START" ] && skipping=1

# Verdict-aware skip: calibrate_dose.py (b8/b9/b10) can exit nonzero to
# report a REGISTERED VERDICT (no usable mid-band dose), not a crash --
# modal_phase_b.py's run_stage() already tells that apart from a real
# failure (artifact-on-disk check) and, for a verdict exit, exits this
# dispatcher's `modal run ... --wait` call with 0 and prints a greppable
# `[modal-phaseb] VERDICT-RECORDED stage=<id> exit=<rc>` marker line. When
# that marker fires for a dose stage, its downstream smoke/full/undosed
# stages have nothing to actuate against and must be SKIPPED (recorded, not
# silently dropped) rather than dispatched against a nonexistent dose.
# Dependency map (cloud/PHASE_B_MODAL_PLAN.md stage table):
#   b8_dose_a1  -> b11_smoke_a1, b14_full_a1, b15_undosed_a1
#   b9_dose_a2  -> b12_smoke_a2
#   b10_dose_a4 -> b13_smoke_a4
# NOTE: these flags are scoped to THIS invocation only -- a resumed run
# (`run_tranche1.sh <stage_id>` starting after b8/b9/b10) will not see a
# verdict recorded by an earlier invocation and will attempt to dispatch the
# downstream stage anyway. That is a known gap (fails closed downstream via
# run_contrast.py's own fail-closed check on a missing usable dose, not
# silent), not a silent skip -- see final report.
skip_a1=0
skip_a2=0
skip_a4=0

for s in "${STAGES[@]}"; do
  if [ "$skipping" -eq 1 ]; then
    if [ "$s" = "$START" ]; then
      skipping=0
      echo "=== [$(date -u +%FT%TZ)] RESUME from $s (earlier stages skipped, ckpt provenance stands) ===" | tee -a "$LOG"
    else
      continue
    fi
  fi

  case "$s" in
    b11_smoke_a1|b14_full_a1|b15_undosed_a1)
      if [ "$skip_a1" -eq 1 ]; then
        echo "=== SKIP $s (A1 dose-viability NOT-RUN) ===" | tee -a "$LOG"
        continue
      fi
      ;;
    b12_smoke_a2)
      if [ "$skip_a2" -eq 1 ]; then
        echo "=== SKIP $s (A2 dose-viability NOT-RUN) ===" | tee -a "$LOG"
        continue
      fi
      ;;
    b13_smoke_a4)
      if [ "$skip_a4" -eq 1 ]; then
        echo "=== SKIP $s (A4 dose-viability NOT-RUN) ===" | tee -a "$LOG"
        continue
      fi
      ;;
  esac

  echo "=== [$(date -u +%FT%TZ)] dispatch $s ===" | tee -a "$LOG"
  # Capture this stage's own output separately (not appended straight to
  # $LOG the way the pre-verdict-aware version did) so the VERDICT-RECORDED
  # grep below is scoped to THIS stage's dispatch only -- grepping the
  # accumulated $LOG would risk matching a marker left by an EARLIER
  # dispatch of the same stage id (e.g. a prior halted/redispatched run) as
  # if it were current. The captured output is still appended to $LOG
  # afterward so the on-disk log is unchanged in content and order.
  STAGE_LOG="$(mktemp)"
  modal run --detach cloud/modal_phase_b.py --stage "$s" --wait >"$STAGE_LOG" 2>&1
  rc=$?
  cat "$STAGE_LOG" >> "$LOG"
  echo "=== [$(date -u +%FT%TZ)] $s exit=$rc ===" | tee -a "$LOG"

  if grep -q "VERDICT-RECORDED stage=${s} exit=" "$STAGE_LOG"; then
    case "$s" in
      b8_dose_a1) skip_a1=1 ;;
      b9_dose_a2) skip_a2=1 ;;
      b10_dose_a4) skip_a4=1 ;;
    esac
  fi
  rm -f "$STAGE_LOG"

  if [ "$rc" -ne 0 ]; then
    echo "TRANCHE1 HALTED at $s (exit $rc); later stages NOT dispatched." | tee -a "$LOG"
    exit "$rc"
  fi
done
echo "TRANCHE1 COMPLETE: all ${#STAGES[@]} stages exited 0." | tee -a "$LOG"
