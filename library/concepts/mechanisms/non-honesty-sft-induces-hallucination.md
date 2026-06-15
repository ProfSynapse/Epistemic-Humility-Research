---
aliases:
- Non-Honesty SFT Induces Hallucination
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:non-honesty-sft-induces-hallucination
  type: mechanism
  status: canonical
cause: '[[supervised-finetuning]] that provides gold answers for questions outside the model''s [[knowledge-boundary]]'
effect: Decreased accuracy on those questions as the model learns to fabricate plausible-sounding but incorrect answers
polarity: increases
related:
- '[[2312.07000--alignment-for-honesty]]'
- '[[supervised-finetuning]]'
- '[[knowledge-boundary]]'
relationships:
- type: supported_by
  target: '[[2312.07000--alignment-for-honesty]]'
  target_id: paper:2312.07000
  confidence: high
- type: related_to
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
- type: related_to
  target: '[[knowledge-boundary]]'
  target_id: term:knowledge-boundary
---

Standard SFT with correct answers as targets applies identical training pressure to in-boundary and out-of-boundary questions, giving the model no signal to distinguish questions it can reliably answer from those it cannot. On out-of-boundary questions, gradient descent drives the model toward producing the training label distribution, which is factually correct but not grounded in the model's parametric knowledge. The alignment-for-honesty paper (arXiv:2312.07000) demonstrates this degradation and contrasts it with [[honesty-oriented-sft]], which instead teaches the model to abstain on unknown questions.
