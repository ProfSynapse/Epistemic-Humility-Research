---
aliases:
- RLHF helpfulness bias suppresses refusal
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:rlhf-helpfulness-bias-suppresses-refusal
  type: mechanism
  status: canonical
cause: '[[reinforcement-learning-from-human-feedback]] [[reward-model]] trained only on helpfulness preference data, which treats both refusal and wrong answers as unhelpful'
effect: Model learns to answer rather than refuse out-of-[[knowledge-boundary]] questions, increasing [[hallucination]] rate
polarity: increases
related:
- '[[2403.18349--rlkf-rejection-improves-reliability]]'
- '[[reinforcement-learning-from-human-feedback]]'
- '[[reward-model]]'
- '[[knowledge-boundary]]'
- '[[hallucination]]'
relationships:
- type: supported_by
  target: '[[2403.18349--rlkf-rejection-improves-reliability]]'
  target_id: paper:2403.18349
  confidence: high
- type: related_to
  target: '[[reinforcement-learning-from-human-feedback]]'
  target_id: method:reinforcement-learning-from-human-feedback
- type: related_to
  target: '[[reward-model]]'
  target_id: method:reward-model
- type: related_to
  target: '[[knowledge-boundary]]'
  target_id: term:knowledge-boundary
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
---

Helpfulness-only reward models cannot distinguish between a wrong answer and a refusal when the question is outside the model's knowledge, and may prefer wrong answers because they are more fluent and appear more helpful. This reward mismatch trains the policy to generate plausible-sounding answers even on out-of-boundary questions. The RLKF paper (arXiv:2403.18349) identifies this as a central failure mode and proposes [[reinforcement-learning-from-knowledge-feedback]] as a corrective that conditions rewards on whether the model actually knows the answer.
