---
aliases:
- AH-UH refusal generalization failure
- refusal tuning type mismatch
- hallucination-type refusal barrier
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:refusal-tuning-fails-to-generalize-across-hallucination-types
  type: mechanism
  status: canonical
cause: "UHs occupy a common activation subspace across different subjects (because they share weak subject-information propagation), while AHs have diverse, subject-specific hidden-state geometries that vary across examples."
effect: "Refusal tuning trained on UH samples generalizes within the UH category (82% refusal ratio on held-out UHs, LLaMA-3-8B) but fails to transfer to AH samples (28% refusal ratio) and introduces spurious refusals on FAs (29.5%). Refusal tuning on AH samples is worse in both directions: only 33% refusal on AH test samples and 23.5% on UH test samples."
polarity: prevents
related:
- '[[2510.09033--probes-read-recall-not-truth]]'
- '[[ah-uh-hallucination-taxonomy]]'
- '[[associated-hallucination]]'
- '[[unassociated-hallucination]]'
- '[[abstention-generalization-failure]]'
- '[[sft-abstention-overfits-indomain]]'
- '[[extended-refusal-fine-tuning-disperses-safety-signal]]'
- '[[refusal-aware-instruction-tuning]]'
relationships:
- type: supported_by
  target: '[[2510.09033--probes-read-recall-not-truth]]'
  target_id: paper:2510.09033
  confidence: high
- type: related_to
  target: '[[ah-uh-hallucination-taxonomy]]'
  target_id: term:ah-uh-hallucination-taxonomy
  confidence: high
- type: related_to
  target: '[[associated-hallucination]]'
  target_id: term:associated-hallucination
  confidence: high
- type: related_to
  target: '[[unassociated-hallucination]]'
  target_id: term:unassociated-hallucination
  confidence: high
- type: related_to
  target: '[[abstention-generalization-failure]]'
  target_id: mechanism:abstention-generalization-failure
  confidence: high
- type: related_to
  target: '[[sft-abstention-overfits-indomain]]'
  target_id: mechanism:sft-abstention-overfits-indomain
  confidence: high
- type: related_to
  target: '[[extended-refusal-fine-tuning-disperses-safety-signal]]'
  target_id: mechanism:extended-refusal-fine-tuning-disperses-safety-signal
  confidence: high
- type: related_to
  target: '[[refusal-aware-instruction-tuning]]'
  target_id: method:refusal-aware-instruction-tuning
  confidence: high
---

Because UH samples share a geometrically coherent activation subspace, a model fine-tuned to refuse on UH examples can learn a consistent decision boundary and apply it to held-out UHs. AH activations are spread across subject-specific regions of representation space, so no compact refusal boundary generalizes across them. The cross-type failure is symmetric but asymmetric in degree: UH-trained models partially generalize to UHs but not AHs; AH-trained models fail substantially in both directions. This implies that refusal-tuning datasets must be stratified by hallucination type, and that a single refusal-tuned model cannot be reliable across both AH and UH inputs without architecturally separate detection mechanisms.
