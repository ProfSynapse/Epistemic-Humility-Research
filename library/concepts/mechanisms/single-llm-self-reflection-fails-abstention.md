---
aliases:
- Single-LLM self-reflection fails at abstention
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:single-llm-self-reflection-fails-abstention
  type: mechanism
  status: canonical
cause: Relying on a single LLM to evaluate or reflect on its own generated answers (calibration, prompting, or [[self-consistency]] approaches)
effect: Unreliable [[abstention]] decisions due to confirmation bias and [[hallucination]] in self-evaluation
polarity: prevents
related:
- '[[2402.00367--dont-hallucinate-abstain]]'
- '[[self-consistency]]'
- '[[abstention]]'
- '[[hallucination]]'
relationships:
- type: supported_by
  target: '[[2402.00367--dont-hallucinate-abstain]]'
  target_id: paper:2402.00367
  confidence: high
- type: related_to
  target: '[[self-consistency]]'
  target_id: method:self-consistency
- type: related_to
  target: '[[abstention]]'
  target_id: term:abstention
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
---

When a model evaluates its own answer, the evaluation is conditioned on the same internal state that produced the answer, making confirmation of the original (possibly hallucinated) answer likely. The model cannot step outside its own representations to detect errors it has already committed to. The dont-hallucinate-abstain paper (arXiv:2402.00367) documents this limitation systematically and argues for multi-LLM cooperative evaluation as an alternative, where independent models provide less correlated error signals.
