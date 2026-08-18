---
title: contract-elicited-base-refusal-direction-is-distinct-from-trained-refusal-axis
aliases:
- the response-confidence contract does not recruit the trained refusal direction
- base-under-contract refusal direction is near-orthogonal to the trained refusal axis
- the shared trained-checkpoint refusal axis is manufactured by training, not latent in the base
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:contract-elicited-base-refusal-direction-is-distinct-from-trained-refusal-axis
  type: mechanism
  status: canonical
cause: "Fitting a refusal direction on the raw, untrained Qwen3-4B base under the response-confidence contract (P-rc, the one prompt condition where the base over-refuses) via a logistic refuse-vs-answer contrast at layer 35, then comparing it by absolute cosine, in the registered Section-5 shared-standardized frame (L2 logistic C=0.5 per checkpoint, StandardScaler fit on the pooled known-row activations of all four compared arms), to the refusal directions independently fit on three trained checkpoints (clean SFT, SFT->GRPO-DPO, SFT->GRPO-v2, same layer)."
effect: "The base-under-contract direction sits far from every trained direction: |cos| 0.0422 / 0.0522 / 0.0436 against clean SFT, SFT-GRPO-DPO, and SFT-GRPO-v2 respectively, mean 0.0460, under the pre-registered 0.20 distinct bound and roughly 2-3x the noisy single-shuffle permutation floor (base-vs-trained floor pairs mean 0.0184). The trained pairs, by contrast, cluster tightly (0.5720-0.8591, reproducing the published 0.6713/0.5762/0.8566 within 0.005). The response-confidence contract does not recruit at inference time the direction training consolidates into weights; contract-elicited refusal in the base runs through a different direction, and the shared refusal axis of the trained checkpoints is manufactured by training rather than a latent base direction the prompt merely activates."
polarity: decouples
related:
- '[[base-refusal-direction-under-contract]]'
- '[[rc-prompt-elicits-near-ceiling-abstention-from-untrained-base]]'
- '[[raw-theta-refusal-axis-ablation-rederives-archived-overrefusal-collapse]]'
- '[[refusal-directions-are-geometrically-distinct]]'
- '[[internal-paper3--knows-but-doesnt-say]]'
- '[[refusal-direction]]'
- '[[known-unknown-direction]]'
relationships:
- type: supported_by
  target: '[[base-refusal-direction-under-contract]]'
  target_id: experiment:base-refusal-direction-under-contract
  confidence: high
  evidence:
  - "experiments/base-refusal-direction-under-contract/AMENDMENT.md#outcome
    (BR-G1 DISTINCT, mean abs cosine 0.0460 <= distinct_max 0.20; BR-G0 PASS,
    1528 known-refused vs 359 known-correct-answered rows, held-out AUROC
    0.9497 / 0.9509)"
- type: related_to
  target: '[[rc-prompt-elicits-near-ceiling-abstention-from-untrained-base]]'
  target_id: mechanism:rc-prompt-elicits-near-ceiling-abstention-from-untrained-base
  confidence: high
  evidence:
  - "this mechanism's cause population (base refuse-vs-answer rows under P-rc)
    is exactly the near-ceiling abstention population that mechanism
    established; this mechanism shows the direction fit on that population is
    geometrically distinct from what training installs, so the prompt effect
    and the trained effect are not the same mechanism at the representation
    level"
- type: related_to
  target: '[[raw-theta-refusal-axis-ablation-rederives-archived-overrefusal-collapse]]'
  target_id: mechanism:raw-theta-refusal-axis-ablation-rederives-archived-overrefusal-collapse
  confidence: medium
  evidence:
  - "one of the three trained reference directions compared against here is
    the same clean_sft_grpo_v2_seed1 L35 raw-theta refusal axis that
    mechanism causally validates as the governed write-site direction on a
    trained checkpoint; this mechanism shows the base-under-contract
    direction is far from it in cosine, complementing that mechanism's
    causal-ablation account with a geometric-distinctness account"
- type: related_to
  target: '[[refusal-directions-are-geometrically-distinct]]'
  target_id: mechanism:refusal-directions-are-geometrically-distinct
  confidence: medium
  evidence:
  - "shares the broader caution against a single universal refusal direction;
    this mechanism is a within-program, within-checkpoint-family instance of
    that caveat, contrasting a prompt-elicited base direction against
    training-installed directions on the same model lineage rather than
    across unrelated refusal categories"
- type: related_to
  target: '[[internal-paper3--knows-but-doesnt-say]]'
  target_id: paper:internal-paper3
  confidence: high
  evidence:
  - "answers the direct test paper 3 Section 5 explicitly queued and left
    unrun at registration; sharpens that section's trained-checkpoint-
    construct claim for the refusal axis"
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

The response-confidence contract makes the untrained Qwen3-4B base over-refuse
at near-ceiling rates, but the direction that behavior runs through in
activation space is not the direction post-training later consolidates. A
refusal direction fit on the raw base under this contract reads |cos| 0.0422,
0.0522, and 0.0436 against the refusal directions of three independently
trained checkpoints (clean SFT, SFT->GRPO-DPO, SFT->GRPO-v2), mean 0.0460,
close to orthogonal and only marginally above a noisy permutation floor
(mean 0.0184). The three trained directions, measured against each other in
the same frame, cluster at 0.5720-0.8591: they share an axis with one
another that the base-under-contract direction does not share with any of
them.

**Why it matters here:** this was the direct, previously unrun test paper 3
Section 5 queued: whether a refusal direction fit on the base under the
response-confidence contract points where the trained checkpoints' shared
refusal axis points. The distinct result sharpens the trained-construct
reading, the shared axis is something training builds, not a latent base
direction the contract activates at inference time.

**Recorded caveats:** the base arm's negative class is known-correct-answered
only (no known-answered-wrong rows exist in the base P-rc source
extraction, a property of the data); the permutation floor is a single
shuffle per arm, noisy by construction; single seed, exploratory tier.

**Lineage:** established in [[base-refusal-direction-under-contract]],
resolved 2026-08-18. Source of truth:
`experiments/base-refusal-direction-under-contract/AMENDMENT.md`, Outcome
section.
