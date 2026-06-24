---
aliases:
- trajectory features
- problem-level trajectory features
- three trajectory features
tags:
- kg/method
- concept
- method
kg:
  id: method:trajectory-distributional-features
  type: method
  status: canonical
area: methods
related:
- '[[2606.05145--distributional-failure-signatures]]'
- '[[pass-at-k]]'
- '[[best-of-n-sampling]]'
- '[[failure-recoverability-structure]]'
- '[[steerable-hard]]'
relationships:
- type: proposed_by
  target: '[[2606.05145--distributional-failure-signatures]]'
  target_id: paper:2606.05145
  confidence: high
- type: related_to
  target: '[[pass-at-k]]'
  target_id: metric:pass-at-k
  confidence: medium
- type: related_to
  target: '[[best-of-n-sampling]]'
  target_id: method:best-of-n-sampling
  confidence: medium
- type: related_to
  target: '[[failure-recoverability-structure]]'
  target_id: term:failure-recoverability-structure
  confidence: medium
- type: related_to
  target: '[[steerable-hard]]'
  target_id: term:steerable-hard
  confidence: medium
---

A set of three problem-level features computed from the statistical distribution of failed rollouts (not their text content) that characterize a problem's recoverability regime and support training-free routing to appropriate test-time interventions.

**Why it matters here:** Enables post-training audit and test-time routing without weight-space access or additional training, purely from observing failure distributions across rollouts.

**Lineage:** Proposed in 2606.05145; related to pass-at-k and best-of-n-sampling in measuring rollout statistics but distinct in targeting recoverability structure rather than aggregate accuracy.
