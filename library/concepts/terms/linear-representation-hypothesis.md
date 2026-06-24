---
aliases:
- linearity hypothesis
tags:
- kg/term
- concept
- term
kg:
  id: term:linear-representation-hypothesis
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[linear-probe]]'
- '[[superposition-hypothesis]]'
- '[[residual-stream]]'
relationships:
- type: related_to
  target: '[[linear-probe]]'
  target_id: method:linear-probe
- type: related_to
  target: '[[superposition-hypothesis]]'
  target_id: term:superposition-hypothesis
- type: related_to
  target: '[[residual-stream]]'
  target_id: term:residual-stream
---

The linear representation hypothesis, tracing to Mikolov et al. (2013), holds that neural network features are encoded as linear directions in activation space: meaningful concepts correspond to vectors such that arithmetic on those vectors corresponds to semantic operations. If true, the [[residual-stream]] decomposition into per-component contributions is tractable, because each component's effect on a feature is a simple dot product. The hypothesis is empirically supported in many settings but violated when [[superposition-hypothesis]] packs more features than dimensions allow.

**Why it matters here:** It is the theoretical foundation for [[steering-vector]], [[known-unknown-direction]], [[truth-direction]], and [[refusal-direction]] approaches to epistemic-humility research: all assume that honesty-relevant features live in identifiable linear subspaces.

**Lineage:** motivates [[linear-probe]] as an analysis tool; stands in tension with [[superposition-hypothesis]], which predicts that directions are shared across features in high-capacity models.
