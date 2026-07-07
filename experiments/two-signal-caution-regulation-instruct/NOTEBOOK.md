# two-signal-caution-regulation-instruct notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

- 2026-07-07 -- Dose-fix retune (ALPHA 5.0 -> 10.0, added hard
  marginal_write clip at +/-350) + SMOKE-only proof. Initial offline build
  (ALPHA=10.0 pending, no clip) put only 23.8% of confab rows and 25% of
  answerable_refused rows inside the pre-validated 150-300 coherent window,
  with tail excursions past the dark-screen's >=400 collapse floor (min
  observed -553.7 on answerable_refused, 10.7% of that cell already
  >=400-in-magnitude). Retuned to ALPHA=10.0 and added
  `MARGINAL_WRITE_CLIP=350.0` (a collapse-safety margin strictly below the
  dark-screen's >=400 floor, applied to the ACTUAL write, not just the
  reported number) in `build_two_signal_directions.py`. Regenerated
  `analysis-committed/build_manifest.json` and
  `analysis-committed/eval_pool_both_tail.jsonl`. Per-cell result (see
  build_manifest.json for exact numbers): confab (n=309) median|marginal_write|
  = 175.1, 65.7% positive (tighten-oriented), 18.4% pinned at the clip; 
  answerable_refused (n=149) median|marginal_write| = 271.6, 59.1% negative
  (release-oriented), 36.9% pinned at the clip. Both medians land inside
  150-300; both cells keep a majority of rows below the clip (selectivity not
  saturated) and preserve the AMENDMENT's pre-stated orientation. The
  STEP-2-style saturation tension (alpha so high most rows pin at the clip)
  did NOT fire; no fallback base-shift design was needed.

  SMOKE (local 3090, 12-row stratified subset x 3 arms = 36 rows,
  `analysis/cell_smoke.yaml`, gitignored ephemeral config pointed at the same
  committed `analysis-committed/eval_pool_both_tail.jsonl` rows): G0's
  mechanical checks pass -- `write_ok: True`, `parity_ok: True`,
  `max_write_error: 0.4339` (within the 0.5 write_abs_floor),
  `offtarget_abs_max: 0.0`, `gen_stream_fired: True`. No smoke setpoint
  reached the >=400 void threshold (max magnitude realized was the 350 clip
  itself). Coupled-arm output changed vs baseline on 8/12 smoke rows (all 4
  unchanged rows were the near-zero-dose picks, as expected for a
  proportional controller). Both cells produced at least one clean in-window
  (150-300 |marginal_write|, unclipped) example with the correct-orientation
  behavioral flip: confab row `ahx::kuq_ku_unknown_x::002821` (mw=+175.1)
  answered -> coherent refuse; answerable_refused rows
  `ah::selfaware_answerable::004462` (mw=-271.6) and
  `ah::kuq_ku_known::004792` (mw=-271.1) both refused -> answered (correct=False
  on both, so neither counted as well_formed_correct -- a real content miss,
  not a coherence problem).

  Open finding, NOT gate-relevant but worth flagging: the two smoke rows that
  landed exactly at the +/-350 clip (one per cell) produced repetitive,
  low-information output (`answerable_refused` clip rows both produced
  ~90-token literal repeats of the single word "True"; one `confab` clip row
  produced a 3x-repeated refusal phrase) that reads as collapse-adjacent, yet
  `two_signal_grader.is_degenerate` did NOT flag either as degenerate. Root
  cause: `is_degenerate`'s ported n-gram check requires the WHOLE token
  sequence to be one repeated unit from position 0; this cell's answers are
  JSON-wrapped (e.g. `{"answer": "True True True...`), so the JSON preamble
  token(s) desynchronize the check and it never fires, even when the bulk of
  the text past the preamble is pure repetition. This does not change any
  G1/G2 pass/fail as specified (both affected rows already have `correct:
  False`, so `well_formed_correct` is False regardless of the degenerate
  flag), but it is a real coherence-check gap worth the lead's attention
  before relying on the raw `degenerate` field for anything beyond this
  cell's pre-registered gates. Not fixed here (would be a grader-algorithm
  change, out of scope for a SMOKE-only build task); reported as a finding.

  Added `score_gates_by_cell.py` (build-time-only tool, no GPU): adjudicates
  gates.yaml's three G1/G2 gates by importing
  `MechInterp.stats.gates.kill_diff_vs_control` directly and doing the
  cell-filtering the generic tuner CLI cannot do (see gates.yaml's
  "DISCOVERED LIMITATION" note). Not run against a full sweep (none exists
  yet); a smoke-scale sanity run (n=6/cell) confirms the script executes and
  the G2 do-no-harm gate's sign is already in the right direction at that
  tiny scale.

  Not run: the full 458-row behavioral sweep, and `bin/exp sign`. Both
  explicitly out of scope for this build task; left for the lead to schedule
  and for the user to separately approve.
