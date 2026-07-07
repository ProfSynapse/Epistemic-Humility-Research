# two-signal-caution-regulation-instruct notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

- 2026-07-07 -- BF16 DOSE-UNITS BUG FIX (red-team-caught) + readback-logged
  dose re-sweep + ALPHA/CLIP recalibration + re-smoke. Supersedes the dose
  numbers in the entry immediately below (that entry's ALPHA=2.0/CLIP=40.0
  build is now known to be ~20x under-dosed; its other content -- the
  extraction, direction refits, containment migration -- is unaffected and
  NOT redone here). Same pass also carries two other red-team-flagged minor
  fixes, unrelated to the dose bug: (a) `materialize_eval_pool.py` now
  HARD-FAILS (nonzero exit) if any answerable_refused row has empty aliases
  after the local AH A0 join, rather than only warning -- a missing/broken
  canonical pool could otherwise silently produce a clean-looking but
  vacuous release-tail null; (b) `AMENDMENT.md`'s Design section now
  discloses that the same 309 confab rows are in-sample to BOTH the
  pos_ctrl/neg_ctrl direction fit and the G1-tighten eval tail -- not an
  outcome leak (grading is independent of the fit labels, the permuted
  placebo destroys the fit's own row-gain pairing, and the tighten claim
  already rests on the dark-screen's held-out positive control, not this
  in-sample fit) but disclosed rather than left implicit.

  **The bug.** The tuner's erase_write law writes `gain*sigma` as the
  realized post-write projection onto the direction, exactly
  (`synaptic-tuner/MechInterp/intervention/hooks.py` docstring lines 7-12).
  `analysis/dose_escalation_bf16_ambient_relative.py` constructs the REAL
  tuner `InterventionHook` with this experiment's own `sigma=21.36` and
  passes `strength = k * ambient_mean` as the GAIN argument -- so the
  sweep's own printed "strength" column (which the entry below, and this
  file's superseded bf16-pivot text, read as if it were the realized write)
  was actually a GAIN requiring a further `*sigma_c` (~21x) to become the
  real setpoint. The prior ALPHA=2.0/MARGINAL_WRITE_CLIP=40.0 build
  calibrated directly against those un-multiplied numbers, so the real run
  wrote setpoints ~20x smaller than the confirmed coherent window. This is
  exactly the confirming signature behind the prior smoke's 0/12 tighten
  flips: the near-proven tighten half (dark-screen's own positive control:
  79/80 confab->refuse flips) produced ZERO flips at smoke scale because the
  dose was ~20x too small to ever leave the "inert" zone.

  **The fix.** Extended `dose_escalation_bf16_ambient_relative.py` to record
  `hook.last_readback` (the GPU-measured, POST-write projection -- the
  ground-truth unit, immune to any gain/setpoint confusion) into `per_k` and
  the row summary, then reran it unchanged otherwise (same c_hat_L34.json,
  same 24-row half-confab/half-answerable_refused draw, same K_LIST, local
  3090). 24/24 rows processed, 21/24 usable (3 rows never registered a clean
  move within K_LIST -- ambient projection too small on those particular
  rows to reach a coherent move by k=15; not investigated further, same
  per-row-heterogeneity character as the entry below). Results:
  `analysis/dose_ladder_bf16_readback_results.jsonl`.

  Readback-unit coherent window (n=21 usable):
  - first-coherent-move |readback|: median=531.9, p25=452.0, p75=587.9
    (confab median=456.0, n=9; answerable_refused median=546.0, n=12).
  - first-garbage-collapse |readback|: median=952.0, p25=743.8, p90=1112.0
    (confab median=808.0, n=9 -- the LOWER of the two cells; answerable_refused
    median=997.9, n=12).
  - Order-of-hundreds, consistent with the dark-screen's own bf16
    un-orthogonalized pos_ctrl_L34 prior (coherent~100, collapse>=500) scaled
    by this direction's own sigma_c, and with the hand-derived 530/843
    estimate from `strength * sigma_c` arithmetic on the entry-below sweep's
    own numbers.
  - Fragility finding (not used to set the clip, same convention as the
    entry below's own low-collapse-outlier discussion): row
    `ahx::kuq_ku_unknown_x::000518` shows a NON-MONOTONIC garbage flag --
    garbage at readback -374 (k=7), clears (non-garbage) at -588 (k=11) and
    -696 (k=13), then re-collapses at -800 (k=15). This reads as a
    heuristic-detector glitch (the token-collapse/phrase-loop regex checks
    are not guaranteed monotonic in dose), not a real early collapse floor.

  **Recalibration.** `build_two_signal_directions.py`: `ALPHA` 2.0 -> 40.0,
  `MARGINAL_WRITE_CLIP` 40.0 -> 750.0 (below BOTH cells' median collapse
  floors, margin ~58 below confab's own 808 -- the tighter constraint;
  ~248 below answerable_refused's 998). Also fixed the report function's
  own `frac_abs_in_bf16_window_ge_15_le_40` / `frac_abs_ge_45` fields, which
  were hardcoded to the OLD, wrong-unit window -- renamed to
  `frac_abs_in_bf16_readback_window_ge_452_le_808` / `frac_abs_ge_808` so the
  committed `build_manifest.json` does not silently re-report the bug's own
  numbers as if they were still meaningful. Regenerated
  `analysis-committed/{build_manifest.json,eval_pool_manifest.jsonl}` and
  re-ran `materialize_eval_pool.py` (458/458 rows, 0 missing question, 0
  missing alias on answerable_refused). New per-cell distribution: confab
  (n=309) abs_median|marginal_write|=505.9 (23.3% clipped, 0% reach 808);
  answerable_refused (n=149) abs_median|marginal_write|=622.6 (43.6% clipped,
  0% reach 808); overall abs_median=541.2, 57.0% of the pool in [452,808].
  Both medians land inside the confirmed window and preserve the prior
  build's orientation and clip-fraction character (majority of rows below
  the clip in both cells).

  **Re-smoke** (local 3090, free, SAME 12-row stratified subset as both
  prior smokes -- `analysis/eval_pool_smoke12.jsonl` regenerated from the
  recalibrated pool by row_key, not reselected, so this is a clean
  before/after comparison; `analysis/cell_smoke.yaml` regenerated from the
  updated `cell.yaml` with `surface.rows_path`/`execution.output_path`/
  `smoke.n_rows` repointed, same convention as all three prior smokes). G0
  PASSES: `write_ok: True`, `parity_ok: True`, `gen_stream_fired: True`,
  `offtarget_abs_max: 0.0`, `max_write_error: 2.157` (well within the
  effective relative tolerance: `write_rel_tol=0.05` times the coupled arm's
  own mean |commanded| of 450.9, i.e. an envelope of 22.5). Realized
  |marginal_write| on the smoke's 12 coupled-arm rows: min=6.7, median=499.2,
  max=750.0 (3 rows pinned exactly at the +/-750 clip, all on the
  answerable_refused cell) -- comfortably inside the readback-confirmed
  window at the aggregate level.

  **THE KEY CHECK (falsifier-relevant): tighten-flip count at an in-window
  dose.** 1/6 confab-cell smoke rows flip baseline-confabulated ->
  coupled-coherent-refuse (`ah::selfaware_unanswerable::002663`, mw=229.2 --
  note this flip fired at a BELOW-median dose, not the highest; several
  higher-dose confab rows, up to mw=750.0, did NOT flip). This is NONZERO,
  so the step-3 stop-gate ("if the re-smoke still shows ~0 tighten flips at
  an in-window dose, STOP") does NOT fire -- the dose is live. 1/6 at n=6 is
  a small-sample proof-of-life only, not a gate result (G1-tighten reads the
  full 309-row confab cell with a bootstrap CI, not this smoke). Release-flip
  count: 0/6 (`well_formed_correct`) -- expected at this scale, since the
  release half is the genuinely open, non-near-proven claim; not smoke-gate
  relevant either. Degenerate coupled-arm rows: 4/12, concentrated on the
  answerable_refused cell at/near the +/-750 clip (2 of the 3 clip-pinned
  rows -- `ahx::triviaqa::005236`, `ahx::triviaqa::004138` -- are degenerate
  repetition spam; the third clip-pinned row, `ahx::kuq_ku_unknown_x::001029`,
  a confab row at mw=750.0, is NOT degenerate). Open finding, not gate
  relevant at smoke scale: the clip ceiling (750) is close enough to some
  individual rows' own (heterogeneous, per-row) collapse floor that
  clip-pinned rows show a real, elevated collapse rate -- the same
  per-row-fragility character flagged throughout this experiment's dose
  work, now visible in actual generations rather than only the dose-sweep's
  probe rows.

  Not run: the full 458-row behavioral sweep and `bin/exp sign`; both remain
  out of scope for this build task, left for the lead to schedule.

- 2026-07-07 -- BF16 SUBSTRATE PIVOT: full refit + dose recalibration +
  eval-pool containment migration + re-smoke.

  Moved the entire experiment off `unsloth/Qwen3-4B-bnb-4bit` (4-bit) onto
  `unsloth/Qwen3-4B` (full bf16, `load_in_4bit=False`, `dtype=torch.bfloat16`).
  Design (prediction/falsifier/gates prose) UNCHANGED; only the substrate,
  the fitted directions, and the dose calibration changed.

  1. **Extraction (`extract_l34_anchor.py`, rewritten).** The prior 4-bit
     build only filled the two "answerable-side" roles it lacked a cache for
     (known_correct_answered=89, answerable_refused=149) and read the
     unanswerable side (unknown_refused=1029, confab=309) from the AK
     Stage-1 tensor cache -- a 4-bit capture, not reusable under bf16. This
     rewrite extracts ALL FOUR roles fresh (1,576 rows total) via
     `unsloth.FastLanguageModel.from_pretrained(unsloth/Qwen3-4B,
     dtype=torch.bfloat16, load_in_4bit=False)`, same render/anchor
     convention as before (`render_probe_prompt` + baseline system prompt,
     anchor at prompt_len-1, hs[34]). Local 3090, 77s total. Counts verified:
     89/1029/309/149, matching the original AK Stage-1 / AH A0 manifests
     exactly.
  2. **Direction refits (`build_two_signal_directions.py`, rewritten).** u_d
     refit as before (mean-diff, now bf16-only H). pos_ctrl (caution_dir) and
     neg_ctrl (u_p) are NO LONGER copied from the dark-actuator-screen's
     4-bit fit -- both refit fresh on this experiment's own bf16 AK Stage-1
     extraction (1,338 rows), using the dark-screen's own
     `_raw_refuse_and_propensity` method VERBATIM (mass-mean refuse_dir;
     StandardScaler + `LogisticRegression(solver="saga", tol=1e-3,
     max_iter=5000, C=1.0)` propensity direction), read in full from
     `/home/profsynapse/code/ehr-worktrees/dark-screen/experiments/
     dark-actuator-screen/build_directions.py:149-165` before writing this.
     c_hat = 2-D Gram-Schmidt orthogonalization of caution_dir against {u_d,
     u_p}, unchanged method. Fit provenances (all `substrate: "bf16"`,
     `base_model: "unsloth/Qwen3-4B"`):
       - u_d_L34.json: n_known_correct_answered=89, n_unknown_refused=1029.
       - source_directions/pos_ctrl_L34.json,
         source_directions/neg_ctrl_L34.json: n_confab=309, n_refuse=1029,
         same logreg hyperparams as the dark-screen.
       - c_hat_L34.json: cos(caution_dir, c_hat)=0.872, cos(u_d,u_p)=0.093,
         sigma_c=21.36 over the 458-row eval pool (was 36.18 under 4-bit).
  3. **Dose calibration.** Seeded from the dark-screen's own bf16
     characterization of ITS (un-orthogonalized) pos_ctrl_L34: coherent
     window ~100, ambient ~19-27, collapse >=500
     (`/tmp/.../scratchpad/dose_ladder_bf16_results.json`, a 3-prompt fixed
     ladder against `Qwen/Qwen3-4B`). A naive linear rescale from the 4-bit
     ALPHA=10.0 gave an initial ALPHA=4.0 guess -- checked against a FRESH
     24-row ambient-relative dose escalation
     (`analysis/dose_escalation_bf16_ambient_relative.py`, mirroring the
     dark-screen's own `dose_escalation_ambient_relative.py` method exactly:
     k in {3,5,7,9,11,13,15} x each row's own natural ambient projection,
     half confab / half answerable_refused, on THIS experiment's own refit
     c_hat_L34 direction). First attempt used unsloth's
     `FastLanguageModel.for_inference` and produced ZERO ambient signal on
     every row (0/24 usable) -- unsloth's fused inference `generate()` path
     does not reliably fire the per-decode-step forward hooks this
     diagnostic (and the tuner's own intervention machinery) depend on.
     Switched to plain `AutoModelForCausalLM.from_pretrained(...,
     dtype=torch.bfloat16)` (matching BOTH the dark-screen's own diagnostic
     scripts AND `synaptic-tuner/MechInterp/cli.py`'s real model-loading
     path -- confirmed by reading that file: the tuner never uses unsloth for
     steer cells), which fixed it: 21/24 rows produced a usable coherent
     window. Result: this experiment's c_hat_L34 (post-orthogonalization,
     cos 0.872 with the un-orthogonalized caution_dir) has a substantially
     NARROWER and LOWER window than the seed prior -- median
     first-coherent-move strength ~20-27 (k_move median 3x ambient), median
     first-garbage-collapse strength ~40-43 (k_collapse median 7x ambient),
     with real per-row heterogeneity (one outlier row collapsed as early as
     strength ~17.5; two rows never registered a clean "move" before
     collapsing). ALPHA retuned to 2.0 (from the 4.0 naive-rescale guess) and
     MARGINAL_WRITE_CLIP to 40.0 (from an initial 150.0 guess), landing this
     eval pool's abs_median marginal write at 25.3 (confab, n=309, 68.6% in
     [15,40]) / 31.1 (answerable_refused, n=149, 74.5% in [15,40]), 0% >=45,
     comfortably inside the confirmed coherent zone and below the confirmed
     median collapse floor. Raw results:
     `analysis/dose_ladder_bf16_ambient_relative_results.jsonl` (gitignored
     scratch, not committed -- reproducible by rerunning the script against
     the committed c_hat_L34.json).
  4. **Eval-pool containment migration.** `analysis-committed/
     eval_pool_both_tail.jsonl` used to commit `question` and `aliases` text
     directly (this repo is PUBLIC; forbidden per `.skills/pr-workflow/
     SKILL.md`). Removed from git (`git rm --cached`). Replaced with
     `analysis-committed/eval_pool_manifest.jsonl` (458 rows, ID + derived
     columns only -- row_key/safe_key/cell/gold_class/category_canon/source/
     proj_d/proj_p/proj_c/z_d/z_p/g_two_signal/marginal_write/
     g_two_signal_unclipped/marginal_write_unclipped/clipped -- no question,
     no aliases). New `materialize_eval_pool.py` joins that manifest against
     question text fetched via `hf_hub_download(repo_id=
     "professorsynapse/eh-al-prep-staging",
     filename="pools/a0_pool_v21_questions.jsonl", repo_type="dataset")`
     (verified to cover all 458 row_keys with text byte-identical to the
     local AH A0 pool) and aliases read from the local canonical-checkout AH
     A0 pool (itself sourced from this repo's own already-committed
     `datasets/kuq/` / `datasets/selfaware/`), writing the full local pool to
     the gitignored `analysis/eval_pool_both_tail.jsonl` that `cell.yaml`'s
     `surface.rows_path` now points at. Mirrors the
     `j-space-localization-qwen3-4b` containment migration exactly (commit
     `88c98cdc`). `git grep` confirms no question/answer text remains tracked
     anywhere in this experiment's directory or the shared render module.
  5. **`ah_a0_raw_base_render.py`** (shared render, only consumer is this
     experiment): `_MODEL_NAME` updated to `unsloth/Qwen3-4B`; docstring
     updated for the materialized-pool path. Tokenizer vocab/chat template is
     unchanged between the 4-bit and bf16 repo ids.
  6. **`cell.yaml`**: model -> `unsloth/Qwen3-4B` (bf16, no 4-bit); dose block
     updated to ALPHA=2.0/clip=40; `surface.rows_path` repointed at the
     gitignored materialized pool; smoke commentary sigma updated to 21.36.
     Loads clean via `MechInterp.config.load_steer_config` (CPU check).

  **Re-smoke** (local 3090, free, 12-row stratified subset --
  `analysis/eval_pool_smoke12.jsonl`, 6 confab + 6 answerable_refused --
  `analysis/cell_smoke.yaml`, gitignored ephemeral config copied from
  `cell.yaml` with `surface.rows_path`/`execution.output_path` repointed at
  the smoke-scale files, same convention as the two prior 4-bit smokes). Run
  from the worktree root (NOT `cd synaptic-tuner`, per the dark-screen's own
  documented path-resolution gotcha: `cell.yaml` paths are repo-root-relative
  and a plain `open()` resolves them against the process CWD). G0 PASSES:
  `write_ok: True`, `parity_ok: True`, `gen_stream_fired: True`,
  `offtarget_abs_max: 0.0`, `max_write_error: 0.1353` (well within
  `write_abs_floor=0.5`). Realized commanded writes on the smoke's 12
  coupled-arm rows: min=0.31, p25=8.85, median=24.95, p75=38.11, max=40.00
  (2 rows pinned exactly at the +/-40 clip); 66.7% of the 12 smoke rows in
  [15,40]. 0/12 coupled-arm rows graded `degenerate` (0% collapse). This is
  G0 instrument-validity only -- no G1/G2 behavioral claim; the 12-row smoke
  did not flip any confab row to refusal (expected at this scale/dose, not a
  gate result).

  Not run: the full 458-row behavioral sweep and `bin/exp sign`, both
  explicitly out of scope for this build task; left for the lead to schedule.

- 2026-07-07 -- Three validity fixes (lead-directed) + re-smoke. **4-BIT
  ERA -- superseded by the bf16 pivot above; kept for history.**

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
