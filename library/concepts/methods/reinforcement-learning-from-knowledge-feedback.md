---
aliases:
- RLKF
- knowledge feedback alignment
- Reinforcement Learning from Knowledge Feedback (RLKF)
tags:
- kg/method
- concept
- method
kg:
  id: method:reinforcement-learning-from-knowledge-feedback
  type: method
  status: canonical
area: methods
related:
- '[[2403.18349--rlkf-rejection-improves-reliability]]'
- '[[reinforcement-learning-from-human-feedback]]'
- '[[proximal-policy-optimization]]'
- '[[knowledge-boundary]]'
relationships:
- type: proposed_by
  target: '[[2403.18349--rlkf-rejection-improves-reliability]]'
  target_id: paper:2403.18349
  confidence: high
- type: derived_from
  target: '[[reinforcement-learning-from-human-feedback]]'
  target_id: method:reinforcement-learning-from-human-feedback
- type: related_to
  target: '[[proximal-policy-optimization]]'
  target_id: method:proximal-policy-optimization
- type: related_to
  target: '[[knowledge-boundary]]'
  target_id: term:knowledge-boundary
---

Reinforcement Learning from Knowledge Feedback (RLKF) is a three-step alignment
framework that first probes the model's knowledge boundary via multiple-sample
correctness estimation, then synthesizes model-specific Reliable Preference Data
(RPD) ranking correct responses above refusals above wrong answers, and finally
trains a Reliable Reward Model (RRM) which is used to fine-tune the policy via
PPO so that the model explicitly refuses out-of-knowledge questions rather than
hallucinating.

**Why it matters here:** RLKF directly targets the abstention vs. hallucination
trade-off that the SFT-vs-DPO-vs-KTO study investigates: by constructing
model-specific preference data around refusal, it provides a reference point for
how RL-based approaches can align abstention without purely supervised signals.

**Lineage:** extends [[reinforcement-learning-from-human-feedback]] by replacing
human preference labels with knowledge-grounded correctness signals; uses
[[proximal-policy-optimization]] as the policy-optimization step.
