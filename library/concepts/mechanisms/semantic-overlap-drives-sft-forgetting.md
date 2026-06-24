---
aliases:
- representational interference drives forgetting
- surface-form similarity causes factual forgetting
- structural interference account of hallucination
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:semantic-overlap-drives-sft-forgetting
  type: mechanism
  status: canonical
cause: "SFT updates for new facts whose entity names share token substrings with pre-trained entity representations"
effect: "Cosine drift in held-out entity hidden states (layer 14) continuing beyond the task-format-learning plateau, producing forgetting that scales with the number of semantically overlapping new facts but remains near-zero (0-4%) for syntactically isolated UUID-style entities even at 1M new facts"
polarity: increases
related:
- '[[2604.15574--why-finetuning-encourages-hallucinations]]'
- '[[sft-unknown-examples-drive-hallucination]]'
- '[[supervised-finetuning]]'
- '[[hallucination]]'
- '[[factual-plasticity-stability-tradeoff]]'
- '[[sft-self-distillation]]'
relationships:
- type: supported_by
  target: '[[2604.15574--why-finetuning-encourages-hallucinations]]'
  target_id: paper:2604.15574
  confidence: high
- type: related_to
  target: '[[sft-unknown-examples-drive-hallucination]]'
  target_id: mechanism:sft-unknown-examples-drive-hallucination
  confidence: high
- type: related_to
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
  confidence: high
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
  confidence: high
- type: related_to
  target: '[[factual-plasticity-stability-tradeoff]]'
  target_id: term:factual-plasticity-stability-tradeoff
  confidence: high
- type: related_to
  target: '[[sft-self-distillation]]'
  target_id: method:sft-self-distillation
  confidence: high
---

When synthetic entities are constructed by recombining tokens from real location names (semantic keys), introducing them via SFT causes held-out HighlyKnown accuracy to drop sharply with scale while UUID-key SFT of the same scale produces near-zero forgetting. Layer-14 cosine drift rises to 5% in all conditions during task-format learning then continues to 11% only under semantic-key SFT, implicating shared representational neighborhoods as the interference pathway. This asymmetric scaling pattern rules out both capacity-limited accounts (which predict uniform degradation with scale) and behavioral cloning accounts (which predict forgetting whenever Unknown examples are present regardless of surface form).
