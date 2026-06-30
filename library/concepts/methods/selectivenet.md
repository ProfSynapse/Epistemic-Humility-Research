---
aliases:
- SelectiveNet
- selective network with integrated reject option
tags:
- kg/method
- concept
- method
kg:
  id: method:selectivenet
  type: method
  status: canonical
area: methods
related:
- '[[1901.09192--selectivenet-deep-neural-network-integrated-reject-option]]'
- '[[selective-prediction]]'
- '[[selective-risk]]'
- '[[coverage-aware-training]]'
- '[[abstention]]'
- '[[learned-confidence-branch]]'
relationships:
- type: proposed_by
  target: '[[1901.09192--selectivenet-deep-neural-network-integrated-reject-option]]'
  target_id: paper:1901.09192
  confidence: high
- type: related_to
  target: '[[selective-prediction]]'
  target_id: term:selective-prediction
  confidence: high
- type: related_to
  target: '[[selective-risk]]'
  target_id: metric:selective-risk
  confidence: high
- type: related_to
  target: '[[coverage-aware-training]]'
  target_id: method:coverage-aware-training
  confidence: high
- type: related_to
  target: '[[abstention]]'
  target_id: term:abstention
  confidence: medium
---

SelectiveNet is a deep network with an integrated reject option, trained jointly
through three heads on a shared body: a prediction head `f`, a selection head `g`
(a sigmoid gate deciding whether to predict or abstain), and an auxiliary
prediction head `h` that keeps the representation generally useful. It optimizes
a selective loss that minimizes risk on the covered (non-rejected) subset subject
to a target-coverage constraint, enforced via an interior-point penalty so the
model hits a pre-specified coverage level.

**Why it matters here:** It is the canonical end-to-end example of training a
selection/abstention head jointly with the base network rather than thresholding
a post-hoc confidence score — the joint-co-training shape of the Phase B aux_head
experiment. The auxiliary head `h` is an explicit guard against the body
overfitting to the covered subset.

**Lineage:** Geifman and El-Yaniv 2019; builds on selective-prediction theory
(El-Yaniv and Wiener 2010) and contrasts with post-hoc confidence thresholding
such as the [[learned-confidence-branch]] and softmax-response baselines.
