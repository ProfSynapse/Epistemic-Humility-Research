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
| `clean_sft_grpo_dpo` | clean SFT -> GRPO v2 -> DPO | current best seed-1 stack | `experiments/grpo-centered-stacking/RUNBOOK.md` |
| `clean_sft_dpo_grpo` | clean SFT -> DPO -> GRPO v2 | preference then RL contrast | `experiments/grpo-centered-stacking/RUNBOOK.md` |
| `clean_sft_grpo_kto` | clean SFT -> GRPO v2 -> KTO | RL then unpaired preference contrast | `experiments/grpo-centered-stacking/RUNBOOK.md` |
| `clean_sft_kto_grpo` | clean SFT -> KTO -> GRPO v2 | unpaired preference then RL contrast | `experiments/grpo-centered-stacking/RUNBOOK.md` |

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

1. Read `.agents/skills/mech-interp-runner/SKILL.md` (router; for interpretation
   invariants see `references/interpretation-invariants.md`) and
   `docs/sessions/20260625T145842Z-phase-3-model-variation-panel.md`. Current findings live
   in that session note and in this experiment note, not in the skill.
2. Inventory existing Phase 3 configs and manifests using
   `python .skills/mech-interp-runner/scripts/phase3_cli.py validate --quick`.
3. Build a model-row inventory from
   `experiment/phase1/eval/analysis/selfaware_full_run_comparison.csv`,
   `experiment/phase1/analysis/training_exhaust_summary.csv`, and existing
   manifests under `experiment/phase1/probe/`.
4. Reuse these prior config families as templates rather than conclusions:
   `archive/experiment/phase1/probe/config/selfaware-behavior-axis/phase3_selfaware_behavior_axis_scan.yaml`,
   `archive/experiment/phase1/probe/config/selfaware-calibrated-expression-axis/phase3_selfaware_calibrated_expression_axis_scan.yaml`,
   `archive/experiment/phase1/probe/config/selfaware-sae-screens/phase3_selfaware_sae_smoke.yaml`,
   `experiment/phase1/probe/config/phase3_gold_kto_targeted_multicell_readout.yaml`,
   and `archive/experiment/phase1/probe/config/gold-kto-targeted-rare-cell-panels/phase3_gold_kto_targeted_calibrated_expression_logit_sweep.yaml`.
5. Materialize or update checked-in configs only after the inventory says which
   model rows have usable extraction artifacts and which require live extraction.
6. Run non-GPU/offline scans first. Use live logit diagnostics only after a
   candidate model-row contrast has enough behavior-cell rows and explicit sign
   goals.
7. If a single model row shows distinct layer windows, SAE features, or behavior
   cells not shared by nearby comparisons, split it into a dedicated experiment
   note before expanding that branch.
8. Append checkpoints to `docs/sessions/20260625T145842Z-phase-3-model-variation-panel.md`
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

- Session note: `docs/sessions/20260625T145842Z-phase-3-model-variation-panel.md`.
- Retired experiment-note registry: `archive/notes/experiments/README.md`.
- Model-variation inventory:
  `docs/research/phase3-model-variation-inventory.csv` and
  `docs/research/phase3-model-variation-inventory.md`.
- Inventory script:
  `docs/research/scripts/phase3/build_model_variation_inventory.py`.
- Prepared hidden-state extraction configs:
  `archive/experiment/phase1/probe/config/selfaware-hs/hidden_state_selfaware_manifest_clean_sft_seed1_full.yaml`,
  `archive/experiment/phase1/probe/config/selfaware-hs/hidden_state_selfaware_manifest_clean_sft_grpo_v2_seed1_full.yaml`,
  and
  `archive/experiment/phase1/probe/config/selfaware-hs/hidden_state_selfaware_manifest_clean_sft_grpo_dpo_seed1_full.yaml`.
- Current behavior-row overlays:
  `experiment/phase1/probe/analysis/current_selfaware_behavior_rows/`.
- Current clean behavior-axis scan:
  `archive/experiment/phase1/probe/config/current-clean-behavior-axis-directions/phase3_current_clean_behavior_axis_scan.yaml`
  and `experiment/phase1/probe/analysis/current_clean_behavior_axis_scan/`.
- Current clean behavior-axis direction export:
  `archive/experiment/phase1/probe/config/current-clean-behavior-axis-directions/phase3_current_clean_behavior_axis_directions.yaml`
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

## Sub-hypothesis H_monitor (uncertainty monitor) and test battery

> **Canonical home: session note `docs/sessions/20260626T191124Z-uncertainty-monitor-hypothesis.md`.**
> The H_monitor thread was spun off from this panel into a dedicated session note
> (it is an evolution of, but conceptually separate from, the model-variation
> panel). The reframe, competing-hypothesis battery, and random-head control
> verdict live in 0025; the summary below is retained as the panel-side pointer.

Arising from the Step A.4 sweep (session 0023 checkpoints 038-039). The per-head
ITI direction, built as `mean(unknown_answered_wrong) - mean(unknown_refused)`
on 11 heads, steers with an INVERTED causal sign (adding the "wrong-answer"
direction raises refusal) and acts as a partially knowledge-conditioned
abstention dial (~5.6x more effect on unknown than known).

- **H_monitor.** The direction is not a "be-wrong" axis but a GRADED internal
  uncertainty / "this-is-hard, I-might-not-know" monitor present during hard
  questions regardless of the answer-vs-refuse outcome. Hallucinations =
  sub-threshold alarm (model guessed); refusals = supra-threshold (model bailed);
  amplifying the alarm pushes more items over the threshold -> more refusal
  (the "stimulant amplifies the brake, not the symptom" shape).
- **Competing hypotheses to kill.** H_wrongness (original "be-wrong" axis;
  contradicted by the sign). H_refusal_motor (it is just the refuse-vs-answer
  motor direction, not an epistemic monitor). H_OOD_default (no specific signal;
  any large perturbation collapses to the model's default JSON abstention).
- **Falsifier for H_monitor.** theta-projection does NOT track independent
  difficulty among answered items, OR theta is ~parallel to the refuse-vs-answer
  axis, OR matched-norm random heads/directions reproduce the abstention shift,
  OR it fails to transfer across datasets/regimens.

Circularity guard: never score the monitor against the same wrong/refused labels
theta was built from. Use INDEPENDENT difficulty (stated `response_confidence`,
answer-token logprob, resample accuracy, or an external model).

Test battery (priority order; cheapest/most-discriminating first):

1. **Geometry vs refusal axis** (offline). cosine(theta_failure,
   theta_refuse-vs-answer) per head; ~1 collapses H_monitor into H_refusal_motor.
2. **Flip-order vs difficulty** (offline, reuses the A.4 sweep). Per unknown item,
   the alpha at which it flips to refusal vs independent difficulty. Monitor =>
   difficulty-ordered flips; OOD-default => difficulty-agnostic.
3. **Read-don't-steer wrongness prediction** (offline). Among ANSWERED items,
   does theta-projection predict the answer being WRONG? Doubles as the
   selective-prediction/abstention-trigger test (AUC vs the model's own stated
   confidence).
4. **Ground-truth difficulty grading** (GPU). Resample N times; empirical accuracy
   = difficulty; check projection rises monotonically.
5. **Pre-commitment timing** (GPU). Projection trajectory across generated tokens;
   high BEFORE the refusal tokens appear separates monitor from decision-echo.
6. **Random-DIRECTION control** (GPU). Same 11 heads, random directions, matched
   norm; crosses head x direction with the random-HEAD control.
7. **Cross-dataset / cross-regimen transfer** (GPU). Build theta here, read+steer
   on TriviaQA/bridge and on KTO/DPO. Transfer => general monitor; speaks directly
   to `gap:4-probe-transfer`.

Literature grounding (KG): `paper:2306.03341` ITI, `paper:2310.01405` RepE,
`paper:2212.03827` CCS, `paper:2304.13734` internal-state-knows-when-lying,
`paper:2207.05221` P(IK), `paper:2510.09033` (probes read recall not truth --
the key caution), `term:truth-direction`, `term:universal-truthfulness-hyperplane`,
`term:knowledge-boundary`. External gaps under ingestion (Geometry of Truth,
Semantic Entropy Probes, selective-prediction-for-LLMs).

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
- 2026-06-26: STEP A.1-A.3 — per-head extraction lands; the failure axis is the
  sparsest, weakest head signal. Added an additive `attention_head` extraction
  granularity (residual path byte-for-byte unchanged) that hooks each decoder
  block's `self_attn.o_proj` INPUT — the concatenated per-head context vectors,
  width `num_attention_heads * head_dim`. Ran it on GRPO v2 (best-coherence
  regimen) prompt-matched to the same SelfAware manifest: manifest
  `status=ok verified=True`, 32 heads x head_dim 128 = width 4096 across 36
  blocks, 256 rows. GQA was load-bearing: Qwen3-4B `hidden_size=2560` so
  `hidden//heads = 80 != 128`; the split reads `head_dim` from config, never
  `hidden_size // num_heads`. New offline `phase3_head_localization_scan.py`
  splits each block vector into its 32 per-head slices and computes a mean-diff
  axis per (block, head), reusing the residual scan's metric primitives
  (10,368 axes/role). Result (delta role): the refuse-vs-answer IDENTITY axis is
  richly head-distributed and sharply localized (223/1152 heads >= 0.85 AUC, best
  L34H17/L32H14 ~0.98), and GRPO pushes it into LATE heads (L32-35) where the base
  representation has it mid-stack (L21-22). The FAILURE-discrimination axis we
  need to steer (`unknown_answered_wrong vs unknown_refused`) is the sparsest and
  weakest (20/1152 heads >= 0.85, best L21H17 AUC 0.910). Single-head best AUC is
  0.02-0.08 below the full-block AUC (a 128-dim head carries less than the
  4096-dim block) — per-head's value is sparse-intervention localization, not a
  sharper probe. This sharpens [[gap-4-probe-transfer]]: GRPO moved the *identity*
  of refusal far more than the *failure discrimination* the behavior needs,
  predicting Step A.4 steering will be hardest on the axis that matters most. Top
  failure-axis steering targets for A.4: L21H17, L35H0, L23H1, L7H30, L10H11,
  L22H12.
- 2026-06-26: STEP A.4 input — ITI steering-direction artifact built (GPU-free).
  New `phase3_head_steering_directions.py` reads the per-head extraction and a
  chosen sparse target set and emits, per head, the ITI triple the generation
  hook consumes: `theta` (unit mass-mean direction `mean(positive) -
  mean(negative)`), `sigma` (std of the arm's per-head activations projected onto
  theta — the ITI scale, `h' = h + alpha*sigma*theta`), and projection
  provenance. Directions are computed from the `h_lora` (adapter-active) arm —
  the forward pass the harness will hook — not delta. Targets = union of the
  top-6 `h_lora` and top-6 `delta` failure-axis heads (11 sparse heads; L21H17 is
  the robust overlap). GRPO v2 run: all 11 unit-norm, 64 unknown-wrong / 64
  unknown-refused rows, per-head sigma 0.18-3.0. Sign convention: positive =
  `unknown_answered_wrong` projects higher than negative = `unknown_refused`, so
  steering toward the SAFE behavior (refuse) is `alpha<0`; the artifact records
  the labels and the harness sweeps both signs. Remaining for A.4:
  `phase3_head_intervention.py` (GPU) — hook the 11 heads' `o_proj` input, add
  `alpha*sigma*theta` per generated token, sweep alpha, score behavior cells, run
  the generated-replay gate. Build + tiny-model test offline; gate the GPU sweep.
- 2026-06-26: STEP A.4 mechanism — per-head intervention landed + tested
  (GPU-free core). `phase3_head_intervention.py` discovers each block's
  `self_attn.o_proj` (same name-suffix/regex discovery as the extraction backend)
  and registers forward PRE-hooks that add `alpha*sigma*theta` to each target
  head's column slice of the o_proj INPUT at ALL token positions, so under
  generation the steer fires once per decode step — token-by-token, as ITI
  prescribes (NOT the residual-stream final-prompt-token hook in
  `phase3_causal_pilot_runner.py`, which the sweep showed is exhausted).
  `build_block_deltas` precomputes per-head `delta = alpha*sigma*theta` grouped by
  block; `per_head_intervention` is a context manager that removes handles in
  `finally`. Torch-injected so a tiny 2-layer/2-head/head_dim-3 module verifies it
  offline (5 tests): delta scales as `alpha*sigma*theta`, only the target head
  slice shifts across all positions, only the target block is touched, hooks are
  removed after the context, and discovery fails loudly on a mis-claimed block
  count. The GPU runner (4B model load + alpha sweep + behavior-cell scoring) is
  the explicit-gate follow-up; the CLI `main()` is a gated placeholder. Score
  generated outputs with the existing replay/eval cell scorer rather than
  duplicating the JSON behavior parser. Predicted negative if the sparse 11-head
  steer cannot move the cells safely: the failure axis is too weak/sparse at head
  granularity, closing Step A on a Tier-2 negative pointing back to training/eval.
- 2026-06-26: STEP A.4 sweep RESULT — sparse 11-head ITI is causally potent but
  SIGN-INVERTED vs the probe and only partially selective (gate = partial pass).
  `phase3_head_intervention_runner.py` (gated GPU) loaded GRPO v2 (merged base +
  active adapter) and generated the 256-row matched panel (128 known/128 unknown,
  greedy, 96 new tokens) under the 11-head intervention across alphas
  `[-8,-4,-2,0,+4]` (0 = no-hook baseline), scored with the causal-pilot
  generated-replay cell scorer. Four cells are MONOTONIC in alpha (counts /128).
  Failure cell `unknown_answered_wrong`: `-8:76 / -4:66 / -2:66 / 0:61 / +4:22`.
  `unknown_refused`: `52/62/62/67/106`. `known_correct`: `61/62/64/63/56`.
  `known_refused` (over-refusal): `61/62/63/65/72`. No thinking-tag contamination.
  (1) SIGN INVERSION: the A.4-input artifact predicted `alpha<0` = toward safe
  refusal (positive=wrong-answer projects higher), but causally `alpha>0` (ADDING
  the wrong-answer direction) raises refusal; `alpha<0` makes the failure WORSE.
  A direct probe-causality dissociation — the per-head linear axis does not move
  generation in the sign its projection predicts. (2) PARTIAL SELECTIVITY: at
  `+4` the failure cell drops 61→22 (−64%), unknown refusal +39, while known
  over-refusal rises only +7 and known-correct falls only −7 — unknown abstention
  moves ~5.6× harder than known (knowledge-conditioned) but not collateral-free.
  Aggregate truthful_rate `50.8→63.3` at +4, entirely via raised abstention.
  Gate verdict PARTIAL PASS at +4: sparse per-head ITI is a *partially
  knowledge-conditioned abstention dial*, not a clean humility switch — sharpest
  local evidence yet on `gap:4-probe-transfer` (representation carries causal,
  ~5:1-selective abstention control, so NOT behavior-only, but sign-inverted vs
  the readout and imperfectly selective). Positive side UNDER-SAMPLED (only +4;
  collateral curves flat through −4, break at +4 → magnitude-driven). Natural
  refinement Step A.4b: positive-only `[+1,+2,+3,+6]` sweep (new fingerprint →
  `--fresh`/new dir) to find any collateral-free window. Resume/checkpoint infra
  proved out: the run finished after a CLI-teardown kill at 901/1280 rows by
  resuming (379 generated, 901 reused, identical fingerprint).
- 2026-06-26: RANDOM-HEAD CONTROL launched (sigma-matched + norm-matched) +
  H_monitor hypothesis registered (see the sub-hypothesis section above; session
  0023 checkpoint 039). The control tests whether the A.4 abstention shift is
  specific to the 11 localized heads or reproduced by any 11 heads at matched
  push. Two variants bracket the magnitude confound: sigma-matched random heads
  carry only ~0.30x the localized perturbation energy at matched alpha, so a
  norm-matched variant grafts the localized sigma multiset onto random heads
  (`phase3_head_norm_match_control.py`). Random heads chosen by numpy seed
  20260626, disjoint from the localized 11. Early peek (sigma-matched `-8` arm):
  localized drove unknown_answered_wrong to 76 / refusal to 52; random heads sat
  near baseline (wrong 54 / refusal 74) -- i.e. random heads did NOT reproduce
  the localized effect -- but this is the weaker push and the decisive `+4` arm +
  norm-matched run were still pending at log time. H_monitor test battery (Tier
  1-3) registered for follow-up; Tier 1 (geometry-vs-refusal-axis,
  flip-order-vs-difficulty, read-don't-steer wrongness prediction) is offline and
  reuses data in hand. Literature grounding via a parallel research+ingestion
  pass against the existing KG (ITI, RepE, CCS, P(IK), probes-read-recall).
