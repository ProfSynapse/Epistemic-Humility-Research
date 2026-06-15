---
aliases:
- Larger model size improves abstention calibration
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:larger-model-better-abstention
  type: mechanism
  status: canonical
cause: Applying [[idk-sft]] to a larger model (Llama-2-70b-chat vs 7b-chat)
effect: 5.8% improvement in total Ik-Ik + Ik-Idk questions, indicating better [[self-knowledge]] discrimination
polarity: increases
related:
- '[[2401.13275--can-ai-assistants-know-what-they-dont-know]]'
- '[[idk-sft]]'
- '[[self-knowledge]]'
relationships:
- type: supported_by
  target: '[[2401.13275--can-ai-assistants-know-what-they-dont-know]]'
  target_id: paper:2401.13275
  confidence: high
- type: related_to
  target: '[[idk-sft]]'
  target_id: method:idk-sft
- type: related_to
  target: '[[self-knowledge]]'
  target_id: term:self-knowledge
---

Larger models have stronger parametric knowledge and richer internal representations of question difficulty, which gives Idk-SFT a better foundation to build on. When the model's underlying factual competence is higher, abstention training can focus on boundary cases rather than on questions the smaller model simply cannot answer. The can-ai-assistants paper (arXiv:2401.13275) measures a 5.8% improvement in combined Ik-Ik and Ik-Idk rates when scaling from 7B to 70B with the same SFT procedure.
