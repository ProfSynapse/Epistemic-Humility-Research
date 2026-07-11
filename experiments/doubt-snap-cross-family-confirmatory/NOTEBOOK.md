# doubt-snap-cross-family-confirmatory notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

- 2026-07-11 (llama G0 characterization + grid recalibration extension +
  mistral stop, user-approved): llama32_3b_instruct stopped at the registered
  FIT dose-viability rule (exit 4, zero qualifying doses), the same signature
  as the 2026-07-08 Qwen3.5 cells. A committed-artifact diagnostic showed this
  is overdose collapse on the unrecalibrated default grid, not plumbing and
  not family-level insensitivity: dose correctly parameterized the write
  (per-arm strengths 47.79 to 119.48, completions 94 to 99.9 percent pairwise
  identical across doses, not 100 percent), but the default 100-250 grid
  realizes 48.7 to 120.4 sigma on llama's sigma_c of 2.092, beyond the 38
  sigma that collapsed Qwen3.5-4B, and 100 percent of fired FIT rows were
  degenerate at every dose. mistral7b_instruct_v03 was stopped mid dose sweep
  before wasting spend on a predetermined null: its sigma_c of 0.939 realizes
  106.7 to 266.5 sigma on the default grid. Baseline, grading, capture, and
  direction-fit artifacts for both cells are volume-backed and resume-safe.
  Per the user-approved pre-outcome recalibration extension in AMENDMENT.md,
  cell.yaml gains per-cell grids mapping Qwen3.5-4B's working z-ladder onto
  each cell's own mu_c/sigma_c (llama 11-60, mistral 6-27); the cell.yaml pin
  hash is refreshed accordingly. Both cells relaunch detached at batch-1 to
  re-enter at the dose sweep. Durable lesson queued for the skill: a per-cell
  dose-grid fix does NOT propagate to sibling cells; before any steering cell
  launches, assert the realized z-range of its grid against its own
  build_manifest sigma_c.

- 2026-07-11 (2-cell probe relaunch authorized): user approved in-conversation
  a two-cell fleet probe under a $75 operational cap: two-row harness smoke on
  llama32_3b_instruct first (smoke_only lane of run_one_cell), then detached
  batch-1 cell launches for llama32_3b_instruct and mistral7b_instruct_v03 at
  repo commit c560ae98, A10G default lane. Both Qwen3.5 FIT-dose-null live
  namespaces were archived to _archive/<cell>_fitdose_null_20260708_2100 per
  the runbook before relaunch. Hub metadata access verified at both pinned
  revisions. Batch size stays 1 per the registered semantic-parity evidence;
  no scientific parameter changes.

- 2026-07-11 (Qwen3.5 FIT-dose nulls committed to public artifacts): Pulled the
  nine `analysis-committed` aggregate files for both `qwen35_4b` and
  `qwen35_9b` from the Modal volume `eh-doubt-snap-cross-family`
  (`doubt-snap-cross-family-r1/_live/<cell>/analysis-committed/`) into
  `analysis-committed/qwen35_4b/` and `analysis-committed/qwen35_9b/` under
  version control (`modal_status.json`, `dose_fit.json`, `gate_fit.json`,
  `g0_prep_summary.json`, `split_manifest.json`, `build_manifest.json`,
  `u_d.json`, `c_hat.json`, `random_direction.json`). Every file was inspected
  by key, not filename, before staging: `split_manifest.json` rows carry only
  `category_canon`/`role`/`row_key` (ID-only, e.g. `kuq_unknowns_all:0`)/
  `source`/`split`; the direction files carry only fitted vectors and
  provenance metadata. No prompt text, answer aliases, or generation text is
  present in any pulled file.

  `modal_status.json` is identical in shape on both cells: `status: failed`,
  `failure_stage: fit_dose_selection`, `dose_select_exit_code: 4`,
  `reason: no_registered_candidate_dose_met_fit_selection_criteria`. Per the
  registered taxonomy this is a pre-outcome FIT-dose-selection stop, not a
  G1/G2/G3 held-out fail and not a G0 harness/access failure: both cells
  cleared every other `g0_eligibility_and_instrument_validity` check
  (`held_out_power` true with confab/known-correct held-out counts
  1332/360 for 4B and 1384/428 for 9B, both above the 150/250 floor;
  `gate_auc_on_fit` 0.9960 (4B) / 0.9992 (9B), both >= 0.90;
  `directions_reproducible` true; `generation_terminates` 0.995 (4B) / 0.987
  (9B), both >= 0.90; `batched_parity_smoke` passed with zero mismatches on 8
  rows) and failed only `dose_viable_on_fit`. No held-out outcome was scored
  on either cell. No gate is reinterpreted and no threshold changed; this
  entry commits to version control, unchanged, the null already characterized
  in the 2026-07-09 and 2026-07-10 entries below.

  Registered candidate doses tried (per-cell recalibrated grid, `cell.yaml`
  `dose_selection.per_cell_candidate_realized_projection_targets`): 4B
  `{10, 20, 30, 40, 50, 60, 75}`, 9B `{60, 80, 100, 120, 140}`. Selection rule
  (`gates.yaml` `dose_viable_on_fit` / `cell.yaml` `snap.dose_selection.rule`):
  lowest dose with FIT gated `confab_tighten >= 0.60` AND FIT
  `known_correct_cost_control <= 0.10`. From the committed `dose_fit.json`
  reports: 4B `confab_tighten` rate by dose is 2.8% (10), 9.0% (20), 17.2%
  (30), 32.6% (40, the peak), 10.8% (50), 0.0% (60), 0.0% (75), with
  `known_correct_cost_control` at or below 3.3% throughout -- the cost-control
  criterion is met at every dose but `confab_tighten` never reaches the 0.60
  floor. 9B `confab_tighten` rate rises monotonically 0.43% (60), 0.98% (80),
  1.95% (100), 3.47% (120), 5.75% (140), with `known_correct_cost_control`
  2.10-2.45% throughout -- again cost control is fine but tighten never
  approaches 0.60. `selected_dose: null` on both. Both cells are recorded as
  G0 dose-viability fails and are ineligible-before-held-out for the panel
  denominator.

  Note for resolve time: the `qwen35-4b-midband-doubt-snap` ladder currently
  running locally in the separate worktree
  `/home/profsynapse/code/ehr-worktrees/qwen35-midband/`
  (`experiments/qwen35-4b-midband-doubt-snap/run_dose_ladder.py full`,
  decided in session-0044 checkpoint `e45f19a5` "Qwen3.5 decomposition verdict
  + 4B-local mid-band decision") is an exploratory follow-up outside this
  confirmatory surface's registered instrument. Its results are never pooled
  with this amendment's G0/G1/G2/G3 outcomes or with the cross-family headline
  gate in `gates.yaml`.

- 2026-07-10 (anchor audit): Read-only audit of anchor placement on both
  Qwen3.5 cells, the last unchecked harness surface behind the no-window
  nulls. Verdict: CONFIRMS, no confound. (1) Structural: under
  generation_mode gen_stream the write span never consults the prompt
  anchor at all -- the hook is inactive during prefill and writes every
  decode step (window_start=0, seq_len=1 per step; tuner
  MechInterp/intervention/hooks.py gen_stream branch, lead-verified) -- so
  a chat-template shift cannot move the write span. (2) Empirical: capture
  anchor invariant positions.anchor == len(token_ids)-1 holds on all
  3000/3114 rows; a deterministic 45-row-per-cell re-render with the real
  pinned tokenizers reproduced recorded token_ids byte-identically 90/90;
  all sampled prompts end in the same empty-think template tail as Qwen3
  (no leaked thinking, no multimodal wrapper tokens, no off-by-N vs the
  Qwen3 exploratory convention); prompt_len 127-163, no outliers. Gate AUC
  0.996/0.999 and smoke readback (write_ok, offtarget 0.0) corroborate.
  Hygiene gap noted, not a harm finding: the cross-family render.py lacks
  the exploratory pipeline's assert_no_think_scaffolding self-check and
  falls back silently across chat-template kwarg variants; add the loud
  check before the remaining panel cells launch.

- 2026-07-10: Both recalibrated Qwen3.5 FIT dose sweeps completed and committed
  `selected_dose: null`. These are now well-characterized G0 dose-viability
  fails, not grid artifacts. 4B (grid 10-75, n=887 confab / 240 known per arm):
  coherent actuation rises 2.8% -> 9.0% -> 17.3% -> 32.6% across doses 10-40,
  then JSON corruption sets in (confab well-formedness 90% -> 55% -> 3% across
  40/50/60) and tighten falls to 10.8% / 0% / 0% at 50/60/75; peak coherent
  tighten ~33% at dose 40, far below the registered 60% bar, known-cost <=3.3%
  throughout. 9B (grid 60-140, n=921 / 286): tighten rises 0.4% -> 5.8%
  monotonically across 60-140; with the prior run's points (5.1% at 150, 0%
  with well-formedness collapse at 200/250) the curve peaks ~6% near 140-150
  before the cliff. Neither substrate has a coherent operating window
  anywhere near the registered thresholds. Per the recalibration note's
  pre-commitment, both cells fail G0 dose viability and are recorded as such
  with no further grid changes. Family-level reading for resolve time: the
  doubt-gated caution snap does not transfer to Qwen3.5 at the registered
  thresholds (max coherent tighten ~33% at 4B, ~6% at 9B, vs 73.5% held-out
  on Qwen3-4B); both cells are ineligible-before-held-out for the panel
  denominator (G0 fail, not a held-out G1/G2/G3 fail). Sweep-side operational
  note: collapsed arms are the slowest because shattered generations never
  emit EOS and burn the full 200-token cap.

- 2026-07-09: Registered the pre-outcome Qwen3.5 dose-grid recalibration after
  both cells failed FIT dose viability with zero qualifying doses. The audit of
  committed FIT artifacts (gate_fit, dose_fit, rows_out_dose_fit, readback)
  established overdose collapse, not family nulls: 4B fits sigma_c = 2.80
  (about 4.7x below the Qwen3-4B reference), so dose 100 is already a ~38-sigma
  write and all 854 fired FIT confabs degenerated; 9B collapses dose-graded
  across 100/150/200 (refusals 18 -> 363 -> 886 while well-formed 886 -> 503 ->
  2, peak clean 5.1% at 150), placing any coherent window below or between the
  registered 50-unit steps. Readback proves the write realized the commanded
  projection exactly on both cells, falsifying the inert-write hypothesis.
  Portable lesson: sigma-distance does not transfer across models (9B collapsed
  at 15.8 sigma, the reference's working distance); coherent dose windows are
  absolute and model-specific. Recalibrated per-cell grids recorded in
  `cell.yaml` (4B {10,20,30,40,50,60,75}, 9B {60,80,100,120,140}); selection
  rule and thresholds unchanged; user approved the paid FIT-sweep-only
  relaunch (~$1-3/cell). This commit also folds in the previously uncommitted
  A10G default-GPU operational change per the 2026-07-08 12:20 entry, now that
  no jobs are in flight. Honest limit carried forward: the existing data does
  not prove a >= 60%/<= 10% window exists for either cell; if the recalibrated
  grid also fails, the cells fail G0 and stay failed.

- 2026-07-08 12:20 EDT: Qwen3.5 semantic batch-parity follow-up found batch 1
  as the only evidenced safe generation batch: 9B passed at batch 1 and failed
  at batch 2 on the same smoke IDs as the earlier high-batch run; 4B failed the
  semantic parity smoke at batch 8. Archived failed/partial Modal live
  namespaces and relaunched clean batch-1 Qwen3.5 4B/9B jobs. Because batch-1
  generation underutilizes A100 memory, future launches default the Modal
  wrapper and generated pipeline metadata back to A10G, with
  `DOUBT_SNAP_MODAL_GPU=A100` reserved for explicit exceptions. The current
  detached Qwen jobs were left running rather than restarted solely for lane
  economics.

- 2026-07-08 08:55 EDT: Qwen3.5 4B and 9B stopped at the pre-outcome
  `batched_parity_smoke` guard after baseline generation, anchor capture,
  direction fitting, and FIT gate fitting all completed. This was not an OOM,
  model-load failure, or intervention failure; no held-out steering outcome was
  run. The guard implementation compared exact generated token IDs, while the
  registered gate in `gates.yaml` specifies identical parsed answers plus stop
  reasons. Updated `prep_tuner_cell.py` to enforce the registered semantic
  parity criterion. Existing volume-backed baseline/capture artifacts are
  resumable; relaunch should re-enter prep, re-check parity, and proceed to FIT
  dose sweep if the semantic smoke passes.

- 2026-07-08 08:40 EDT: Batch-sizing lesson from the first Qwen3.5 Modal
  cells: after the live-volume durability fix, do not use conservative smoke
  batch sizes as production defaults. Qwen3.5 4B baseline generation completed
  cleanly at batch 80 with peak GPU memory about 13.8/39.5 GiB, after resuming
  from 80 already-written rows on the volume. Qwen3.5 9B is running at batch 48
  with live volume commits. Next Modal cells should start aggressively, verify
  the first persisted batch and peak memory, then back off only on OOM, stalls,
  or later-stage capture/steering pressure. Provisional next-start targets:
  4B-class cells batch 160, 8B/9B-class cells batch 64-96 depending on first
  peak, with the caveat that capture and steering can have different memory
  curves than baseline generation.

- 2026-07-08 08:15 EDT: Refreshed the pinned hash for
  `cloud/modal_doubt_snap_cross_family.py` after Qwen3.5 4B exposed a Modal
  preemption edge case. The interrupted worker had generated partial baseline
  rows, but those rows lived only on scratch and were not visible to the
  replacement worker, so tuner `--resume` restarted at zero. The wrapper now
  symlinks each cell's `analysis/<cell_id>` and `analysis-committed/<cell_id>`
  directories onto the Modal volume before GPU work starts and periodically
  commits the volume during long tuner subprocesses. This is an operational
  durability fix only; it does not change model selection, rows, generation
  settings, steering configs, gates, scoring, or dose selection.

- 2026-07-08 07:24 EDT: Refreshed the pinned hash for
  `cloud/modal_doubt_snap_cross_family.py` after a wrapper-only artifact
  preservation fix. The change separates Modal volume copy targets for
  `analysis-committed/` and private `analysis/`; it does not change model
  selection, rows, generation settings, steering configs, gates, scoring, or dose
  selection. This keeps the run inspectable when a cell stops at FIT dose
  selection while preserving the signed scientific instrument.

- (add dated entries as the experiment progresses)
