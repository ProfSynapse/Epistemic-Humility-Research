---
aliases:
- Injecting conflicting answers induces abstention in low-confidence settings
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:knowledge-conflict-induces-abstention
  type: mechanism
  status: canonical
cause: Presenting an LLM with alternative answers and supporting passages that conflict with its parametric knowledge
effect: LLMs that are swayed by conflicting information [[abstention|abstain]] more; LLMs confident in their parametric knowledge stick to their answer
polarity: enables
related:
- '[[2402.00367--dont-hallucinate-abstain]]'
- '[[abstention]]'
relationships:
- type: supported_by
  target: '[[2402.00367--dont-hallucinate-abstain]]'
  target_id: paper:2402.00367
  confidence: high
- type: related_to
  target: '[[abstention]]'
  target_id: term:abstention
---

When contradictory evidence is injected into the context, models with lower parametric confidence about the answer are more susceptible to the conflicting signal, which surfaces as uncertainty and can trigger abstention. Models with high parametric confidence are less affected and maintain their original answer. The dont-hallucinate-abstain paper (arXiv:2402.00367) exploits this as a method for inducing abstention by deliberately constructing conflicting-evidence prompts for questions where the model's parametric confidence is borderline.
