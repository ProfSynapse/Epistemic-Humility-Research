---
aliases:
- RLHF improves math unanswerability recognition
- chat tuning closes scale gap on abstention
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:rlhf-improves-unanswerability-recognition
  type: mechanism
  status: canonical
cause: "Reinforcement learning from human feedback (RLHF) fine-tuning applied to a base language model (LLaMA-v2 chat variants)"
effect: "Substantially improved F1 on the UMWP unanswerability recognition task across all three input forms; LLaMA-v2-13b-chat competes with LLaMA-65b despite having fewer than one-fifth the parameters"
polarity: increases
related:
- '[[2403.03558--umwp-unanswerable-math]]'
- '[[reinforcement-learning-from-human-feedback]]'
- '[[rlhf-reduces-closed-domain-hallucination]]'
- '[[umwp]]'
- '[[abstention]]'
- '[[hallucination]]'
- '[[self-knowledge-f1]]'
- '[[in-context-learning]]'
relationships:
- type: supported_by
  target: '[[2403.03558--umwp-unanswerable-math]]'
  target_id: paper:2403.03558
  confidence: high
- type: related_to
  target: '[[reinforcement-learning-from-human-feedback]]'
  target_id: method:reinforcement-learning-from-human-feedback
  confidence: high
- type: related_to
  target: '[[rlhf-reduces-closed-domain-hallucination]]'
  target_id: mechanism:rlhf-reduces-closed-domain-hallucination
  confidence: high
- type: related_to
  target: '[[umwp]]'
  target_id: dataset:umwp
  confidence: high
- type: related_to
  target: '[[abstention]]'
  target_id: term:abstention
  confidence: high
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
  confidence: high
- type: related_to
  target: '[[self-knowledge-f1]]'
  target_id: metric:self-knowledge-f1
  confidence: high
- type: related_to
  target: '[[in-context-learning]]'
  target_id: method:in-context-learning
  confidence: high
---

On UMWP, RLHF chat fine-tuning consistently closes the gap to larger base models. Comparing LLaMA-v2-7b-chat to LLaMA-v2-7b, LLaMA-v2-13b-chat to LLaMA-v2-13b, and LLaMA-v2-70b-chat to LLaMA-v2-70b, RLHF improves F1 across direct, instruction, and ICL input forms. The 13b-chat result is the sharpest case: it matches or exceeds LLaMA-65b, a roughly 5x parameter difference. This evidence complements the InstructGPT RLHF-reduces-closed-domain-hallucination finding but generalizes it to an explicit unanswerability recognition task rather than a closed-domain generation faithfulness measure.
