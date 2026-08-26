---
title: known-unknown-direction-transfers-partially-across-prompt-contracts
aliases:
- the neutral-prompt known-unknown direction survives P-plain but not P-rc/P-struct
- contract-crossing partial transfer, no rotation, no suppression
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:known-unknown-direction-transfers-partially-across-prompt-contracts
  type: mechanism
  status: canonical
cause: "Projecting each checkpoint's neutral-extraction-prompt known-unknown direction (fit at L35, RU-G0 parity-checked against the paper-3 Section-4 reading within 0.0071 AUROC) onto activations gathered under the P-rc and P-struct prompt contracts instead of the neutral contract it was fit under, versus refitting a fresh cross-validated in-contract probe on those same P-rc/P-struct activations."
effect: "The neutral-prompt direction's transfer AUROC drops 0.0614-0.1054 below its checkpoint's in-contract refit AUROC (which itself stays 0.9881-0.9939, near ceiling) under P-rc and P-struct on all three checkpoints (base, clean-SFT, SFT->GRPO-v2). Under the P-plain contract the same direction transfers with no drop, 0.9996-0.9997 on all three checkpoints. No pair rotates (transfer < 0.85 with refit >= 0.95) or is suppressed (transfer < 0.85 with refit < 0.90) against the readout-under-contract-crossing RU-G1 gate."
polarity: decreases
coefficient: 0.1054
coefficient_units: "AUROC points, largest single-pair transfer drop (base checkpoint, P-rc contract) relative to its own in-contract refit"
coefficient_source: "experiments/readout-under-contract-crossing/AMENDMENT.md RU-G1 table"
related:
- '[[readout-under-contract-crossing]]'
- '[[known-unknown-direction]]'
- '[[prompt-vs-training-panel]]'
- '[[post-training-shrinks-known-unknown-contract-sensitivity]]'
- '[[context-invariance]]'
relationships:
- type: supported_by
  target: '[[readout-under-contract-crossing]]'
  target_id: experiment:readout-under-contract-crossing
  confidence: high
  evidence:
  - "experiments/readout-under-contract-crossing/AMENDMENT.md#outcome (RU-G1
    per-pair band table, verdict PARTIAL TRANSFER)"
- type: related_to
  target: '[[known-unknown-direction]]'
  target_id: term:known-unknown-direction
  confidence: high
- type: related_to
  target: '[[prompt-vs-training-panel]]'
  target_id: experiment:prompt-vs-training-panel
  confidence: medium
  evidence:
  - "experiments/readout-under-contract-crossing/AMENDMENT.md Design (the
    P-rc/P-plain/P-struct contract renders are the same byte-identical
    configs prompt-vs-training-panel pinned)"
- type: related_to
  target: '[[post-training-shrinks-known-unknown-contract-sensitivity]]'
  target_id: mechanism:post-training-shrinks-known-unknown-contract-sensitivity
  confidence: high
  evidence:
  - "experiments/readout-under-contract-crossing/AMENDMENT.md#outcome (Reading:
    same nine per-pair drops, read across checkpoints instead of across
    contracts, describe the training gradient in the paired mechanism)"
- type: related_to
  target: '[[context-invariance]]'
  target_id: term:context-invariance
  confidence: medium
  evidence:
  - "experiments/readout-under-contract-crossing/AMENDMENT.md Motivation and
    posture (tests whether the internal known-unknown readout, not just
    behavioral abstention, is contract-invariant)"
---

The known-unknown direction fit under the neutral extraction prompt does not
generalize uniformly across prompt contracts. Refitting in-contract recovers
the readout almost exactly everywhere (0.9881-0.9939 AUROC), so the
underlying signal is present regardless of contract. But the specific
neutral-prompt direction transfers exactly only to the P-plain contract
(0.9996-0.9997) and loses 0.06-0.11 AUROC when projected under P-rc or
P-struct instead. The geometry of the direction, not the presence of the
signal, is what a change of contract disturbs.

**Why it matters here:** this is the first direct measurement of paper 3
Section 9's open conditionality question for the internal known-unknown
readout specifically (as opposed to behavioral abstention, which
[[prompt-vs-training-panel]] already showed is prompt-carried at the base).
It keeps the internal-vs-stated gap's premise intact (an internal signal
exists under every contract) while showing the fitted direction itself is
contract-sensitive, not contract-invariant.

**Lineage:** established in [[readout-under-contract-crossing]], resolved
2026-08-18, single seed, Qwen3-4B lineage. Source of truth:
`experiments/readout-under-contract-crossing/AMENDMENT.md`, Outcome section.
