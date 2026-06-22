---
aliases:
- AtP
- linear IE approximation
- integrated-gradients patching
tags:
- kg/method
- concept
- method
kg:
  id: method:attribution-patching
  type: method
  status: canonical
area: mechanistic-interpretability
related:
- '[[activation-patching]]'
- '[[integrated-gradients]]'
- '[[sparse-feature-circuits]]'
- '[[indirect-object-identification]]'
relationships:
- type: derived_from
  target: '[[activation-patching]]'
  target_id: method:activation-patching
- type: variation_of
  target: '[[integrated-gradients]]'
  target_id: method:integrated-gradients
- type: required_by
  target: '[[sparse-feature-circuits]]'
  target_id: method:sparse-feature-circuits
---

Attribution patching is a scalable linear approximation to activation patching
for estimating the indirect causal effect of a model component on a behavior.
Rather than running a separate forward pass per component, it uses a first-order
Taylor expansion (or the more accurate integrated-gradients variant) to score
all nodes and edges in a single backward pass. This reduces the per-circuit
search cost from O(components) forward passes to one, making circuit discovery
tractable at the scale of full SAE feature vocabularies.

**Why it matters here:** Attribution patching makes it computationally feasible
to identify which internal representations causally mediate a model behavior, a
prerequisite for testing whether epistemic states such as uncertainty or
known-unknown discrimination are circuit-localizable rather than distributed.

**Lineage:** derives from [[activation-patching]]; uses [[integrated-gradients]]
as its more accurate variant; required by [[sparse-feature-circuits]] to scale
to SAE feature graphs.
