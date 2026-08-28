---
aliases:
- Boundless Distributed Alignment Search
- Boundless DAS
tags:
- kg/method
- concept
- method
kg:
  id: method:boundless-distributed-alignment-search
  type: method
  status: canonical
area: methods
related:
- '[[2305.08809--interpretability-scale-identifying-causal-mechanisms-alpaca]]'
- '[[causal-intervention]]'
- '[[causal-abstraction]]'
relationships:
- type: proposed_by
  target: '[[2305.08809--interpretability-scale-identifying-causal-mechanisms-alpaca]]'
  target_id: paper:2305.08809
  confidence: high
- type: variation_of
  target: '[[causal-intervention]]'
  target_id: method:causal-intervention
  confidence: medium
- type: related_to
  target: '[[causal-abstraction]]'
  target_id: term:causal-abstraction
  confidence: high
---

Boundless DAS learns an orthogonal rotation and differentiable masks that align high-level causal variables with subspaces of a neural representation. Annealing turns the soft masks into discrete subspace boundaries for intervention-based evaluation.

**Why it matters here:** The method searches for compact internal variables that causally control model outputs, and it supplies transfer and negative-control tests for the alignment.

**Lineage:** It extends Distributed Alignment Search by learning subspace dimensionality instead of selecting it by manual search.
