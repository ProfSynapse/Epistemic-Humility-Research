---
aliases:
- output-distribution constraint prevents interference propagation
- distillation stabilizes hidden-state trajectories
- KL regularization blocks entity-representation corruption
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:self-distillation-suppresses-representational-drift
  type: mechanism
  status: canonical
cause: "SFT self-distillation constraint (KL penalty toward frozen teacher output distribution) during fine-tuning on semantically overlapping new facts"
effect: "Layer-14 cosine drift of held-out entity representations stabilizes near the task-format-learning plateau (approximately 5%) rather than continuing to approximately 11% under unconstrained SFT, with resulting forgetting reduced from approximately 15% to approximately 3%"
polarity: prevents
related:
- '[[2604.15574--why-finetuning-encourages-hallucinations]]'
- '[[sft-self-distillation]]'
- '[[semantic-overlap-drives-sft-forgetting]]'
- '[[supervised-finetuning]]'
- '[[factual-plasticity-stability-tradeoff]]'
- '[[hallucination]]'
relationships:
- type: supported_by
  target: '[[2604.15574--why-finetuning-encourages-hallucinations]]'
  target_id: paper:2604.15574
  confidence: high
- type: related_to
  target: '[[sft-self-distillation]]'
  target_id: method:sft-self-distillation
  confidence: high
- type: related_to
  target: '[[semantic-overlap-drives-sft-forgetting]]'
  target_id: mechanism:semantic-overlap-drives-sft-forgetting
  confidence: high
- type: related_to
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
  confidence: high
- type: related_to
  target: '[[factual-plasticity-stability-tradeoff]]'
  target_id: term:factual-plasticity-stability-tradeoff
  confidence: high
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
  confidence: high
---

Self-distillation on semantic-overlap entities produces the same approximately 5% residual hidden-state drift as UUID-key SFT, despite training on lexically similar entity names. L2 weight regularization matched in gradient magnitude fails to replicate this: it leaves forgetting near 10 percentage points, demonstrating that the mechanism is not generic weight-magnitude suppression. The output-distribution constraint specifically prevents gradient updates for overlapping new entities from propagating through shared representational regions, which is the pathway identified as the driver of forgetting by the semantic-vs-UUID contrast.
