---
aliases:
- Grad Detect
- Gradient-Based Hallucination Detection
tags:
- kg/method
- concept
- method
kg:
  id: method:grad-detect
  type: method
  status: canonical
area: methods
related:
- '[[2606.24790--grad-detect-gradient-hallucination-detection]]'
- '[[linear-probe]]'
- '[[p-true]]'
- '[[consistency-based-confidence]]'
- '[[hallucination]]'
- '[[abstention]]'
relationships:
- type: proposed_by
  target: '[[2606.24790--grad-detect-gradient-hallucination-detection]]'
  target_id: paper:2606.24790
  confidence: high
- type: related_to
  target: '[[linear-probe]]'
  target_id: method:linear-probe
  confidence: medium
- type: related_to
  target: '[[p-true]]'
  target_id: method:p-true
  confidence: medium
- type: related_to
  target: '[[consistency-based-confidence]]'
  target_id: method:consistency-based-confidence
  confidence: medium
---

Grad Detect predicts whether a language model's own answer is a hallucination,
and whether the model should abstain, by reading the layer-wise gradient
patterns produced in a single forward-backward pass over the generated answer.
Instead of looking only at output-level signals (token probabilities, sampled
agreement, or verbalized confidence), it backpropagates a loss on the model's
response and turns the resulting per-layer gradient statistics into features for
a lightweight classifier. The authors report that this gradient structure
carries correctness information not recoverable from outputs alone, and that
restricting the features to the last five layers preserves over 97% of the
discriminative signal, so the method stays cheap to deploy.

**Why it matters here:** Grad Detect is a honesty-and-abstention detector that
operates on internal model state, making it a candidate signal for the
abstention and uncertainty-reporting work in this project. It sits alongside
[[p-true]], [[verbalized-confidence]], and [[consistency-based-confidence]] as a
self-knowledge signal, but sources that signal from gradients rather than from
the model's outputs, and it is the baseline it claims to beat on both
hallucination detection and abstention prediction.

**Lineage:** a gradient-space cousin of activation probing such as
[[linear-probe]] and [[correlational-probe]]: where those read residual-stream
activations for a truth or known-unknown signal, Grad Detect reads the gradients
of a single backward pass. It is positioned against confidence-based and
sampling-based baselines rather than derived from any one of them.
