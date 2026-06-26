---
title: 'Phase 3 model-variation mechanistic-interpretability panel'
kg:
  id: experiment:mech-interp-model-variation-panel
  type: experiment
  status: canonical
tags:
  - kg/experiment
status: proposed
governance: exploratory
phase: phase3
lane: local
est_compute: 'No GPU for inventory/offline analysis; live extraction or causal replay requires explicit local GPU approval'
relationships:
  - type: tests
    target: '[[gap-4-probe-transfer]]'
    target_id: gap:4-probe-transfer
    confidence: high
  - type: builds_on
    target: '[[grpo-composite-reward-installs-epistemic-output-schema]]'
    target_id: mechanism:grpo-composite-reward-installs-epistemic-output-schema
    confidence: high
  - type: builds_on
    target: '[[dpo-beta-should-follow-pair-quality]]'
    target_id: mechanism:dpo-beta-should-follow-pair-quality
    confidence: medium
  - type: tests
    target: '[[generation-discrimination-gap]]'
    target_id: term:generation-discrimination-gap
    confidence: high
related:
  - '[[gap-4-probe-transfer]]'
  - '[[generation-discrimination-gap]]'
  - '[[grpo-composite-reward-installs-epistemic-output-schema]]'
  - '[[dpo-beta-should-follow-pair-quality]]'
  - '[[2306.03341--inference-time-intervention]]'
  - '[[2606.27359--when-likely-answers-right-sequence-probability-correctness]]'
---

## Question & Hypothesis

Do the JSON-output response-confidence model variations share a coherent
calibrated-expression control surface, or does each fine-tuning regimen produce
distinct behavior-control geometry?

- **Hypothesis.** The refit response-confidence models will not contain one
  clean humility feature. They will show overlapping but regimen-specific
  subspaces for known over-refusal, unknown hallucination, and confidence
  expression. GRPO-centered stacks should share some mid/late-layer behavior
  geometry with the earlier KTO/SFT-DPO panels, but confidence-bearing outputs
  may expose a separate style/confidence axis.
- **Falsifier.** A single same-layer direction, low-rank readout, or SAE feature
  transfers across model variations while improving damaged behavior cells and
  preserving paired desired cells in generated-answer replay.

## Design

This is one umbrella exploratory Phase 3 panel. It starts from the previously
tested Phase 3 finding that simple refusal/answer axes are behaviorally blunt,
then ports the strongest prior analyses onto the JSON-output response-confidence
models.

Initial model rows:

| Row | Model variation | Why include | Current note coverage |
|---|---|---|---|
| `base` | Qwen3-4B instruction base | original behavior control | missing per-model note; adapterless extraction remains fail-closed unless runner supports it |
| `clean_sft_merged` | clean response-confidence SFT | schema/format and broad confidence behavior | missing per-model note |
| `clean_sft_dpo` | clean SFT -> DPO | preference objective after SFT | missing per-model note |
| `clean_sft_kto` | clean SFT -> KTO | unpaired preference objective after SFT | missing per-model note |
| `clean_sft_grpo_v1` | clean SFT -> GRPO v1 | first clean GRPO comparator | inventory comparator only |
| `clean_sft_grpo_v2` | clean SFT -> GRPO v2 | strongest two-stage reward-shaped refusal boundary | missing per-model note |
| `clean_sft_grpo_dpo` | clean SFT -> GRPO v2 -> DPO | current best seed-1 stack | `experiment/notes/clean-sft-grpo-dpo.md` |
| `clean_sft_dpo_grpo` | clean SFT -> DPO -> GRPO v2 | preference then RL contrast | `experiment/notes/clean-sft-dpo-grpo.md` |
| `clean_sft_grpo_kto` | clean SFT -> GRPO v2 -> KTO | RL then unpaired preference contrast | `experiment/notes/clean-sft-grpo-kto.md` |
| `clean_sft_kto_grpo` | clean SFT -> KTO -> GRPO v2 | unpaired preference then RL contrast | `experiment/notes/clean-sft-kto-grpo.md` |

Legacy comparison rows may be used as historical controls only:

- original `sft`, `dpo`, `kto` seed panels;
- Amendment A/B SFT-warmed sequential rows;
- prior KTO/SFT-DPO hidden-state panels before JSON response-confidence refits.

Primary behavior cells:

- `known_correct_answered`;
- `known_refused`;
- `unknown_refused`;
- `unknown_answered_wrong`;
- confidence variants when rows expose `response_confidence`.

Primary analyses:

- behavior-cell inventory and extraction readiness per model row;
- layerwise behavior-axis scans over `h_base`, `h_lora`, and `delta` where
  available;
- calibrated-expression plane/readout analyses before causal claims;
- SAE feature screens as candidate discovery only;
- logit diagnostics and generated-answer replay only after candidate directions
  pass paired-cell sign gates.

## Prerequisites & Gating

- Do not launch Docker, vLLM, hidden-state extraction, or GPU causal replay
  without explicit approval for the named live run.
- Inventory existing extraction manifests before creating new extraction jobs.
- Treat prior Phase 3 results as priors, not as direct evidence for the
  JSON-output models.
- Base/original adapterless extraction remains fail-closed until the live runner
  supports adapterless execution cleanly.
- Each model row must have a traceable eval result in
  `experiment/phase1/eval/analysis/selfaware_full_run_comparison.csv` before
  behavior-cell claims.
- For confidence-bearing claims, inspect unique `response_confidence` values and
  behavior-cell confidence means; JSON coverage alone is not calibration.

## Runbook

1. Read `.agents/skills/mech-interp-runner/references/phase3-current-findings.md`
   and `docs/sessions/0023 - phase-3-model-variation-panel.md`.
2. Inventory existing Phase 3 configs and manifests using
   `python .skills/mech-interp-runner/scripts/phase3_cli.py validate --quick`.
3. Build a model-row inventory from
   `experiment/phase1/eval/analysis/selfaware_full_run_comparison.csv`,
   `experiment/phase1/analysis/training_exhaust_summary.csv`, and existing
   manifests under `experiment/phase1/probe/`.
4. Reuse these prior config families as templates rather than conclusions:
   `experiment/phase1/probe/config/phase3_selfaware_behavior_axis_scan.yaml`,
   `experiment/phase1/probe/config/phase3_selfaware_calibrated_expression_axis_scan.yaml`,
   `experiment/phase1/probe/config/phase3_selfaware_sae_smoke.yaml`,
   `experiment/phase1/probe/config/phase3_gold_kto_targeted_multicell_readout.yaml`,
   and `experiment/phase1/probe/config/phase3_gold_kto_targeted_calibrated_expression_logit_sweep.yaml`.
5. Materialize or update checked-in configs only after the inventory says which
   model rows have usable extraction artifacts and which require live extraction.
6. Run non-GPU/offline scans first. Use live logit diagnostics only after a
   candidate model-row contrast has enough behavior-cell rows and explicit sign
   goals.
7. If a single model row shows distinct layer windows, SAE features, or behavior
   cells not shared by nearby comparisons, split it into a dedicated experiment
   note before expanding that branch.
8. Append checkpoints to `docs/sessions/0023 - phase-3-model-variation-panel.md`
   after each inventory, config materialization, scan, causal diagnostic, or
   generated replay.

## Validation contract

- **Pre-analysis.** The model inventory lists every included row, eval source,
  artifact path, extraction status, behavior-cell counts, and confidence
  availability.
- **Offline gate.** Behavior-axis/readout/SAE outputs report per-model cells,
  layers, roles, effect sizes, AUC or macro recall where applicable, and
  enough row counts for the contrast.
- **Causal gate.** Candidate directions are judged by paired sign goals:
  reduce known over-refusal without lowering unknown refusal; increase refusal
  on unknown wrong answers without increasing refusal on known correct answers;
  preserve or improve response-confidence appropriateness.
- **Behavior gate.** Generated-answer replay is required before claiming any
  improvement in calibrated expression.
- **Definition of done.** We can state whether the JSON-output fine-tuning
  regimens share a reusable behavior-control surface, require model-specific
  mechanisms, or lack steerable evidence under current local methods.

## Outputs & provenance

- Session note: `docs/sessions/0023 - phase-3-model-variation-panel.md`.
- Experiment registry: `experiment/notes/README.md`.
- Model-variation inventory:
  `experiment/phase1/probe/analysis/model_variation_inventory.csv` and
  `experiment/phase1/probe/analysis/model_variation_inventory.md`.
- Inventory script:
  `experiment/phase1/probe/analysis/build_model_variation_inventory.py`.
- Prepared hidden-state extraction configs:
  `experiment/phase1/probe/config/hidden_state_selfaware_manifest_clean_sft_seed1_full.yaml`,
  `experiment/phase1/probe/config/hidden_state_selfaware_manifest_clean_sft_grpo_v2_seed1_full.yaml`,
  and
  `experiment/phase1/probe/config/hidden_state_selfaware_manifest_clean_sft_grpo_dpo_seed1_full.yaml`.
- Current behavior-row overlays:
  `experiment/phase1/probe/analysis/current_selfaware_behavior_rows/`.
- Current clean behavior-axis scan:
  `experiment/phase1/probe/config/phase3_current_clean_behavior_axis_scan.yaml`
  and `experiment/phase1/probe/analysis/current_clean_behavior_axis_scan/`.
- Current clean behavior-axis direction export:
  `experiment/phase1/probe/config/phase3_current_clean_behavior_axis_directions.yaml`
  and
  `experiment/phase1/probe/analysis/current_clean_behavior_axis_directions/`.
- Inventory and derived summaries should live under
  `experiment/phase1/probe/analysis/` or another checked-in analysis directory
  only if they are small, deterministic, and safe to commit.
- Raw hidden-state tensors, generated completions, model weights, and scratch
  run products stay gitignored unless a separate publication decision
  explicitly whitelists them.
- Results are Tier 2 exploratory local mechanism evidence and do not feed Phase
  1 headline claims.

## Variations

- **Umbrella first pass.** One table across all model rows using existing eval
  and extraction artifacts only.
- **Clean-stack focused pass.** Limit to `clean_sft_merged`,
  `clean_sft_grpo_v2`, `clean_sft_grpo_dpo`, and `base` for the first
  calibrated-expression comparison.
- **Preference contrast pass.** Compare `clean_sft_dpo`, `clean_sft_kto`,
  `clean_sft_grpo_dpo`, and `clean_sft_grpo_kto`.
- **GRPO order pass.** Compare `clean_sft_dpo_grpo`,
  `clean_sft_kto_grpo`, `clean_sft_grpo_dpo`, and `clean_sft_grpo_kto`.
- **Per-model split.** Create a dedicated note when a row has a distinct
  mechanism, artifact lifecycle, or live-run plan that would make this umbrella
  note unwieldy.

## Status log

- 2026-06-25: created as a single umbrella note for the JSON-output
  response-confidence model-variation mech-interp panel. Starts from prior
  Phase 3 findings that behavior geometry is distributed and multi-axis, with
  earlier KTO/SFT-DPO configs used as templates rather than direct conclusions.
- 2026-06-25: generated the first model-variation inventory. All JSON-output
  refit rows have eval metrics, but no row has exact current hidden-state
  extraction coverage yet. `clean_sft_dpo` and `clean_sft_kto` have only legacy
  pre-schema extraction candidates. Prioritize current extractions for
  `clean_sft_merged`, `clean_sft_grpo_v2`, and `clean_sft_grpo_dpo`.
- 2026-06-25: prepared model-free validated extraction configs for the three
  first-pass current rows: clean SFT as adapter over original base, GRPO v2 as
  adapter over clean SFT merged, and GRPO-DPO as DPO adapter over GRPO v2
  merged. Each config resolves to 1,233 frozen SelfAware rows; live execution
  still requires an explicit GPU/Docker launch gate.
- 2026-06-25: live local Docker/GPU extraction completed for the first-pass
  current rows: `clean_sft_merged`, `clean_sft_grpo_v2`, and
  `clean_sft_grpo_dpo`. All three manifests are `status=ok` and
  `verified=true`, each with 1,233 rows and `h_base`/`h_lora`/`delta` tensors.
  The original frozen SelfAware row manifest carried legacy SFT/DPO/KTO
  `source_arms`, so current clean-arm behavior-row overlays were materialized
  from current scored eval rows before scanning.
- 2026-06-25: first current clean behavior-axis scan completed. Current panel
  counts: clean SFT has 127 known-refused, 404 known-correct, 670
  unknown-refused, and 7 unknown-wrong rows; GRPO v2 has 168 known-refused, 373
  known-correct, 676 unknown-refused, and 1 unknown-wrong row; GRPO-DPO has 152
  known-refused, 387 known-correct, 676 unknown-refused, and 1 unknown-wrong
  row. Unknown-wrong and confidence-low contrasts were skipped by the
  min-row gate. Delta known-overrefusal axes peaked at AUC 0.908 for clean SFT
  layer 20, 0.915 for GRPO v2 layer 25, and 0.918 for GRPO-DPO layer 12. Broad
  unknown-refused vs known-correct delta axes were near-saturated at AUC
  0.993-0.994 around layers 22-24. Six behavior-axis candidate vectors were
  exported for later logit/generation gates; no causal claim yet.
- 2026-06-26: after the prompt-matched GRPO v2 unknown-failure panel exhausted
  simple and constrained hand-axis steering, shifted the next pass to
  cross-regimen comparison rather than more scalar tuning. First target is
  `clean_sft_grpo_dpo` because it has exact-current extraction coverage and
  differs from GRPO v2 by a final DPO adapter over the GRPO v2 merged base.
  Build a full-eval, quota-gated SelfAware rare-cell panel with the same four
  behavior cells used in the GRPO v2 pass: `unknown_answered_wrong`,
  `unknown_refused`, `known_correct_answered`, and `known_refused`. Use the
  exact Amendment E JSON response-confidence prompt for hidden-state extraction
  and generated replay so source eval labels and replay behavior are comparable.
  Planned follow-on order is `clean_sft_kto`, then the GRPO-order variants
  (`clean_sft_dpo_grpo`, `clean_sft_kto_grpo`) and the clean SFT control, as
  coverage and rare-cell quotas allow.
- 2026-06-26: materialized the first cross-regimen panel for
  `clean_sft_grpo_dpo`. The full SelfAware eval had 69
  `unknown_answered_wrong` rows, so the 64-row rare-cell quota is tight but
  available. Builder output is a balanced 256-row manifest with 128 known and
  128 unknown rows, and embedded behavior labels only for
  `clean_sft_grpo_dpo`. Model-free hidden-state preflight passed for
  `hidden_state_selfaware_manifest_clean_sft_grpo_dpo_unknown_failure_panel_prompt_matched.yaml`
  with config hash prefix `ef1c54a85ce466b2`.
- 2026-06-26: live Docker extraction completed for the GRPO-DPO prompt-matched
  rare-cell panel (`extraction__ef1c54a85ce4`; 256 rows; manifest `status=ok`,
  `verified=true`). Offline behavior-axis and multicell readouts completed.
  Compared with GRPO v2, the unknown-answering contrast is still strongest in
  the same early/mid final-adapter band (`delta` L15), but weaker:
  GRPO v2 `d=2.388`, AUC `0.985`, balanced accuracy `0.914`; GRPO-DPO
  `d=2.280`, AUC `0.939`, balanced accuracy `0.867`. The final DPO delta also
  weakens the known-overrefusal axis relative to GRPO v2 (`delta` best
  `d=1.956`, AUC `0.935` vs GRPO v2 `d=3.276`, AUC `0.999`). Four-cell
  multicell readout remains readable but not cleaner than GRPO v2: best
  GRPO-DPO `delta` L24 full-rank macro recall `0.664` vs GRPO v2 `delta` L26
  full-rank macro recall `0.695`. Interpretation: stacking DPO after GRPO does
  not obviously create a cleaner epistemic-humility control surface in this
  panel; it looks like a weaker/broader version of the same family.
- 2026-06-26: prepared the next cross-regimen panel for `clean_sft_kto`.
  Unlike GRPO v2 / GRPO-DPO, the full KTO SelfAware eval has more rare-cell
  headroom: 196 available `unknown_answered_wrong` rows. For apples-to-apples
  comparison, still selected the same 64-per-cell balanced 256-row panel.
  Model-free hidden-state preflight passed for
  `hidden_state_selfaware_manifest_clean_sft_kto_unknown_failure_panel_prompt_matched.yaml`
  with config hash prefix `1a7322f28ac0175e`; analysis configs now point at
  `extraction__1a7322f28ac0`.
- 2026-06-26: live KTO extraction completed (`extraction__1a7322f28ac0`; 256
  rows; manifest `status=ok`, `verified=true`) and the same offline
  behavior-axis / multicell readouts completed. KTO has the strongest pairwise
  final-adapter separability so far: `delta` L11 unknown-answering contrast
  `d=2.998`, AUC `0.994`, balanced accuracy `0.977`; known-overrefusal
  `delta` L11 `d=3.468`, AUC `1.000`; unknown-refused-vs-known-correct
  `delta` L11 `d=4.436`, AUC `1.000`. But KTO's four-cell readout is worse,
  not better: best `delta` readout is L25 full-rank macro recall `0.566`, and
  best overall is `h_base` L33 rank-16 macro recall `0.625`. Interpretation:
  KTO creates a very sharp pairwise final-adapter behavior axis, but that axis
  may collapse multiple behaviors into a simpler refusal/answering boundary
  rather than a coherent calibrated-expression surface. Generated replay is
  required before treating the L11 axis as useful.
- 2026-06-26: KTO L11 generated replay completed and did not pass the
  behavioral gate. The no-vector replay baseline had 65/128 unknown refusals
  and 63/128 unknown answers, plus 64/128 known refusals and 64/128 known
  answers. The best-looking arm was `activation_subtraction` coeff 25: unknown
  refusals improved from 65 to 67, with 3 unknown answer-to-refusal repairs but
  still 1 unknown refusal-to-answer leak; known correctness improved by only one
  row and known refusal count did not move. Other signs/coefficients were flat
  or net negative. Interpretation: even KTO's sharp L11 pairwise axis mostly
  changes wording and does not deliver robust calibrated-expression control.
- 2026-06-26: completed the GRPO-order pass of the regimen sweep with two new
  prompt-matched 256-row rare-cell panels (64/cell), analysis-only (no generated
  replay). `clean_sft_dpo_grpo` (SFT->DPO->GRPO; `extraction__7dfcdd2681a5`) and
  `clean_sft_kto_grpo` (SFT->KTO->GRPO; `extraction__481dd6eb764c`) both extracted
  live via Docker, manifests `status=ok`, `verified=true`, 256 rows each. Final
  GRPO adapter over the respective SFT->DPO / SFT->KTO merged base, so delta
  isolates the final GRPO surface. Behavior-axis (best per contrast/role) and
  four-cell multicell readout (balanced ridge, CV=4) results:
  - dpo_grpo: unknown-answering `delta` L14 `d=2.391`, AUC `0.983`, balacc
    `0.961`; known-overrefusal `delta` L13 `d=3.205`, AUC `1.000`. Best four-cell
    readout `h_lora` L21 full-rank macro recall `0.648`.
  - kto_grpo: unknown-answering `delta` L14 `d=2.269`, AUC `0.987`, balacc
    `0.953`; known-overrefusal `delta` L12 AUC `1.000`. Best four-cell readout
    `h_base` L6 rank-16 / `delta` L22 full macro recall `0.641`.
  Two findings. (1) FINAL-STAGE DOMINANCE: the final training stage, not the
  stacking history, sets the delta-surface geometry. All three GRPO-terminal
  stacks (GRPO v2, dpo_grpo, kto_grpo) converge on the same sharp mid-layer
  (L14-15) delta signature at AUC `~0.98-0.99`; the GRPO stage even overwrites
  KTO's distinctive ultra-sharp L11 axis (kto_grpo looks like GRPO, not standalone
  KTO). The lone DPO-terminal stack (GRPO-DPO) is the outlier (blurred, AUC
  `0.939`). (2) SEPARABILITY != COHERENCE confirmed across the sweep: best
  four-cell macro recall is GRPO v2 `0.695` > GRPO-DPO `0.664` > dpo_grpo `0.648`
  > kto_grpo `0.641` > KTO `0.625`. Plain single-stage GRPO v2 has the best
  multicell coherence; no stacking order improves it, and the sharp GRPO-terminal
  pairwise axes do not translate into a cleaner calibrated-expression surface.
  This independently re-confirms that hand-built linear surfaces are exhausted for
  calibrated-expression control. Clean SFT control deferred: its h_base would be
  the original Qwen base (fail-closed adapterless path) plus a 4-bit-base vs
  16-bit-merged quantization-parity wrinkle the other regimens do not have.
- 2026-06-26: SYNTHESIS — naming the result and connecting it to the literature.
  The sweep's `separability != coherence != steerability` pattern is not a defect
  of our probes; it is the **generation-discrimination gap**
  ([[generation-discrimination-gap]], coined by Saunders et al., operationalized
  by ITI [[2306.03341--inference-time-intervention]] as a ~40-point probe-vs-
  generation gap on LLaMA-7B / TruthfulQA). Our contribution is to show the gap
  is **regimen-robust** in the calibrated-epistemic-humility setting: across five
  fine-tuning regimens (SFT-DPO-GRPO, SFT-KTO-GRPO, GRPO v2, GRPO-DPO, KTO) the
  final-adapter delta is highly *separable* (pairwise AUC ~0.98-0.99,
  final-stage-determined) yet does not *steer* generated behavior safely
  (KTO L11 replay failed the gate; best four-cell macro recall only 0.695). This
  is direct evidence on [[gap-4-probe-transfer]] (Gap 4, meta-analysis §6.3): the
  representations DO move with the final training stage, but the moved signal is
  the *performance of humility* read off internal state, not a behaviorally
  controllable calibration surface — exactly the representations-vs-behavior split
  the gap predicts. The same dissociation appears in a different surface in
  [[2606.27359--when-likely-answers-right-sequence-probability-correctness]]:
  sequence probability predicts correctness across prompts but maximizing it does
  not transfer to decoding decisions (predictiveness != interventional efficacy).
  Inherited cautions: probes may read knowledge-recall rather than calibration
  ([[2510.09033--probes-read-recall-not-truth]]), so the high separability should
  not be over-read as a calibration signal. METHOD CONSEQUENCE for next step:
  ITI's gains came from where it reads/applies the direction — a sparse set of
  *attention heads*, intervened *token-by-token during generation* at intermediate
  strength — not from a better single residual-stream axis (mass-mean, which we
  already use, was ITI's best estimator). Our probe currently extracts
  residual-stream, final-prompt-token vectors only; closing the gap (Step A) means
  extending extraction to per-head activations and applying the direction during
  generation, not more scalar tuning of one residual axis.
