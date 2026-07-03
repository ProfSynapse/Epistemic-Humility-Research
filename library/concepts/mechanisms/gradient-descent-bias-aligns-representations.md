---
aliases:
- Gradient descent implicit bias aligns concept representations
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:gradient-descent-bias-aligns-representations
  type: mechanism
  status: canonical
cause: "Implicit bias of gradient descent optimising the NTP exponential loss subproblem, which functions as a hidden binary classification task over concept pairs"
effect: "Unembedding [[steering-vector|steering vectors]] for the same concept converge to mutual cosine similarity 1 in the limit; with joint training, embedding and unembedding steering vectors also align"
polarity: enables
related:
- '[[2403.03867--origins-linear-representations-large-language-models]]'
- '[[linear-representation-hypothesis]]'
- '[[steering-vector]]'
- '[[next-token-prediction]]'
relationships:
- type: supported_by
  target: '[[2403.03867--origins-linear-representations-large-language-models]]'
  target_id: paper:2403.03867
  confidence: high
- type: related_to
  target: '[[linear-representation-hypothesis]]'
  target_id: term:linear-representation-hypothesis
- type: related_to
  target: '[[steering-vector]]'
  target_id: term:steering-vector
- type: related_to
  target: '[[next-token-prediction]]'
  target_id: method:next-token-prediction
---

Gradient descent on the cross-entropy NTP loss converges to a max-margin solution for the binary classification subtask implicit in each concept pair, and the max-margin solution aligns the unembedding weight differences for all context pairs with the same concept. This implicit bias guarantees that all concept steering vectors for a given binary concept converge toward a single direction as training proceeds, regardless of the specific context used to estimate them (arXiv:2403.03867). Joint embedding and unembedding training further aligns the two matrices so that both the input and output representations of the concept converge to the same direction.
