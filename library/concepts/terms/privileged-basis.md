---
aliases:
- basis-aligned representation
- privileged basis representation
tags:
- kg/term
- concept
- term
kg:
  id: term:privileged-basis
  type: term
  status: canonical
area: mechanistic-interpretability
related: []
relationships: []
---

A privileged basis is a property of a neural network representation in which there exists a natural coordinate system, typically the neuron-activation directions after a nonlinearity such as ReLU, that the network is architecturally encouraged to align its learned features with. When a privileged basis exists, individual neurons tend toward monosemanticity: each neuron responds to one concept rather than a mixture. By contrast, residual stream activations (before a nonlinearity) have no privileged basis, and features there can orient in arbitrary directions.

**Why it matters here:** The presence or absence of a privileged basis determines whether neuron-level probing is a valid analysis technique. Calibration and self-knowledge probes applied to residual-stream activations must account for the absence of privileged basis, while MLP-output probes can exploit it.

**Lineage:** foundational term in mechanistic interpretability; closely related to [[superposition-hypothesis]], [[monosemanticity]], and [[sparse-autoencoder]] (which recovers monosemantic features from non-privileged-basis spaces).
