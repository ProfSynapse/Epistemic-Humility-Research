---
aliases:
- RLVR entropy collapse reduces rollout diversity
- policy entropy collapse in reasoning RL
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:policy-entropy-collapse-narrows-rlvr-reasoning-paths
  type: mechanism
  status: canonical
cause: "Standard RLVR training (e.g., GRPO) optimizing for verifiable reward without entropy regularization"
effect: "Premature concentration of the policy on narrow high-probability reasoning paths, reducing majority-vote accuracy on hard benchmarks such as AIME-style tasks"
polarity: decreases
related:
- '[[2606.08543--rl-diversity-collapse]]'
- '[[paec]]'
- '[[policy-entropy-collapse]]'
- '[[group-relative-policy-optimization]]'
- '[[rlvr-post-training-degrades-abstention]]'
- '[[reasoning-fine-tuning]]'
relationships:
- type: supported_by
  target: '[[2606.08543--rl-diversity-collapse]]'
  target_id: paper:2606.08543
  confidence: high
- type: related_to
  target: '[[paec]]'
  target_id: method:paec
  confidence: high
- type: related_to
  target: '[[policy-entropy-collapse]]'
  target_id: term:policy-entropy-collapse
  confidence: high
- type: related_to
  target: '[[group-relative-policy-optimization]]'
  target_id: method:group-relative-policy-optimization
  confidence: high
- type: related_to
  target: '[[rlvr-post-training-degrades-abstention]]'
  target_id: mechanism:rlvr-post-training-degrades-abstention
  confidence: high
- type: related_to
  target: '[[reasoning-fine-tuning]]'
  target_id: method:reasoning-fine-tuning
  confidence: high
---

As RLVR training progresses, the verifiable-reward signal repeatedly reinforces the few paths that receive positive reward. Without a mechanism to maintain entropy at decision-sensitive positions, the policy concentrates probability mass on its current best guesses, reducing the diversity of sampled rollouts. This loss of diversity degrades majority-vote (Maj@K) accuracy because the K samples become increasingly similar and errors are correlated. PAEC (arXiv:2606.08543) documents this empirically: GRPO Avg Maj@K on five math benchmarks is 35.5, while adding position-aware entropy floor enforcement raises it to 41.6. The same collapse likely underlies the rlvr-post-training-degrades-abstention finding, as a less diverse policy has less internal uncertainty signal.
