---
aliases:
- In-Context Learning Improves Self-Knowledge
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:icl-improves-self-knowledge
  type: mechanism
  status: canonical
cause: Adding few-shot examples of answerable and unanswerable question-answer pairs to the prompt ([[in-context-learning]] input form)
effect: Substantially increased [[self-knowledge-f1]]; the gap between base and instruction-tuned models narrows with ICL
polarity: increases
related:
- '[[2305.18153--selfaware-know-what-they-dont-know]]'
- '[[in-context-learning]]'
- '[[self-knowledge-f1]]'
relationships:
- type: supported_by
  target: '[[2305.18153--selfaware-know-what-they-dont-know]]'
  target_id: paper:2305.18153
  confidence: high
- type: related_to
  target: '[[in-context-learning]]'
  target_id: method:in-context-learning
- type: related_to
  target: '[[self-knowledge-f1]]'
  target_id: metric:self-knowledge-f1
---

Few-shot ICL examples demonstrate the format and expectation that some questions should be declined, which activates existing latent self-knowledge representations without requiring any weight updates. The SelfAware paper (arXiv:2305.18153) shows that the davinci model gains 27.96% on [[self-knowledge]] F1 with ICL over direct prompting, and that ICL narrows but does not close the gap between base and instruction-tuned models. This pattern suggests self-knowledge representations are present in pretrained models but require a prompt cue to surface.
