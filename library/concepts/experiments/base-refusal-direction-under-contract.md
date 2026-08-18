---
title: base-refusal-direction-under-contract
aliases:
- Base refusal direction under the response-confidence contract
- does a contract-elicited base refusal direction point where trained checkpoints' refusal axis points
tags:
- kg/experiment
- experiment
- abstention
kg:
  id: experiment:base-refusal-direction-under-contract
  type: experiment
  status: canonical
related:
- '[[rc-prompt-elicits-near-ceiling-abstention-from-untrained-base]]'
- '[[prompt-vs-training-panel]]'
- '[[internal-paper3--knows-but-doesnt-say]]'
- '[[contract-elicited-base-refusal-direction-is-distinct-from-trained-refusal-axis]]'
- '[[raw-theta-refusal-axis-ablation-rederives-archived-overrefusal-collapse]]'
- '[[refusal-direction]]'
- '[[known-unknown-direction]]'
relationships:
- type: builds_on
  target: '[[rc-prompt-elicits-near-ceiling-abstention-from-untrained-base]]'
  target_id: mechanism:rc-prompt-elicits-near-ceiling-abstention-from-untrained-base
  confidence: high
  evidence:
  - "experiments/base-refusal-direction-under-contract/AMENDMENT.md Motivation
    and posture (the enabling fact registered for this cell: the resolved
    prompt-vs-training-panel cell showed the response-confidence contract
    alone elicits near-ceiling abstention from the untrained base, refusal
    recall 90.89, over-refusal 65.38% of answerables, exactly the
    refuse-versus-answer population a direction fit needs)"
- type: builds_on
  target: '[[prompt-vs-training-panel]]'
  target_id: experiment:prompt-vs-training-panel
  confidence: high
  evidence:
  - "experiments/base-refusal-direction-under-contract/experiment.yaml inputs
    (Stage 1 known-refused vs known-answered labels join from the governed
    retained scored_rows of the resolved prompt-vs-training-panel cell's base
    P-rc arm, SelfAware n=3369; no fresh generation in this cell)"
- type: related_to
  target: '[[internal-paper3--knows-but-doesnt-say]]'
  target_id: paper:internal-paper3
  confidence: high
  evidence:
  - "experiments/base-refusal-direction-under-contract/AMENDMENT.md Motivation
    and posture (paper 3 Section 5 rules the refusal axis a trained-checkpoint
    construct under the neutral extraction prompt and explicitly queues this
    cell as the direct, unrun test of whether a base-under-contract direction
    points where the trained checkpoints' refusal axis points)"
- type: supports
  target: '[[contract-elicited-base-refusal-direction-is-distinct-from-trained-refusal-axis]]'
  target_id: mechanism:contract-elicited-base-refusal-direction-is-distinct-from-trained-refusal-axis
  confidence: high
  evidence:
  - "experiments/base-refusal-direction-under-contract/AMENDMENT.md#outcome
    (BR-G1 DISTINCT, mean abs cosine 0.0460 under the 0.20 distinct bound)"
- type: related_to
  target: '[[raw-theta-refusal-axis-ablation-rederives-archived-overrefusal-collapse]]'
  target_id: mechanism:raw-theta-refusal-axis-ablation-rederives-archived-overrefusal-collapse
  confidence: medium
  evidence:
  - "experiments/base-refusal-direction-under-contract/experiment.yaml inputs
    (Stage 4 re-derives the three trained-regimen refusal directions, one of
    them the same clean_sft_grpo_v2_seed1 L35 refusal axis this mechanism
    established, via the committed Section 5 provenance reconstruction
    script over its pinned archived inputs)"
- type: related_to
  target: '[[refusal-direction]]'
  target_id: term:refusal-direction
  confidence: high
- type: related_to
  target: '[[known-unknown-direction]]'
  target_id: term:known-unknown-direction
  confidence: medium
  evidence:
  - "experiments/base-refusal-direction-under-contract/AMENDMENT.md#outcome
    (Stage 5 descriptive |cos| to the known-unknown axis as an orthogonality
    check on the fitted base refusal direction)"
---

Exploratory (single seed, Qwen3-4B) probe-fit cell that fits a refusal
direction on the raw base under the response-confidence contract (P-rc, the
one prompt condition where the untrained base over-refuses) and compares it
by absolute cosine, in the registered Section-5 shared-standardized frame, to
the refusal directions independently fit on three trained checkpoints (clean
SFT, SFT->GRPO-DPO, SFT->GRPO-v2, layer 35). No fresh generation: Stage 1
labels reuse the governed retained rows of the resolved
prompt-vs-training-panel cell's base P-rc arm; Stage 2 extracts L35 hidden
states for the raw base under the same byte-identical render.

Resolved 2026-08-18: DISTINCT, prediction falsified. The aligned prediction
(mean |cos| >= 0.50) was not met; mean |cos| landed at 0.0460
(0.0422/0.0522/0.0436 against clean SFT, SFT-GRPO-DPO, and SFT-GRPO-v2
respectively), under the 0.20 distinct bound, roughly 2-3x the noisy
single-shuffle permutation floor (mean 0.0184) and far below the trained-pair
cluster (0.5720-0.8591). BR-G0 fit-integrity gate passed cleanly: 1,528
known-refused vs 359 known-correct-answered rows, held-out AUROC 0.9497 first
pass / 0.9509 redo, both instrument passes agreeing to within 0.005 of the
published trained-pair cosines. Single seed, exploratory tier, reported
separately from any headline.

**Why it matters here:** this cell is the direct, previously unrun test paper
3 Section 5 explicitly queued. The distinct result sharpens rather than
weakens that section's trained-construct claim: the shared refusal axis of
the trained checkpoints is manufactured by training, not a latent base
direction the response-confidence contract merely activates. The contract
elicits near-ceiling base abstention ([[rc-prompt-elicits-near-ceiling-abstention-from-untrained-base]])
through a mechanism geometrically distinct from what training installs.

**Lineage:** builds on `prompt-vs-training-panel`'s base P-rc retained rows
and the enabling fact it established. Source of truth:
`experiments/base-refusal-direction-under-contract/AMENDMENT.md`, Outcome
section, resolved 2026-08-18; `experiments/base-refusal-direction-under-contract/experiment.yaml`.
