---
aliases:
- Out-of-Distribution Detection
- OOD detection
- out-of-distribution input detection
tags:
- kg/term
- concept
- term
kg:
  id: term:out-of-distribution-detection
  type: term
  status: canonical
area: terms
related:
- '[[1802.04865--learning-confidence-out-distribution-detection-neural-networks]]'
- '[[learned-confidence-branch]]'
- '[[overconfidence]]'
relationships:
- type: proposed_by
  target: '[[1802.04865--learning-confidence-out-distribution-detection-neural-networks]]'
  target_id: paper:1802.04865
  confidence: medium
- type: related_to
  target: '[[overconfidence]]'
  target_id: term:overconfidence
  confidence: high
---

Out-of-distribution (OOD) detection is the task of flagging inputs at test time
that are drawn from a different distribution than the training data, so the model
can decline or down-weight its prediction rather than answer confidently on
inputs it was never trained for. A well-calibrated confidence estimate should be
low on OOD inputs; the failure mode is a model that is overconfident on inputs
far from its training manifold.

**Why it matters here:** OOD detection is the classic vision-side analogue of
answerability/knowledge-boundary detection in the epistemic-humility setting:
both ask a model to recognize when an input is outside what it can answer
reliably and to signal low confidence rather than hallucinate.

**Lineage:** Hendrycks and Gimpel 2017 (baseline max-softmax); studied here via
DeVries and Taylor 2018's [[learned-confidence-branch]].
