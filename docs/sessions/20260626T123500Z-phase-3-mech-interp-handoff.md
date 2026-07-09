---
schema_version: research-session/v1
session_id: 20260626T123500Z-phase-3-mech-interp-handoff
title: Phase 3 Mech-Interp Handoff
status: complete
created_at: '2026-06-26T12:35:00Z'
updated_at: '2026-06-26T14:45:00Z'
phase: phase3
question: On resume, is the next Phase 3 mech-interp move more model-variation comparison,
  a stronger causal method, or a return to training/eval?
tags:
- mech-interp-runner
run_ids: []
trajectory:
  anchor: docs/research-trajectory.md
  current_position: GRPO-order regimen sweep complete; canonical detail in session
    note 0023 checkpoints 032-033.
  changed_by_session: Folded dpo_grpo/kto_grpo GRPO-order pass into 0023; closed the
    cross-regimen behavior-axis/readout sweep.
checkpoints: []
legacy_session:
  id: phase3-mech-interp-handoff
  path: docs/sessions/0024 - phase-3-mech-interp-handoff.md
---
# Phase 3 Mech-Interp Handoff

- created: `2026-06-26T12:35:00Z`
- status: GRPO-order pass complete (checkpoints 032-033); regimen sweep closed
- updated: `2026-06-26T14:45:00Z`
- active skill: `mech-interp-runner`
- primary session note: `docs/sessions/20260625T145842Z-phase-3-model-variation-panel.md`
- experiment note: `notes/experiments/mech-interp-model-variation-panel.md`

## Bootstrap

On resume:

1. Read `.skills/mech-interp-runner/SKILL.md`.
2. Run KG-first search before broad grep, for example:
   `bin\search.cmd "phase3 model variation KTO GRPO v2 generated replay calibrated expression" --limit 10`.
3. Read this handoff, then checkpoints 026-031 in
   `docs/sessions/20260625T145842Z-phase-3-model-variation-panel.md`.
4. Do not launch a new run automatically. First align on whether the next move
   is more model-variation comparison, a stronger causal method, or a return to
   training/eval.

## Current State

No Docker containers are running. The KTO replay finished and generated summary
artifacts. Generated tensors/results remain out of normal git status; durable
notes/configs were updated.

Most relevant new result paths:

- `experiment/phase1/probe/analysis/current_clean_kto_unknown_failure_prompt_matched_generation_replay/summary_latest/summary.json`
- `experiment/phase1/probe/analysis/current_clean_kto_unknown_failure_prompt_matched_generation_replay/summary_latest/changed_rows.csv`
- `experiment/phase1/probe/analysis/current_clean_kto_unknown_failure_prompt_matched_behavior_axis_scan/top_layers_all.csv`
- `experiment/phase1/probe/analysis/current_clean_kto_unknown_failure_prompt_matched_multicell_readout/top_readouts_all.csv`
- `experiment/phase1/probe/analysis/current_clean_grpo_dpo_unknown_failure_prompt_matched_behavior_axis_scan/top_layers_all.csv`
- `experiment/phase1/probe/analysis/current_clean_grpo_dpo_unknown_failure_prompt_matched_multicell_readout/top_readouts_all.csv`

## Findings

GRPO-DPO does not look cleaner than GRPO v2 on the prompt-matched 256-row
rare-cell panel. It keeps the same general surface but weakens it: unknown
answering `delta` L15 drops from GRPO v2 `d=2.388`, AUC `0.985`, balanced
accuracy `0.914` to GRPO-DPO `d=2.280`, AUC `0.939`, balanced accuracy
`0.867`. Four-cell readout is also lower: GRPO-DPO best `delta` macro recall
`0.664` vs GRPO v2 `0.695`.

KTO has the sharpest pairwise final-adapter axes but worse multicell coherence.
KTO `delta` L11 reaches unknown-answering `d=2.998`, AUC `0.994`, balanced
accuracy `0.977`; known-overrefusal and unknown-refused-vs-known-correct are
near/perfect pairwise separations at the same layer. But four-cell readout is
weak: best KTO `delta` macro recall is `0.566`, best overall is `h_base` L33
rank-16 macro recall `0.625`.

KTO L11 generated replay does not pass the behavioral gate. Baseline replay had
65/128 unknown refusals and 63/128 unknown answers. Best arm was
`activation_subtraction` coeff 25: 3 unknown answer-to-refusal repairs, 1
unknown refusal-to-answer leak, unknown refusals 65 -> 67, and only +1 known
correctness with no known-refusal movement. Other signs/coefficients were flat
or net negative.

Plain-language read: pairwise AUC/d-prime is not enough. These vectors can
separate rows internally and still fail to steer the generated behavior safely.
The current hand-built single-axis path is looking exhausted for robust
epistemic-humility control.

## Update 2026-06-26: GRPO-order pass complete (option 1 done)

Resumed and ran option 1 (finish the regimen sweep, analysis-only). Two new
prompt-matched 256-row rare-cell panels extracted live (manifests `status=ok`,
`verified=true`, 256 rows): `clean_sft_dpo_grpo` (`extraction__7dfcdd2681a5`)
and `clean_sft_kto_grpo` (`extraction__481dd6eb764c`). See session note 0023
checkpoints 032-033 and `phase3-current-findings.md`. Two findings:

1. FINAL-STAGE DOMINANCE: the final training stage, not the stacking history,
   sets the final-adapter delta geometry. All three GRPO-terminal stacks
   (GRPO v2, dpo_grpo, kto_grpo) converge on a sharp mid-layer L14-15 delta axis
   at AUC `~0.98-0.99`; GRPO overwrites KTO's ultra-sharp L11 axis; the lone
   DPO-terminal stack (GRPO-DPO) is the blurred outlier (AUC `0.939`).
2. SEPARABILITY != COHERENCE across the sweep: best four-cell macro recall ranks
   GRPO v2 `0.695` > GRPO-DPO `0.664` > dpo_grpo `0.648` > kto_grpo `0.641` >
   KTO `0.625`. Plain single-stage GRPO v2 keeps the best coherence; no stacking
   order improves it.

Clean SFT control deferred: its h_base is the original Qwen base (fail-closed
adapterless path) plus a 4-bit-base vs 16-bit-merged quantization-parity confound
the other regimens lack. Treat as a separate methodology decision.

## Next Options

The regimen sweep is now closed at the four-cell prompt-matched level. Remaining
defensible moves:

1. (DONE) Compare remaining model variations: `clean_sft_dpo_grpo` and
   `clean_sft_kto_grpo` complete; clean SFT control deferred per above.
2. Design a stronger method than single mean-difference axes, such as
   readout-derived interventions, answer-field-prefix diagnostics, or a
   constrained multi-layer candidate path.
3. Return to training/eval planning if the research goal is now behavior
   improvement rather than mechanism mapping.

Avoid next:

- More scalar tuning on GRPO v2 L15, GRPO-DPO L15, or KTO L11 as the primary
  path.
- Treating final-prompt-token schema-prompt logit diagnostics as answer/refusal
  evidence.
- Claiming a mechanism from pairwise separability without generated replay.
