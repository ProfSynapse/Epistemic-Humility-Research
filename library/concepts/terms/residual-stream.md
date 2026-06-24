---
aliases:
- transformer residual stream
tags:
- kg/term
- concept
- term
kg:
  id: term:residual-stream
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[logit-lens]]'
- '[[tuned-lens]]'
- '[[linear-representation-hypothesis]]'
relationships:
- type: related_to
  target: '[[logit-lens]]'
  target_id: method:logit-lens
- type: related_to
  target: '[[tuned-lens]]'
  target_id: method:tuned-lens
- type: related_to
  target: '[[linear-representation-hypothesis]]'
  target_id: term:linear-representation-hypothesis
---

The residual stream is the running sum that accumulates across all components of
a transformer forward pass: the token embedding, each attention head output, and
each MLP layer output all write additively to this shared vector at each
sequence position. Because the residual stream is purely additive, any linear
function of the final hidden state decomposes exactly into a sum of linear
contributions from every upstream component, making it the primary substrate for
mechanistic interpretability analysis. Techniques such as the logit lens and
tuned lens read the residual stream at each layer to trace how the model's
predictions evolve from input to output.

**Why it matters here:** Probing the residual stream for uncertainty or
self-knowledge signals requires that those signals reside as approximately linear
subspaces in this stream, so understanding its additive structure is a
prerequisite for interpreting linear-probe and activation-patching results on
calibration-relevant features.

**Lineage:** foundational infrastructure concept in transformer mechanistic
interpretability; related to [[logit-lens]] and [[tuned-lens]] as readout
methods, and to [[linear-representation-hypothesis]] as the theoretical premise
that meaningful features form linear subspaces within it.
