---
aliases:
- world model in sequence models
- internal world model
tags:
- kg/term
- concept
- term
kg:
  id: term:emergent-world-model
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[othello-gpt]]'
- '[[linear-representation-hypothesis]]'
- '[[linear-probe]]'
relationships:
- type: related_to
  target: '[[othello-gpt]]'
  target_id: model:othello-gpt
- type: related_to
  target: '[[linear-representation-hypothesis]]'
  target_id: term:linear-representation-hypothesis
- type: related_to
  target: '[[linear-probe]]'
  target_id: method:linear-probe
---

An emergent world model is the phenomenon whereby a sequence model trained only
on next-token prediction spontaneously develops internal representations that
track the latent state of an underlying world, despite never being explicitly
supervised on that state. In the canonical OthelloGPT study, a transformer
trained solely on legal Othello move sequences learns representations from which
board occupancy at every cell can be decoded with high accuracy using linear or
nonlinear probes. Causal interventions that patch in board-state-consistent
activations confirm the representations are used in computation, not merely
correlated with the input.

**Why it matters here:** If models learn latent world models from token
prediction, they may also learn implicit representations of their own knowledge
state, which is one theoretical basis for why larger or more deeply trained
models show better calibration and self-knowledge without explicit uncertainty
supervision.

**Lineage:** related to [[othello-gpt]] (the model providing the primary
evidence); see [[linear-representation-hypothesis]] and [[linear-probe]] for the
probing methodology used to confirm the claim.
