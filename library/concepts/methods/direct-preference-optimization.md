---
aliases:
- DPO
- Direct Preference Optimization
tags:
- kg/method
- concept
- method
kg:
  id: method:direct-preference-optimization
  type: method
  status: canonical
area: methods
related:
- '[[2305.18290--direct-preference-optimization]]'
- '[[reinforcement-learning-from-human-feedback]]'
- '[[kahneman-tversky-optimization]]'
relationships:
- type: proposed_by
  target: '[[2305.18290--direct-preference-optimization]]'
  target_id: paper:2305.18290
  confidence: high
- type: derived_from
  target: '[[reinforcement-learning-from-human-feedback]]'
  target_id: method:reinforcement-learning-from-human-feedback
- type: related_to
  target: '[[kahneman-tversky-optimization]]'
  target_id: method:kahneman-tversky-optimization
---

Direct Preference Optimization trains a language model directly on pairs of
preferred and dispreferred responses, skipping the separately-trained reward
model and the RL loop that RLHF uses. It reparameterizes the RLHF objective so
that the optimal policy has a closed-form relationship to the reference policy,
which turns preference learning into a single classification-style loss over
preference pairs.

**Why it matters here:** DPO is one of the three preference-training arms the
Phase 1 experiment compares (SFT vs DPO vs KTO) for teaching abstention, so its
behaviour relative to [[kahneman-tversky-optimization]] and plain
[[supervised-finetuning]] is one of the central contrasts in the study.

**Lineage:** derives from [[reinforcement-learning-from-human-feedback]];
[[kahneman-tversky-optimization]] is a later prospect-theory variant that drops
the paired-preference requirement.
