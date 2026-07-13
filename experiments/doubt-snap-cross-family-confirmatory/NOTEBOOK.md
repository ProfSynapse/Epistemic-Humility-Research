# doubt-snap-cross-family-confirmatory notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

- 2026-07-12 (resolve): Outcome written and the manifest set to resolved,
  now that the held-for comparator landed: `qwen35-4b-midband-doubt-snap`
  resolved G1 PASS at hs20 dose 8 x sigma_c (refused 0.684, well-formed
  0.980, known false-refusal 10/240 = 0.042, in-sample FIT, red-teamed with
  no invalidating finding). Verdict: NOT PROMOTED; prediction not met
  (arithmetically unreachable after three small-tier G0 stops); falsifier
  not triggered because its registered wording binds held-out fails only, a
  gap recorded straight in the Outcome. The Outcome adjudicates the stops
  as indicting the universal 0.94-depth write-site rule rather than the
  mechanism class, on two legs: the c_hat validity audit (encoding readable
  0.84-0.99 in all four families, actuation Qwen-lineage-only at the late
  site) and the same-substrate mid-band ladder (same instrument, same FIT
  rows, late site 0.326 vs hs20 0.684 with intact well-formedness). Both
  legs are cited as context, never pooled. Successor design requirements
  recorded: per-family write sites from the jspace-family-atlas layer map,
  and prediction/falsifier wording that covers uniform pre-outcome stops.

- 2026-07-12 (c_hat validity audit complete; lead-verified): the CPU audit
  over the existing anchor captures answers whether the fleet's write
  direction ever encoded refusal. Per cell (llama32_3b, mistral7b,
  qwen35_4b, qwen35_9b; all alignment sanity checks passed, u_d rederived
  AUC matches the recorded gate AUC to 4 decimals; lead independently
  re-derived mistral's two headline AUROCs from raw tensors, 0.543/0.896
  vs audit 0.551/0.901, pooled-vs-heldout populations): (1) a raw
  mass-mean refused-vs-answered direction reads at 0.997-1.000 held-half
  AUROC in ALL FOUR families at the steered layer/anchor, so the
  refusal-vs-answering axis exists and is trivially linearly readable
  everywhere; (2) the registered c_hat reads refused-vs-known at CHANCE
  (0.50-0.55) in all four cells while reading refused-vs-confab at
  0.84-0.99 (mistral 0.90) - exactly matching its registered
  construction (prep_tuner_cell.py fit_directions: caution =
  unit(mean(refused) - mean(confab)), then orthogonalized against
  {u_d, u_p}, and u_d is anti-aligned with the raw refusal axis at cos
  -0.73 to -0.81, so any refuse-vs-answer leakage is projected out);
  (3) the orthogonalization removed only 0.6-6 percent of pos_ctrl norm
  on llama/mistral (15-20 percent on the qwen cells), so the recipe, not
  the orthogonalization, determines the content. Interpretation for the
  Outcome: the fleet never pushed the refuse-vs-answer axis by DESIGN
  (that is the axis that would wreck known-correct answers; known cost
  was correspondingly ~1 percent everywhere); it pushed the
  refuse-rather-than-confab encoding, which reads cleanly in every
  family including mistral, yet moves behavior only on Qwen3-lineage
  (strongly on Qwen3-4B, weakly on Qwen3.5/llama) and not at all on
  mistral. The cross-family nulls are therefore a genuine
  read-actuate dissociation, not a failure to locate the encoding.
  Caveat recorded straight: on llama/mistral the random-direction
  reference reads refused-vs-known at 0.77-0.83 (a norm/position
  confound in cross-population contrasts at this anchor), so
  cross-population AUROCs there carry some norm artifact; the
  within-comparison contrast (c_hat chance vs mass-mean ~1.0 on the
  same populations, and clean ~0.5 random on both qwen cells) is
  unaffected. Full numbers in the session scratch audit report;
  aggregates only, no row text.

- 2026-07-12 (fleet abandoned, user decision; resolve arc opens): with three
  of four small-tier families G0-stopped before held-out (qwen35_4b 0.326
  peak, llama32_3b 0.184 peak, mistral7b 0.000 flat) the registered
  prediction (at least 3 of 4 small-tier families pass) is arithmetically
  unreachable, so the user decided in-conversation to launch no further
  cells (gemma4_e4b and the mid-tier remain unlaunched; gemma3_12b was
  already access-blocked). The experiment moves to resolve as
  not-promoted. Note for the Outcome: the registered falsifier is defined
  on held-out G1/G2/G3 fails and can never trigger when cells stop at G0,
  a wording gap to record honestly. Before writing the Outcome, a CPU
  audit was dispatched over the existing anchor captures to test whether
  each cell's fitted c_hat actually reads refusal in that model's own
  activations (refused-vs-answered AUROC for c_hat, u_d, random, and a raw
  mass-mean refusal direction, plus cosines): the prior cross-family
  readout claim (Amendment Z) certified gate/dial/veto READING only and
  never certified a caution/refusal direction in any family, and this
  experiment's G0 gated only the doubt gate's AUC, never c_hat's semantic
  validity. The audit result determines whether the per-family actuation
  nulls are "no lever at this direction" or "we never fit the lever."

- 2026-07-12 (mistral7b_instruct_v03 terminal: G0 FIT dose-viability fail,
  true behavioral null): the bracketed dose sweep completed on all seven
  doses (1129 rows per arm) and the registered FIT-only selection rule
  found no qualifying dose (exit 4); committed artifacts pulled into
  `analysis-committed/mistral7b_instruct_v03/`. This null is neither
  overdose artifact nor sub-threshold grid: the ladder correctly spans the
  response window this time. At dose 30 (realized strength 31.9) the write
  visibly moves tokens (only 11/876 fired answers identical to baseline)
  while 638/876 remain well-formed; dose 38 is transitional (474
  degenerate); dose 46 and above are fully degenerate. Dose parameterizes
  correctly (cross-dose answer identity ~0 except the shared collapse
  plateau at 46 vs 56). Yet fired-confab clean_tighten is 0/874 at every
  dose and induced refusals are zero even inside the coherent window: the
  c_hat caution write changes what Mistral says without ever moving it
  toward refusal. Gate AUC on FIT 0.9998, parity clean, held-out power met
  (1312 confab / 382 known-correct). Recorded straight as a G0
  dose-viability fail before held-out scoring. Probe complete: both probe
  cells terminal, no live apps, no further spend. Small-tier picture at
  the FIT stage: qwen35_4b selective peak 0.326, llama32_3b selective peak
  0.184, mistral7b flat zero; none reaches the registered 0.60 floor, so
  none proceeds to held-out. Fleet-scale decision (remaining unlaunched
  cells vs adjudication of the confirmatory) lifted to the user.

- 2026-07-11 (llama32_3b_instruct terminal: G0 FIT dose-viability fail,
  characterized): the recalibrated dose sweep completed and the registered
  FIT-only selection rule found no qualifying dose (exit 4,
  `no_registered_candidate_dose_met_fit_selection_criteria`); committed
  artifacts pulled from the volume into
  `analysis-committed/llama32_3b_instruct/`. Unlike the earlier overdose
  nulls, this is a fully characterized instrument result: a selective
  interior dose-response on FIT with peak fired-confab clean_tighten 0.184
  (107/581, Wilson 95% [0.155, 0.218]) at dose 19 (realized strength 9.1)
  with known-correct false-refusal 0.009 (2/222), falling to 0.105 at dose
  26 and collapsing to 0.000 at doses 34 and above. Every other instrument
  check passed: gate AUC on FIT 0.9992, directions byte-identical on refit,
  batched parity smoke clean, generation termination 0.999, held-out power
  met (872 confab / 334 known-correct). The cell records a G0
  dose-viability fail before held-out scoring, per the registered rule,
  because the peak sits far below the 0.60 clean_tighten floor. No grid
  changes follow: the response window is characterized and the effect size
  is the finding. Probe-cell pattern so far: qwen35_4b peak 0.326, llama
  peak 0.184, both selective and both below floor; mistral7b sweep in
  progress on the bracketed grid.

- 2026-07-11 (mistral smoke refusal, pre-sweep grid correction, probe-strength
  decouple): the mistral7b relaunch on the sigma-mapped grid crashed by design
  at the in-pipeline gen-stream smoke (`gen_stream_fired: False`, exit 4): the
  probe write at strength 27, equal to the strongest arm the grid would have
  run (28.75 after sigma division), produced byte-identical output on all 8
  probe rows. The guard did its job: the entire mapped grid [6..27] is below
  mistral's token-movement threshold, so the sweep would have been a
  predetermined all-inert null. This falsifies the sigma-ladder transfer
  assumption for mistral (inert at 29 sigma where llama fires at comparable
  sigma). The stopped default-grid partial sweep bounds the response region
  from above: 584/584 fired FIT confabs degenerate at dose 100 (realized
  strength 106.5), while the morning probe at 250 moved tokens. Actions, all
  pre-sweep and pre-outcome for this cell, recorded in a dated AMENDMENT
  extension: (1) mistral7b grid revised to log-span the empirical bracket
  (27, 100): [30, 38, 46, 56, 67, 80, 92]; (2) `prep_tuner_cell.py` smoke
  probe decoupled from the dose grid to fixed strength 250.0 matching
  `smoke_tuner_path.py` (plumbing check, not a registered dose; tying it to
  max(dose_grid) makes it inert for any legitimately low grid); (3) both pin
  hashes refreshed. The registered selection rule was never evaluated on the
  [6..27] grid, so the no-further-grid-changes clause never triggered. llama's
  grid is untouched: its sweep is mid-run and showing a real interior
  dose-response (fired-confab clean_tighten 64 -> 107 -> 61 across strengths
  5.3 -> 9.1 -> 12.4, collapse above), well below the 0.60 selection floor so
  far, which the sweep will adjudicate on completion. Mistral relaunches
  detached at batch-1 under the existing $75 probe approval, re-entering at
  the dose sweep on volume-backed artifacts.

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
