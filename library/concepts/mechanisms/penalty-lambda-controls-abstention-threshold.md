---
aliases:
- lambda sets confidence threshold
- ternary reward decision boundary
- 1/(1+lambda) threshold
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:penalty-lambda-controls-abstention-threshold
  type: mechanism
  status: canonical
cause: "Setting the error penalty to lambda in a ternary reward (+1 correct, 0 abstain, -lambda wrong) during RLVR training"
effect: "The rational agent abstains whenever its confidence in the correct answer falls below 1/(1+lambda), making the penalty an interpretable domain risk knob: lambda=1 requires above 50% confidence to answer, lambda=10 requires above ~91%, lambda=100 requires above ~99%"
polarity: enables
related:
- '[[2511.11500--reinforced-hesitation]]'
- '[[reinforced-hesitation]]'
- '[[ternary-reward-design]]'
- '[[abstention]]'
- '[[over-abstention]]'
- '[[binary-grading-reinforces-hallucination]]'
relationships:
- type: supported_by
  target: '[[2511.11500--reinforced-hesitation]]'
  target_id: paper:2511.11500
  confidence: high
- type: related_to
  target: '[[reinforced-hesitation]]'
  target_id: method:reinforced-hesitation
  confidence: high
- type: related_to
  target: '[[ternary-reward-design]]'
  target_id: method:ternary-reward-design
  confidence: high
- type: related_to
  target: '[[abstention]]'
  target_id: term:abstention
  confidence: high
- type: related_to
  target: '[[over-abstention]]'
  target_id: term:over-abstention
  confidence: high
- type: related_to
  target: '[[binary-grading-reinforces-hallucination]]'
  target_id: mechanism:binary-grading-reinforces-hallucination
  confidence: high
---

Under expected-utility maximization, a model answers if and only if p(correct) - lambda * p(wrong) > 0, i.e., p(correct) / p(wrong) > lambda, which for binary correct/wrong reduces to a confidence threshold of 1/(1+lambda). The paper's controlled experiments with Qwen3-1.7B confirm this: at lambda=1, ~60% abstention on hard problems and ~10% on easy ones; at lambda=10, below 1% wrong-answer rate and greater than 99% conditional accuracy; at lambda=0, near-zero abstention and persistent 15% errors. The cross-penalty evaluation (Section 3.3) shows each model is Pareto-optimal precisely for its training lambda, consistent with the threshold prediction.
