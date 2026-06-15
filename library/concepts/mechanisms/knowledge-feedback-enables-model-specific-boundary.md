---
aliases:
- Knowledge feedback enables model-specific boundary detection
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:knowledge-feedback-enables-model-specific-boundary
  type: mechanism
  status: canonical
cause: Dynamically synthesizing preference data by sampling model responses and estimating per-question correctness distribution
effect: '[[reward-model]] learns to distinguish within-boundary from out-of-boundary questions for the specific LLM, enabling targeted refusal training'
polarity: enables
related:
- '[[2403.18349--rlkf-rejection-improves-reliability]]'
- '[[reward-model]]'
relationships:
- type: supported_by
  target: '[[2403.18349--rlkf-rejection-improves-reliability]]'
  target_id: paper:2403.18349
  confidence: high
- type: related_to
  target: '[[reward-model]]'
  target_id: method:reward-model
---

Static abstention datasets reflect the curators' judgment about what questions are unanswerable, not the specific model's actual knowledge boundary. By sampling responses from the target model and using the empirical correctness distribution as a boundary signal, the [[reinforcement-learning-from-knowledge-feedback]] approach builds a reward model that is calibrated to the specific model's competence. The RLKF paper (arXiv:2403.18349) shows this model-specific boundary detection substantially outperforms static dataset approaches on reliability metrics.
