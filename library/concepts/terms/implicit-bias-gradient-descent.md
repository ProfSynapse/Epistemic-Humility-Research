---
aliases:
- gradient descent implicit bias
- max-margin implicit bias
- implicit regularisation
- Implicit Bias of Gradient Descent
tags:
- kg/term
- concept
- term
kg:
  id: term:implicit-bias-gradient-descent
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[linear-representation-hypothesis]]'
relationships:
- type: required_by
  target: '[[linear-representation-hypothesis]]'
  target_id: term:linear-representation-hypothesis
---

The implicit bias of gradient descent refers to the tendency of gradient descent applied to separable data under cross-entropy or exponential loss to converge, in the limit, toward the max-margin solution even without explicit regularisation. This property means that training on the next-token-prediction objective does not produce arbitrary solutions; instead, the optimiser systematically steers embedding and unembedding vectors toward geometrically well-structured configurations. Theoretical results in the linear-representations literature exploit this bias to prove that concept embeddings and unembedding vectors become aligned in the training limit (analogous to Theorems 4 and 5 style arguments), with the alignment growing as training continues.

**Why it matters here:** The implicit bias result grounds claims that internal confidence directions are not arbitrary artifacts of initialisation but are structurally induced by the training objective, supporting the plausibility of linearly reading epistemic signals from residual streams.

**Lineage:** required by [[linear-representation-hypothesis]] (the bias is one of the mechanisms that produces linear concept geometry under NTP training).
