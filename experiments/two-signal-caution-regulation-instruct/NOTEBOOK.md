# two-signal-caution-regulation-instruct notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

- 2026-07-07 -- Three validity fixes (lead-directed) + re-smoke.

  1. **Clip lowered 350 -> 300.** `build_two_signal_directions.py`'s
     `MARGINAL_WRITE_CLIP` moves from 350 (in the un-validated 300-400 gray
     zone above the dark-screen's own coherent window) to 300 (the window's
     own top edge), so no row's commanded write can land outside the
     validated 150-300 window at all. Regenerated
     `analysis-committed/build_manifest.json` and
     `analysis-committed/eval_pool_both_tail.jsonl` (u_d_L34.json /
     c_hat_L34.json untouched, per instruction -- only the alpha/clip pipeline
     output changed). New per-cell distribution: confab (n=309)
     median|marginal_write|=175.1 (unchanged -- below the old clip already),
     65.7% positive, 54.7% in [150,300] (up from 29.8% at clip=350, since
     clipped rows now land AT 300 instead of past it), 0% >=400, 24.9%
     clipped. answerable_refused (n=149) median|marginal_write|=271.6
     (unchanged), 40.9% positive / 59.1% negative (release-oriented majority),
     70.5% in [150,300] (up from 26.8%), 0% >=400, 43.6% clipped. Both medians
     stay inside 150-300 and the AMENDMENT's pre-stated orientation holds
     (confab majority tighten-signed, answerable_refused majority
     release-signed).
  2. **`is_degenerate` now catches JSON-wrapped repetition.** Added
     `_extract_answer_field` (strips the JSON `"answer":` wrapper, falling
     back to the raw text unchanged when no such key is present) and
     `_has_dominant_repeated_unit` (a looser, sliding-window n-gram-dominance
     check than the base `_is_repeated_ngram`, which requires whole-sequence
     periodicity from position 0 and is defeated by a JSON preamble or a
     one-token mid-stream splice). `is_degenerate` now flags a row if EITHER
     check fires. Self-check (`python two_signal_grader.py`) proves both
     known spam shapes from the prior smoke are now flagged (the ~90x-repeated
     "True" and the 3x-repeated refusal phrase with its mid-stream "donI"
     splice) while a normal well-formed answer and a normal coherent refusal
     still pass. Re-checked against all 36 rows of the prior smoke output: 7
     rows flip degenerate False->True, all 7 independently confirmed as real
     spam (2 "True"x92 JSON rows, 1 "I don't know..."x3 splice row, 1 row that
     opens with a real sentence then collapses into "true"x~80, 2 duplicate
     arms of the same underlying rows, 1 row where the model kept generating
     "I don't know the answer" repeatedly after the JSON already closed) --
     zero false positives on any of the 29 unaffected rows. This closes the
     fake-release-flip risk the prior smoke flagged as an open finding: a
     JSON-wrapped repeated-token spam answer can no longer score
     `well_formed_correct` regardless of whether the repeated token happens to
     match a gold alias.
  3. **G2 tolerance locked at 2pt.** `gates.yaml`'s "UNRESOLVED /
     PLACEHOLDER" language on `g2_do_no_harm_confab_not_above_baseline` is
     replaced with a locked-tolerance note (lead, pre-run); the numeric
     threshold (`<= 6` rows, the count-equivalent of 2pt on the 309-confab
     cell) was already correct and did not change. `AMENDMENT.md`'s G2 gate
     line now states the 2pt tolerance explicitly instead of "a small
     pre-stated tolerance" (untracked file; the lead commits it at sign).

  **Re-smoke** (local 3090, free, same 12-row stratified subset as the prior
  smoke run, `analysis/cell_smoke.yaml` against the regenerated
  `eval_pool_both_tail.jsonl`): G0 PASSES --
  `write_ok: True`, `parity_ok: True`, `gen_stream_fired: True`,
  `offtarget_abs_max: 0.0`, no realized setpoint >=400 (max magnitude realized
  is now the new 300 clip itself, not 350). `max_write_error: 0.7550321775304383`
  (worst row: commanded -300.7182340832476, measured -299.96320190571714) --
  higher than this smoke's own `write_abs_floor` (0.5) in absolute terms but
  the gate's actual pass condition is relative (`write_rel_tol=0.05` times the
  batch's mean |commanded|, 194.66, giving an effective tolerance of 9.73), so
  `write_ok` still PASSES by a wide margin; see the lead Q&A below for the
  full explanation of why this number is ~4x the dark-screen's own
  0.02-0.12/0.0247 (this cell commands writes up to 300, dark-screen's
  comparison smoke commanded ~23, and the discrepancy tracks that ~13x
  magnitude ratio at a roughly constant relative (bf16) precision floor, not a
  hook-fidelity regression). The two rows that previously landed at the old
  350 clip and produced spam now land at 300 and are correctly flagged
  `degenerate` by the Fix-2 grader (confirmed against the regenerated smoke
  pool's same row_keys).

  Not run: the full 458-row behavioral sweep and `bin/exp sign` (both
  explicitly out of scope; scoped down further by the lead to skip a fresh
  4-bit dose-window G0 deep-dive, since the substrate is about to pivot to
  bf16 -- see the lead's next spec).

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
