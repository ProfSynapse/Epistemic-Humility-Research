---
aliases:
- pythia-70m
- Pythia-70M
tags:
- kg/model
- concept
- model
kg:
  id: model:pythia-70m
  type: model
  status: canonical
area: mechanistic-interpretability
related:
- '[[pythia-suite]]'
- '[[sparse-feature-circuits]]'
- '[[sparse-autoencoder]]'
relationships:
- type: derived_from
  target: '[[pythia-suite]]'
  target_id: model:pythia-suite
- type: related_to
  target: '[[sparse-feature-circuits]]'
  target_id: method:sparse-feature-circuits
- type: related_to
  target: '[[sparse-autoencoder]]'
  target_id: method:sparse-autoencoder
---

Pythia-70M is a 70-million-parameter decoder-only transformer from the Pythia
suite (EleutherAI), trained on The Pile with fully open weights and
checkpoints. Its small scale makes exhaustive attribution feasible: indirect
effects can be computed exactly over the full computation graph rather than
approximated, enabling ground-truth validation of circuit-discovery methods.

**Why it matters here:** Pythia-70M is the primary model used for sparse
feature circuit discovery and evaluation, because its size permits exact
indirect-effect computation that serves as a validation target for attribution
approximations.

**Lineage:** member of [[pythia-suite]]; used as the base model for
[[sparse-feature-circuits]] and paired [[sparse-autoencoder]] training.
