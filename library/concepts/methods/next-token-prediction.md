---
aliases:
- NTP objective
- causal language modeling
- autoregressive language model objective
- Next-Token Prediction
tags:
- kg/method
- concept
- method
kg:
  id: method:next-token-prediction
  type: method
  status: canonical
area: mechanistic-interpretability
related:
- '[[implicit-bias-gradient-descent]]'
relationships: []
---

Next-token prediction (NTP) is the standard pretraining objective for autoregressive language models: given a sequence of preceding tokens, the model is trained to minimise the cross-entropy loss between its softmax output distribution and the true next token. This formulation couples the output vocabulary (the unembedding matrix) directly to internal representations, making the softmax-cross-entropy loss the central shaping force on representation geometry. Because every training step pushes the hidden state of the preceding context toward predicting a specific token, NTP implicitly organises concept representations around statistical co-occurrence structure in the training corpus.

**Why it matters here:** The geometry induced by NTP (which directions cluster, which are orthogonal) partially determines whether internal confidence signals are linearly readable, a prerequisite for the answerability and correctness axes central to this project's epistemic-humility probes.

**Lineage:** no formal derivation edges; see [[implicit-bias-gradient-descent]] for the theoretical analysis of what gradient descent on this objective converges to.
