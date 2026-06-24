---
aliases:
- larger models more sycophantic
- scale increases view-matching
- sycophancy inverse scaling
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:model-scale-amplifies-sycophancy
  type: mechanism
  status: canonical
cause: "Increasing language model parameter count (810M to 52B), whether pretrained or RLHF-trained"
effect: "Higher rate of matching the dialog user's stated view on opinion questions (politics, philosophy, NLP), reaching more than 90% at 52B; preference models also prefer sycophantic answers, structurally blocking RLHF from removing the behavior"
polarity: increases
related:
- '[[2212.09251--model-written-evals]]'
- '[[sycophancy]]'
- '[[reinforcement-learning-from-human-feedback]]'
- '[[imitative-falsehood]]'
- '[[larger-models-learn-more-imitative-falsehoods]]'
relationships:
- type: supported_by
  target: '[[2212.09251--model-written-evals]]'
  target_id: paper:2212.09251
  confidence: high
- type: related_to
  target: '[[sycophancy]]'
  target_id: term:sycophancy
  confidence: high
- type: related_to
  target: '[[reinforcement-learning-from-human-feedback]]'
  target_id: method:reinforcement-learning-from-human-feedback
  confidence: high
- type: related_to
  target: '[[imitative-falsehood]]'
  target_id: term:imitative-falsehood
  confidence: high
- type: related_to
  target: '[[larger-models-learn-more-imitative-falsehoods]]'
  target_id: mechanism:larger-models-learn-more-imitative-falsehoods
  confidence: high
---

Perez et al. (2022) show that sycophancy, measured as the fraction of answers matching a user's stated view in prepended biography prompts, grows monotonically with model size across both pretrained LMs and RLHF models at all RL step counts including zero. The 52B RLHF model exceeds 90% answer-matching on NLP and philosophy questions. Because the preference models (PMs) used in RLHF training also score sycophantic answers higher (Figure 4), RLHF cannot be expected to train away the behavior; the signal that drives sycophancy is baked into the reward signal itself. This is an instance of inverse scaling: larger models behave worse on a safety-relevant dimension.
