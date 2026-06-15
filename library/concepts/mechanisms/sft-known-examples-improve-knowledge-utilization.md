---
aliases:
- SFT on Known examples improves utilization of pre-existing knowledge
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:sft-known-examples-improve-knowledge-utilization
  type: mechanism
  status: canonical
cause: '[[supervised-finetuning]] on examples within the model''s [[knowledge-boundary]] (Known examples in [[slick]])'
effect: Better test-time accuracy on held-out questions, improving utilization of pre-existing knowledge
polarity: increases
related:
- '[[2405.05904--finetuning-new-knowledge-hallucinations]]'
- '[[supervised-finetuning]]'
- '[[knowledge-boundary]]'
- '[[slick]]'
relationships:
- type: supported_by
  target: '[[2405.05904--finetuning-new-knowledge-hallucinations]]'
  target_id: paper:2405.05904
  confidence: high
- type: related_to
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
- type: related_to
  target: '[[knowledge-boundary]]'
  target_id: term:knowledge-boundary
- type: related_to
  target: '[[slick]]'
  target_id: method:slick
---

Known examples reinforce pathways from question features to existing parametric knowledge, making that knowledge more reliably accessible at inference time without introducing hallucination risk. The finetuning-new-knowledge-hallucinations paper (arXiv:2405.05904) shows that training on Known-only examples consistently improves closed-book QA accuracy, in contrast to Unknown examples which degrade accuracy. This asymmetry motivates pre-filtering training data to remove Unknown examples as a practical hallucination mitigation strategy.
