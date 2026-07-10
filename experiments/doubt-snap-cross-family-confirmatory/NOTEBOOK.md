# doubt-snap-cross-family-confirmatory notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

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
