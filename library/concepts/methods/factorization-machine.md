---
aliases:
- FM
- second-order factorization machine
- Factorization Machine (FM)
tags:
- kg/method
- concept
- method
kg:
  id: method:factorization-machine
  type: method
  status: canonical
area: mechanistic-interpretability
related:
- '[[sae-causal-feature-discovery]]'
relationships:
- type: required_by
  target: '[[sae-causal-feature-discovery]]'
  target_id: method:sae-causal-feature-discovery
---

A factorization machine is a supervised learning model that captures pairwise
feature interactions via low-dimensional latent embedding vectors assigned to
each input feature. Given a feature vector x, the model scores all pairs (i, j)
through the inner product of their latent embeddings, adding O(kd) parameters
rather than O(d^2), making it tractable for high-dimensional sparse inputs. In
the refusal-circuit context, it is fit to SAE feature activations (harmful vs
benign prompts) to discover nonlinear dependencies among refusal-relevant features
that a linear probe would fail to identify.

**Why it matters here:** Nonlinear feature co-activation patterns are one plausible
mechanism behind the hydra-effect redundancy in safety circuits; factorization
machines provide an interpretable, low-parameter tool for exposing such interactions
without exhaustive pairwise search.

**Lineage:** a general machine-learning method adopted as a component of
[[sae-causal-feature-discovery]]; not specific to language models.
