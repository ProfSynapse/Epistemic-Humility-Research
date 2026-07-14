---
aliases:
- wide-instrument baseline abstention differs by model family
- baseline hedging under the wide instrument is not a single constant
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:undosed-wide-instrument-baseline-abstention-is-family-graded
  type: mechanism
  status: canonical
cause: "The wide two-instrument abstention stack (detector v2 screen plus blinded context-free adjudication, pins byte-identical to RR2) is applied to the UNDOSED baseline arm of three model families' fired-confab pools: Qwen3.5-4B at its promoted heldout operating point, Llama-3.2-3B-Instruct's cross-family raw-refusal staged rows, and Mistral-7B-Instruct-v0.3 (cited from RR2), with no write applied in any case."
effect: "Baseline confab abstention reads 139/1332 = 0.104 (Wilson 95% [0.089, 0.122]) for qwen, 239/1453 = 0.164 [0.146, 0.184] for llama, and 368/1312 = 0.280 [0.257, 0.305] for mistral: a genuinely graded, non-overlapping gradient across families rather than a single wide-instrument constant. Known-population (cost) rates read 0 everywhere covered on every family. This generalizes `wide-abstention-instrument-reveals-substantial-undosed-baseline-refusal`, established for mistral alone, to two additional families and shows the substantial-undosed-baseline finding is a family-graded property, not a mistral-specific artifact."
polarity: increases
related:
- '[[abstention-wide-instrument-calibration]]'
- '[[wide-abstention-instrument-reveals-substantial-undosed-baseline-refusal]]'
- '[[abstention]]'
relationships:
- type: supported_by
  target: '[[abstention-wide-instrument-calibration]]'
  target_id: experiment:abstention-wide-instrument-calibration
  confidence: high
  evidence:
  - experiments/abstention-wide-instrument-calibration/AMENDMENT.md#outcome (Calibration table, Wide baseline column)
- type: related_to
  target: '[[wide-abstention-instrument-reveals-substantial-undosed-baseline-refusal]]'
  target_id: mechanism:wide-abstention-instrument-reveals-substantial-undosed-baseline-refusal
  confidence: high
- type: related_to
  target: '[[abstention]]'
  target_id: term:abstention
  confidence: medium
---

A cross-family generalization of `wide-abstention-instrument-reveals-substantial-undosed-baseline-refusal`,
which established a substantial undosed baseline only for mistral. Measuring
qwen and llama with the identical wide instrument shows the baseline is not
merely "substantial for mistral" but genuinely graded across all three
families measured (0.104 / 0.164 / 0.280), with non-overlapping confidence
intervals. This is the direct evidentiary basis for the family-specificity
reading in `abstention-wide-instrument-calibration`'s resolved verdict: the
RR2 placebo failure is a family property, not a universal wide-instrument
artifact, because the undosed baseline itself already varies by family before
any placebo write is applied.
