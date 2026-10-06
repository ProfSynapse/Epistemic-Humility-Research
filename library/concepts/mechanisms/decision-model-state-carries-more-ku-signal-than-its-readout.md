---
title: decision-model-state-carries-more-ku-signal-than-its-readout
aliases:
- The decision model answer state carries more known-unknown signal than its confidence reports
- Fresh KU probe beats the decision readout (dmcc H-D2)
- Decision-model readout lags its internal known-unknown signal
- Knows more than it says, in a model that cannot refuse
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:decision-model-state-carries-more-ku-signal-than-its-readout
  type: mechanism
  status: canonical
  recorded_at: 2026-10-05
cause: "In the decision-model-calibrated-choice experiment, a fresh known-unknown linear probe (PCA then logistic, layer sweep on FIT) is fit on the decision model's own <answer> hidden states (Qwen3.5-2B-Base torso, LoRA r16 + pointer head, PopQA 4-way choice) and compared on TEST (514 known / 4,314 unknown) with the model's calibrated option confidence R1, by an engine paired bootstrap; the frozen base gate direction is compared with R1 the same way."
effect: "The probe (layer 15) reads known vs unknown at AUROC 0.9916 [0.9886, 0.9941] and beats R1 (0.9407) by +0.0509 [0.0393, 0.0639] (H-D2 PASS against +0.03 with CI lower bound above 0; engine permuted-label control 0.4776, inside [0.40, 0.60]). The frozen base direction also beats R1, by +0.0355 [0.0245, 0.0482], meeting the registered +0.03 reading on the primary pointer arm. Secondary letter-logit arm: probe minus R1 +0.0408 [0.0322, 0.0500] (PASS); base direction minus R1 +0.0211 [0.0125, 0.0300], CI excludes 0 but the point is below +0.03, so the registered reading is not met there."
polarity: limits
related:
- '[[decision-model-calibrated-choice]]'
- '[[decision-model-readout-tracks-base-known-unknown-axis]]'
- '[[known-unknown-direction]]'
- '[[linear-probe]]'
- '[[auroc]]'
- '[[verbalized-confidence-channel-bottleneck]]'
- '[[internal-paper3--knows-but-doesnt-say]]'
relationships:
- type: supported_by
  target: '[[decision-model-calibrated-choice]]'
  target_id: experiment:decision-model-calibrated-choice
  confidence: high
  evidence:
  - experiments/decision-model-calibrated-choice/analysis-committed/dmcc-pointer-popqa_gate_summary.json
    (H-D2; H-D1 comparison with R1)
  - experiments/decision-model-calibrated-choice/analysis-committed/dmcc-letter-logits-popqa_gate_summary.json
    (secondary arm)
  - experiments/decision-model-calibrated-choice/AMENDMENT.md#outcome (Stage 1
    gate results; H-D2 detail; H-D1 registered comparison with the readout)
- type: related_to
  target: '[[decision-model-readout-tracks-base-known-unknown-axis]]'
  target_id: mechanism:decision-model-readout-tracks-base-known-unknown-axis
  confidence: high
  evidence:
  - experiments/decision-model-calibrated-choice/AMENDMENT.md#outcome
    (Interpretation matrix; H-D2 qualifies the matrix cell without moving it)
- type: related_to
  target: '[[known-unknown-direction]]'
  target_id: term:known-unknown-direction
  confidence: high
- type: related_to
  target: '[[linear-probe]]'
  target_id: method:linear-probe
  confidence: high
- type: related_to
  target: '[[auroc]]'
  target_id: metric:auroc
  confidence: high
- type: related_to
  target: '[[verbalized-confidence-channel-bottleneck]]'
  target_id: mechanism:verbalized-confidence-channel-bottleneck
  confidence: medium
  evidence:
  - experiments/decision-model-calibrated-choice/AMENDMENT.md (Motivation and
    posture; whether a probe still sees more than a non-verbalized readout says)
- type: related_to
  target: '[[internal-paper3--knows-but-doesnt-say]]'
  target_id: paper:internal-paper3
  confidence: medium
  evidence:
  - experiments/decision-model-calibrated-choice/AMENDMENT.md (Motivation and
    posture; paper 3's represented-but-not-reported contrast, context only, not
    a matched comparison)
---

Even when the decision readout ranks knowledge well (AUROC 0.94), a linear
probe on the same `<answer>` state ranks it better (0.99), by +0.05 with a CI
that excludes 0. On the primary arm the base model's frozen KU direction also
beats the readout by the registered margin (+0.036). The decision model's state
carries more known-unknown signal than its calibrated confidence expresses.

**Why it matters here:** this is a much smaller version of paper 3's
"knows but doesn't say" gap ([[internal-paper3--knows-but-doesnt-say]]), seen
in a model with no refusal and no verbalized channel. In paper 3 the stated
channel sits near chance; here the readout is strong and lags only by about
0.05 AUROC. Removing the verbalized channel closes most of the gap on this
model but not all of it.

**Caveats:** exploratory tier-2, single seed per arm, one 2B model, PopQA 4-way
multiple choice; a different family, size and population from paper 3, so the
two gaps are never differenced. On the secondary letter-logit arm the base
direction's margin over R1 (+0.0211) misses the +0.03 reading. Source of
truth: `experiments/decision-model-calibrated-choice/AMENDMENT.md` (Outcome),
resolved 2026-10-05.
