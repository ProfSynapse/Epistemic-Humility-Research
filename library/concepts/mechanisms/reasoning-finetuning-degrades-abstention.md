---
aliases:
- Reasoning Fine-Tuning Degrades Abstention
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:reasoning-finetuning-degrades-abstention
  type: mechanism
  status: canonical
cause: '[[reasoning-fine-tuning]] that optimizes for a verifiable correctness reward (RLVR), biasing models toward producing definitive confident answers'
effect: Decreased [[abstention-recall]] on unanswerable questions, including in math and science domains; models hallucinate missing context rather than abstaining
polarity: decreases
related:
- '[[2506.09038--abstentionbench]]'
- '[[reasoning-fine-tuning]]'
- '[[abstention-recall]]'
relationships:
- type: supported_by
  target: '[[2506.09038--abstentionbench]]'
  target_id: paper:2506.09038
  confidence: high
- type: related_to
  target: '[[reasoning-fine-tuning]]'
  target_id: method:reasoning-fine-tuning
- type: related_to
  target: '[[abstention-recall]]'
  target_id: metric:abstention-recall
---

RLVR-based reasoning fine-tuning rewards models for producing verifiably correct final answers, creating a strong pressure to always commit to an answer. This directly conflicts with the abstention policy of acknowledging uncertainty: the model learns that generating a confident answer earns reward while abstaining does not. AbstentionBench (arXiv:2506.09038) documents this across multiple reasoning-tuned models, finding degraded abstention recall on false-premise and unanswerable questions even in domains where reasoning models are explicitly optimized.
