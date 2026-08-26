---
title: post-training-shrinks-known-unknown-contract-sensitivity
aliases:
- training monotonically shrinks the known-unknown contract-transfer drop
- base is the most contract-sensitive checkpoint, not the least
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:post-training-shrinks-known-unknown-contract-sensitivity
  type: mechanism
  status: canonical
cause: "Post-training progression across the three readout-under-contract-crossing checkpoints in fixed order: raw base, then clean-SFT (merged), then SFT->GRPO-v2, holding contract, layer (L35), extraction stack, and rows fixed."
effect: "The transfer-AUROC drop of each checkpoint's own neutral-prompt known-unknown direction under the P-rc and P-struct contracts shrinks monotonically across that training progression: P-rc drop 0.1054 (base) to 0.0789 (clean-SFT) to 0.0614 (SFT->GRPO-v2); P-struct drop 0.0815 (base) to 0.0760 (clean-SFT) to 0.0633 (SFT->GRPO-v2). The gradient runs opposite the readout-under-contract-crossing orchestrator's pre-registered prediction, which called the raw base the least contract-sensitive checkpoint and GRPO-v2 P-rc the likeliest partial pair; the base is instead the most contract-sensitive checkpoint on both non-plain contracts."
polarity: decreases
coefficient: 0.044
coefficient_units: "AUROC points, P-rc contract-sensitivity drop shrinkage from base to SFT->GRPO-v2 (0.1054 to 0.0614)"
coefficient_source: "experiments/readout-under-contract-crossing/AMENDMENT.md RU-G1 table and Reading section"
related:
- '[[readout-under-contract-crossing]]'
- '[[known-unknown-direction-transfers-partially-across-prompt-contracts]]'
- '[[known-unknown-direction]]'
- '[[only-sft-installs-abstention-in-weights]]'
relationships:
- type: supported_by
  target: '[[readout-under-contract-crossing]]'
  target_id: experiment:readout-under-contract-crossing
  confidence: high
  evidence:
  - "experiments/readout-under-contract-crossing/AMENDMENT.md#outcome (Reading
    section, per-checkpoint drop gradient; Predictions scoreboard adjudication,
    orchestrator call reversed)"
- type: related_to
  target: '[[known-unknown-direction-transfers-partially-across-prompt-contracts]]'
  target_id: mechanism:known-unknown-direction-transfers-partially-across-prompt-contracts
  confidence: high
  evidence:
  - "experiments/readout-under-contract-crossing/AMENDMENT.md#outcome (same
    RU-G1 per-pair drops, read across checkpoints instead of across contracts)"
- type: related_to
  target: '[[known-unknown-direction]]'
  target_id: term:known-unknown-direction
  confidence: high
- type: related_to
  target: '[[only-sft-installs-abstention-in-weights]]'
  target_id: mechanism:only-sft-installs-abstention-in-weights
  confidence: medium
  evidence:
  - "experiments/readout-under-contract-crossing/AMENDMENT.md#outcome (both
    mechanisms describe post-training changing something about the
    checkpoint's relationship to prompt contract, one for behavioral
    abstention internalization, this one for the internal direction's
    contract-geometry stability)"
---

Across the three readout-under-contract-crossing checkpoints, ordered by
training stage, the AUROC penalty for projecting a checkpoint's own
neutral-prompt known-unknown direction into the P-rc or P-struct contract
shrinks monotonically as training accumulates. The raw base, not the most
trained checkpoint, is the most contract-sensitive: post-training stages
(clean-SFT, then SFT->GRPO-v2) make the internal direction's geometry
progressively more stable across prompt contracts, even though the readout
itself is already near ceiling at every stage under in-contract refit.

**Why it matters here:** this reverses the orchestrator's pre-registered call
(invariant on base and clean-SFT, GRPO-v2 P-rc the likeliest partial pair)
and sharpens the readout-under-contract-crossing result from a flat partial
verdict into a directional training effect: whatever post-training does to
the representation, it includes making the known-unknown direction less
contract-dependent, not just preserving or degrading it.

**Lineage:** established in [[readout-under-contract-crossing]], resolved
2026-08-18, single seed, Qwen3-4B lineage. Source of truth:
`experiments/readout-under-contract-crossing/AMENDMENT.md`, Outcome section
(Reading and Predictions scoreboard adjudication).
