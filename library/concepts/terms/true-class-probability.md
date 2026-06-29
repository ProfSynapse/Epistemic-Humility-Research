---
aliases:
- True Class Probability
- TCP
tags:
- kg/term
- concept
- term
kg:
  id: term:true-class-probability
  type: term
  status: canonical
area: terms
related:
- '[[1910.04851--addressing-failure-prediction-learning-model-confidence]]'
- '[[confidnet]]'
- '[[max-confidence-scoring]]'
- '[[overconfidence]]'
relationships:
- type: proposed_by
  target: '[[1910.04851--addressing-failure-prediction-learning-model-confidence]]'
  target_id: paper:1910.04851
  confidence: medium
- type: related_to
  target: '[[confidnet]]'
  target_id: method:confidnet
  confidence: high
- type: related_to
  target: '[[max-confidence-scoring]]'
  target_id: method:max-confidence-scoring
  confidence: high
---

True class probability (TCP) is the softmax probability a classifier assigns to
the ground-truth class, equal to `exp(-cross-entropy)`. It is a proper-scoring
quantity for failure prediction: when TCP > 1/2 the prediction is necessarily
correct, and when TCP < 1/K (for K classes) the prediction is necessarily wrong,
so TCP separates correct from incorrect predictions far more cleanly than the
maximum class probability (which is large even on confident errors).

**Why it matters here:** TCP is the regression target that makes a trained
confidence head outperform reading the model's own max-softmax — the same logic
behind targeting a per-row correctness/answerability label for the aux_head. It
is the proper-scoring framing of "what should a confidence readout predict."

**Lineage:** Corbiere et al. 2019; the target that [[confidnet]] regresses, in
contrast to the max-softmax-response of [[max-confidence-scoring]].
