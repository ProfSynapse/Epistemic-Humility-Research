---
title: refusal-axis-ablation-confirmatory
aliases:
- Refusal-axis ablation fresh-seed confirmatory
- refusal-axis-ablation-confirmatory (FALSIFIED)
tags:
- kg/experiment
- experiment
- abstention
kg:
  id: experiment:refusal-axis-ablation-confirmatory
  type: experiment
  status: canonical
related:
- '[[caution-ablation-rederivation]]'
- '[[grpo-three-seed-confirmatory]]'
- '[[raw-theta-refusal-axis-ablation-rederives-archived-overrefusal-collapse]]'
- '[[full-refusal-axis-ablation-collapse-is-seed1-specific]]'
- '[[directional-ablation]]'
relationships:
- type: builds_on
  target: '[[caution-ablation-rederivation]]'
  target_id: experiment:caution-ablation-rederivation
  confidence: high
  evidence:
  - "experiments/refusal-axis-ablation-confirmatory/AMENDMENT.md Motivation and posture (registered per the program's promotion rule as the confirmatory step for caution-ablation-rederivation's seed-1 raw-theta result, requested by the PI 2026-08-16; same registered recipe, executed end-to-end on a fresh seed with no artifact reuse from seed 1)"
- type: builds_on
  target: '[[grpo-three-seed-confirmatory]]'
  target_id: experiment:grpo-three-seed-confirmatory
  confidence: high
  evidence:
  - "experiments/refusal-axis-ablation-confirmatory/AMENDMENT.md Design (substrate clean_sft_grpo_v2_seed2: published seed-2 GRPO-v2 LoRA on the published seed-2 merged SFT base, on its own per-seed lineage)"
- type: uses
  target: '[[directional-ablation]]'
  target_id: method:directional-ablation
  confidence: high
  evidence:
  - "experiments/refusal-axis-ablation-confirmatory/AMENDMENT.md Design (four-arm residual intervention: baseline, ablate, shift -2 sigma, shift +2 sigma, on a freshly fit raw mass-mean refusal-axis direction at L35)"
- type: tests
  target: '[[raw-theta-refusal-axis-ablation-rederives-archived-overrefusal-collapse]]'
  target_id: mechanism:raw-theta-refusal-axis-ablation-rederives-archived-overrefusal-collapse
  confidence: high
  evidence:
  - "experiments/refusal-axis-ablation-confirmatory/AMENDMENT.md#outcome (RC-G1: post-ablation known-item over-refusal 0.5528 >= 0.30, falsifier fired; the seed-1 raw-theta 0.994-to-0.030 collapse does not transfer to a fresh seed)"
- type: supports
  target: '[[full-refusal-axis-ablation-collapse-is-seed1-specific]]'
  target_id: mechanism:full-refusal-axis-ablation-collapse-is-seed1-specific
  confidence: high
  evidence:
  - "experiments/refusal-axis-ablation-confirmatory/AMENDMENT.md#outcome (arm table and descriptive observations)"
---

Registered confirmatory of the [[caution-ablation-rederivation]] seed-1 raw-theta
result, requested by the PI 2026-08-16 under the program's standing promotion
rule (an exploratory win becomes a paper claim only via a confirmatory
replication registered before it runs). Same registered recipe (fresh L35
raw mass-mean refusal-axis direction fit, four-arm residual intervention,
byte-identical prompt text, parity-locked archived intervention engine)
executed end-to-end on `clean_sft_grpo_v2_seed2`'s own per-seed lineage
(published seed-2 GRPO-v2 LoRA on the published seed-2 merged SFT base,
local copies on disk; no seed-1 artifacts anywhere in the chain).

Resolved 2026-08-16, PI approval in-conversation. **Verdict: FALSIFIED.**
RC-G0 (integrity) passed: per-seed lineage verified pre-launch, extraction
row count matched the frozen SelfAware manifest exactly, behavior cells
(known_refused n=161, known_correct_answered n=376) joined exactly into the
direction fit, binding fit metadata exact (schema
`mechinterp-residual-caution-direction/v1`, layer 35 / block 34, source
`h_lora`, construction AUROC 0.869), full coverage (537 rows / arm), and
baseline known-item over-refusal 1.0000 (>= 0.97 floor).

RC-G1 (the confirmatory call) fired the falsifier: post-ablation known-item
over-refusal landed at **0.5528**, against a registered prediction of
0.03-0.08, a 0.10 confirmation bound, and a 0.30 falsifier line. This is far
outside even the falsifier band, not merely a miss on the prediction. The
seed-1 collapse (0.994 to 0.0298, [[raw-theta-refusal-axis-ablation-rederives-archived-overrefusal-collapse]])
is seed-1-specific: **no promotion** of the 0.030-class full-ablation figure
to paper 3 section 6 or paper 5 section 6.6 occurs, and both the registered
prediction and the orchestrator's scoreboard call were wrong.

Arm table (known_refused refusal/correct; known_correct_answered
refusal/correct): baseline 1.0000/0.0000; 0.0027/0.9973. ablate
0.5528/0.2919; 0.0133/0.9255. shift_minus2 0.5590/0.3106; 0.0000/0.9628.
shift_plus2 1.0000/0.0000; 0.3617/0.6303. Specificity held throughout
(induced refusal on known_correct_answered 0.0133, correct-rate drop 7.2pp).

**Why it matters here:** the axis itself is not inert at seed 2 (ablation
releases 45.7pp of known-item refusals and lifts formerly-refused knowns
from 0% to 29.2% correct,
[[full-refusal-axis-ablation-collapse-is-seed1-specific]]), but the
near-total, ceiling-to-floor collapse the seed-1 rederivation reproduced does
not generalize. This is a clean registered null on cross-seed transfer, not
an instrument failure: RC-G0 passed on every integrity check before RC-G1
was read.

**Scope:** this cell blocks promotion of the seed-1 0.030-class figure as a
general (cross-seed) result. It does not retract the seed-1 finding itself,
which stands on its own governed source. Source of truth:
`experiments/refusal-axis-ablation-confirmatory/AMENDMENT.md`, Outcome
section, resolved 2026-08-16.
