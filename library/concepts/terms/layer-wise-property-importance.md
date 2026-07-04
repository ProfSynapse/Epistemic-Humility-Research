---
aliases:
- layer importance
- layer-level property localization
- Layer-wise Property Importance
tags:
- kg/term
- concept
- term
kg:
  id: term:layer-wise-property-importance
  type: term
  status: canonical
area: mechanistic-interpretability
introduced-by: "[[2006.00995--amnesic-probing-behavioral-explanation-amnesic-counterfactuals]]"
related:
- "[[2006.00995--amnesic-probing-behavioral-explanation-amnesic-counterfactuals]]"
- "[[amnesic-probing]]"
- "[[linear-probe]]"
relationships:
- type: proposed_by
  target: "[[2006.00995--amnesic-probing-behavioral-explanation-amnesic-counterfactuals]]"
  target_id: paper:2006.00995
  confidence: high
- type: related_to
  target: "[[amnesic-probing]]"
  target_id: method:amnesic-probing
- type: related_to
  target: "[[linear-probe]]"
  target_id: method:linear-probe
---

Layer-wise property importance is the differential causal contribution of a
linguistic or semantic property at each transformer layer to downstream task
performance. It is measured by applying an amnesic intervention (INLP nullspace
projection) at a chosen intermediate layer, running the model forward from that
edited state, and recording the resulting performance drop. This causal profile
can diverge substantially from the layer-localization profile produced by standard
probing accuracy, because probing reveals where a property is encoded whereas the
amnesic profile reveals where it is consumed.

**Why it matters here:** Knowing which layers causally use an uncertainty axis
(rather than merely encode it) tells us where a steering or readout intervention
must be applied to influence model behavior. If the epistemic-signal consumption
is concentrated at early or mid layers, late-layer interventions will be
ineffective regardless of how accurately a probe reads the representation there.

**Lineage:** operationalized by [[amnesic-probing]]; contrasts with standard
[[linear-probe]] localization, which can yield conflicting layer rankings.
