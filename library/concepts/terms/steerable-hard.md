---
aliases:
- Steerable-Hard subset
- steerable-hard failures
tags:
- kg/term
- concept
- term
kg:
  id: term:steerable-hard
  type: term
  status: canonical
area: terms
related:
- '[[2606.05145--distributional-failure-signatures]]'
- '[[failure-recoverability-structure]]'
- '[[trajectory-distributional-features]]'
- '[[best-of-n-sampling]]'
- '[[over-abstention]]'
relationships:
- type: proposed_by
  target: '[[2606.05145--distributional-failure-signatures]]'
  target_id: paper:2606.05145
  confidence: high
- type: related_to
  target: '[[failure-recoverability-structure]]'
  target_id: term:failure-recoverability-structure
  confidence: medium
- type: related_to
  target: '[[trajectory-distributional-features]]'
  target_id: method:trajectory-distributional-features
  confidence: medium
- type: related_to
  target: '[[best-of-n-sampling]]'
  target_id: method:best-of-n-sampling
  confidence: medium
- type: related_to
  target: '[[over-abstention]]'
  target_id: term:over-abstention
  confidence: medium
---

The subset of model failures on reasoning problems where retry with additional rollouts is insufficient to rescue the problem, but at least one bounded test-time intervention (short of retraining) is reachable and can succeed.

**Why it matters here:** This subset is the deployment-relevant target for intelligent test-time routing: problems here cannot be solved by throwing more compute at the same operator, but can be rescued by switching intervention type. The +12.2% rescue lift in 2606.05145 is measured on this subset.

**Lineage:** Defined in 2606.05145 as a construct for identifying where intervention routing adds value beyond retry.
