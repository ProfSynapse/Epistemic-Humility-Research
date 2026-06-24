---
aliases:
- failed rollouts encode recoverability
- failure distribution encodes rescue structure
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:failed-traces-encode-recoverability
  type: mechanism
  status: canonical
cause: "A language model fails repeatedly on a reasoning problem, generating a distribution of failed rollouts"
effect: "The statistical distribution of those failed rollouts encodes which class of test-time intervention can rescue the problem, independently of any information in the text content of the traces"
polarity: enables
related:
- '[[2606.05145--distributional-failure-signatures]]'
- '[[failure-recoverability-structure]]'
- '[[trajectory-distributional-features]]'
- '[[steerable-hard]]'
- '[[policy-entropy-collapse-narrows-rlvr-reasoning-paths]]'
- '[[rlhf-rl-optimisation-collapses-per-input-diversity]]'
relationships:
- type: supported_by
  target: '[[2606.05145--distributional-failure-signatures]]'
  target_id: paper:2606.05145
  confidence: high
- type: related_to
  target: '[[failure-recoverability-structure]]'
  target_id: term:failure-recoverability-structure
  confidence: high
- type: related_to
  target: '[[trajectory-distributional-features]]'
  target_id: method:trajectory-distributional-features
  confidence: high
- type: related_to
  target: '[[steerable-hard]]'
  target_id: term:steerable-hard
  confidence: high
- type: related_to
  target: '[[policy-entropy-collapse-narrows-rlvr-reasoning-paths]]'
  target_id: mechanism:policy-entropy-collapse-narrows-rlvr-reasoning-paths
  confidence: high
- type: related_to
  target: '[[rlhf-rl-optimisation-collapses-per-input-diversity]]'
  target_id: mechanism:rlhf-rl-optimisation-collapses-per-input-diversity
  confidence: high
---

The paper argues that not all failures are alike: some resist any resampling (structural failures) while others merely reflect unlucky draws (sampling failures). The distributional fingerprint of rollouts over a problem, captured by three trajectory features, exposes this recoverability structure. This mechanism is the foundational claim of 2606.05145: the signal is in the distribution, not the text, and it enables training-free routing and post-training audit without weight-space access.
