---
title: readout-under-contract-crossing
aliases:
- Known-unknown readout under a change of prompt contract
- does the internal known-unknown direction survive a change of prompt contract
- RU-G0/RU-G1 contract-crossing probe transfer cell
tags:
- kg/experiment
- experiment
- abstention
kg:
  id: experiment:readout-under-contract-crossing
  type: experiment
  status: canonical
related:
- '[[prompt-vs-training-panel]]'
- '[[internal-paper3--knows-but-doesnt-say]]'
- '[[base-refusal-direction-under-contract]]'
- '[[known-unknown-direction]]'
- '[[known-unknown-direction-transfers-partially-across-prompt-contracts]]'
- '[[post-training-shrinks-known-unknown-contract-sensitivity]]'
relationships:
- type: builds_on
  target: '[[prompt-vs-training-panel]]'
  target_id: experiment:prompt-vs-training-panel
  confidence: high
  evidence:
  - "experiments/readout-under-contract-crossing/AMENDMENT.md Design (the three
    contract renders, P-rc, P-plain, P-struct, resolve byte-identically from
    the pinned prompt-vs-training-panel configs listed in inputs)"
- type: builds_on
  target: '[[internal-paper3--knows-but-doesnt-say]]'
  target_id: paper:internal-paper3
  confidence: high
  evidence:
  - "experiments/readout-under-contract-crossing/AMENDMENT.md Motivation and
    posture (paper 3 Section 9 flags the internal known-unknown readout,
    the paper's first result, as measured under the neutral extraction
    prompt only, and asks whether it survives a change of contract; this
    cell's RU-G0 stage parity-checks each checkpoint's Stage-0 neutral-prompt
    reading against the published Section-4 AUROC, 0.9914 vs 0.997 base,
    0.9905 vs 0.9968 clean_sft_merged, 0.9900 vs 0.9971 sft_grpo_v2, all
    within 0.0071)"
- type: supports
  target: '[[known-unknown-direction-transfers-partially-across-prompt-contracts]]'
  target_id: mechanism:known-unknown-direction-transfers-partially-across-prompt-contracts
  confidence: high
  evidence:
  - "experiments/readout-under-contract-crossing/AMENDMENT.md#outcome (RU-G1
    table: nine checkpoint-contract pairs, P-rc and P-struct transfer 0.8860-0.9286
    against refit 0.9881-0.9939, drop 0.0614-0.1054; P-plain transfer 0.9996-0.9997
    on all three checkpoints; no pair rotated, transfer < 0.85, or suppressed,
    refit < 0.90)"
- type: supports
  target: '[[post-training-shrinks-known-unknown-contract-sensitivity]]'
  target_id: mechanism:post-training-shrinks-known-unknown-contract-sensitivity
  confidence: high
  evidence:
  - "experiments/readout-under-contract-crossing/AMENDMENT.md#outcome (Reading:
    P-rc drop 0.1054 base, 0.0789 clean-SFT, 0.0614 SFT->GRPO-v2; P-struct drop
    0.0815 base, 0.0760 clean-SFT, 0.0633 SFT->GRPO-v2, monotonic across the
    training progression)"
- type: related_to
  target: '[[known-unknown-direction]]'
  target_id: term:known-unknown-direction
  confidence: high
  evidence:
  - "experiments/readout-under-contract-crossing/AMENDMENT.md Design (Stage 2
    projects contract-conditioned activations onto each checkpoint's Stage-0
    neutral-prompt known-unknown direction)"
- type: related_to
  target: '[[base-refusal-direction-under-contract]]'
  target_id: experiment:base-refusal-direction-under-contract
  confidence: medium
  evidence:
  - "experiments/readout-under-contract-crossing/AMENDMENT.md Compute and
    sequencing (may share the slot with base-refusal-direction-under-contract;
    both cells test whether a direction fit under one prompt condition points
    where a direction fit or transferred under another does, one for the
    known-unknown axis and one for the refusal axis)"
---

Exploratory (single seed, Qwen3-4B lineage) probe-transfer cell testing
whether the internal known-unknown readout survives a change of prompt
contract. Three checkpoints (raw base, clean-SFT merged, SFT->GRPO-v2) times
three non-neutral contracts (P-rc, P-plain, P-struct), same SelfAware rows,
same L35 last-prompt-token stack as the paper-3 Section-4 reading; no
generation anywhere, known/unknown labels are dataset properties.

Resolved 2026-08-18: **PARTIAL TRANSFER**. The prediction (all nine pairs
invariant, drop <= 0.05) did not hold; the falsifier (any pair rotated or
suppressed) did not fire. RU-G0 passed on all three checkpoints (12/12
extractions, 3,369 rows each, neutral 5-fold out-of-fold AUROC within 0.0071
of the published Section-4 reading). RU-G1: the readout itself is present
under every contract, in-contract refit recovers 0.9881-0.9939 everywhere.
The neutral-prompt direction transfers exactly to P-plain (0.9996-0.9997 on
all three checkpoints) but drops 0.0614-0.1054 AUROC under P-rc and
0.0633-0.0815 under P-struct on all three checkpoints. Training monotonically
shrinks the contract-sensitivity gradient (P-rc 0.1054 base -> 0.0789
clean-SFT -> 0.0614 SFT->GRPO-v2; P-struct 0.0815 -> 0.0760 -> 0.0633); the
raw base is the most contract-sensitive checkpoint, not the least, contrary
to the orchestrator's pre-registered call.

**Why it matters here:** paper 3 Section 9 flagged this as untested: the
near-ceiling internal known-unknown readout, the paper's first result, was
measured under the neutral extraction prompt only. This cell converts that
open question into a measured, partial result: the internal-vs-stated gap's
premise (an internal signal exists) hardens, since refitting recovers the
signal under every contract, but the specific neutral-prompt direction is
not contract-invariant. The Section-4 invariance upgrade, registered as
conditional on all-nine-invariant, does not trigger.

**Lineage:** reuses the pinned prompt contract renders from
[[prompt-vs-training-panel]]; parity-checks against the paper-3 Section-4
near-ceiling reading. Source of truth:
`experiments/readout-under-contract-crossing/AMENDMENT.md`, Outcome section,
resolved 2026-08-18.
