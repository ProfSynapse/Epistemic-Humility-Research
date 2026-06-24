---
aliases:
- entropy collapse
- policy entropy collapse in RLVR
- diversity collapse in RL training
tags:
- kg/term
- concept
- term
kg:
  id: term:policy-entropy-collapse
  type: term
  status: canonical
area: terms
related:
- '[[2606.08543--rl-diversity-collapse]]'
- '[[reasoning-fine-tuning]]'
- '[[group-relative-policy-optimization]]'
- '[[rlvr-post-training-degrades-abstention]]'
- '[[preference-collapse-causes-alignment-overconfidence]]'
- '[[decoding-randomness]]'
relationships:
- type: proposed_by
  target: '[[2606.08543--rl-diversity-collapse]]'
  target_id: paper:2606.08543
  confidence: high
- type: related_to
  target: '[[reasoning-fine-tuning]]'
  target_id: method:reasoning-fine-tuning
  confidence: medium
- type: related_to
  target: '[[group-relative-policy-optimization]]'
  target_id: method:group-relative-policy-optimization
  confidence: medium
- type: related_to
  target: '[[rlvr-post-training-degrades-abstention]]'
  target_id: mechanism:rlvr-post-training-degrades-abstention
  confidence: medium
- type: related_to
  target: '[[preference-collapse-causes-alignment-overconfidence]]'
  target_id: mechanism:preference-collapse-causes-alignment-overconfidence
  confidence: medium
- type: related_to
  target: '[[decoding-randomness]]'
  target_id: term:decoding-randomness
  confidence: medium
---

A training pathology in reinforcement learning with verifiable rewards (RLVR) where the policy's output distribution prematurely concentrates on a narrow set of high-probability reasoning paths, reducing rollout diversity and degrading majority-vote accuracy. Occurs because the reward signal reinforces successful paths without a mechanism to maintain exploration across other plausible continuations.

**Why it matters here:** Policy-entropy collapse is the mechanism PAEC is designed to counteract. It also likely underlies the rlvr-post-training-degrades-abstention finding: a policy concentrated on narrow paths loses the internal uncertainty signal that supports appropriate abstention on genuinely uncertain queries.

**Lineage:** Described in PAEC (arXiv:2606.08543, Abstract and Section 2) as the primary failure mode addressed. Conceptually related to preference-collapse-causes-alignment-overconfidence in the RLHF setting.
