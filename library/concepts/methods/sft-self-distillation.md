---
aliases:
- self-distillation for SFT
- learning without forgetting SFT
- output-distribution regularization SFT
tags:
- kg/method
- concept
- method
kg:
  id: method:sft-self-distillation
  type: method
  status: canonical
area: methods
related:
- '[[2604.15574--why-finetuning-encourages-hallucinations]]'
- '[[supervised-finetuning]]'
- '[[slick]]'
- '[[sft-unknown-examples-drive-hallucination]]'
- '[[hallucination]]'
- '[[knowledge-boundary]]'
relationships:
- type: proposed_by
  target: '[[2604.15574--why-finetuning-encourages-hallucinations]]'
  target_id: paper:2604.15574
  confidence: high
- type: related_to
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
  confidence: medium
- type: related_to
  target: '[[slick]]'
  target_id: method:slick
  confidence: medium
- type: related_to
  target: '[[sft-unknown-examples-drive-hallucination]]'
  target_id: mechanism:sft-unknown-examples-drive-hallucination
  confidence: medium
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
  confidence: medium
- type: related_to
  target: '[[knowledge-boundary]]'
  target_id: term:knowledge-boundary
  confidence: medium
---

A continual-learning SFT technique in which a frozen teacher model (a snapshot of the student after task-format learning) constrains the student's output distribution via a KL-based distillation loss during subsequent factual fine-tuning, limiting representational drift on pre-existing knowledge while permitting new-fact acquisition.

**Why it matters here:** Reduces SFT-induced hallucinations from approximately 15% to approximately 3% degradation on held-out known facts without sacrificing factual plasticity, providing a drop-in mitigation for any SFT recipe that mixes training data outside the model's prior knowledge boundary.

**Lineage:** Instantiates the Learning Without Forgetting (LWF) framework (Li & Hoiem 2017) adapted for large language and multimodal models (Zhu et al. 2025); distinguishes itself from generic L2 weight regularization by operating on output distributions rather than weight magnitudes.
