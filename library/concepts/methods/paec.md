---
aliases:
- Position-Aware Entropy Calibration
- PAEC
- token-level entropy calibration
tags:
- kg/method
- concept
- method
kg:
  id: method:paec
  type: method
  status: canonical
area: methods
related:
- '[[2606.08543--rl-diversity-collapse]]'
- '[[group-relative-policy-optimization]]'
- '[[reasoning-fine-tuning]]'
- '[[self-consistency]]'
- '[[decoding-randomness]]'
- '[[policy-entropy-collapse-narrows-rlvr-reasoning-paths]]'
- '[[position-aware-entropy-penalty-preserves-exploration]]'
relationships:
- type: proposed_by
  target: '[[2606.08543--rl-diversity-collapse]]'
  target_id: paper:2606.08543
  confidence: high
- type: related_to
  target: '[[group-relative-policy-optimization]]'
  target_id: method:group-relative-policy-optimization
  confidence: medium
- type: related_to
  target: '[[reasoning-fine-tuning]]'
  target_id: method:reasoning-fine-tuning
  confidence: medium
- type: related_to
  target: '[[self-consistency]]'
  target_id: method:self-consistency
  confidence: medium
- type: related_to
  target: '[[decoding-randomness]]'
  target_id: term:decoding-randomness
  confidence: medium
- type: related_to
  target: '[[policy-entropy-collapse-narrows-rlvr-reasoning-paths]]'
  target_id: mechanism:policy-entropy-collapse-narrows-rlvr-reasoning-paths
  confidence: medium
- type: related_to
  target: '[[position-aware-entropy-penalty-preserves-exploration]]'
  target_id: mechanism:position-aware-entropy-penalty-preserves-exploration
  confidence: medium
---

A token-level entropy management framework for RLVR training that constructs a soft position mask from local top-p nucleus entropy and the top-two log-probability gap to identify decision-sensitive positions, then applies an anchor-based one-sided quadratic lower-bound penalty to prevent entropy collapse at those positions while leaving low-entropy positions unregularized.

**Why it matters here:** PAEC shows that entropy regularization in policy-gradient reasoning training should be spatially selective rather than uniform. Uniform entropy bonuses waste capacity on non-decision positions and may dilute the signal at positions that matter. The framework is relevant to understanding how RLVR training shapes internal uncertainty representations and connects to the broader question of why RLVR degrades abstention.

**Lineage:** Proposed in arXiv:2606.08543. Builds on group-relative-policy-optimization as the base training algorithm and reasoning-fine-tuning as the broader paradigm.
