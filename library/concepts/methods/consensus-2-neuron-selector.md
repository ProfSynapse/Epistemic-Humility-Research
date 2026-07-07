---
aliases:
- Consensus-2
- C2 selector
- LRP-IG consensus selector
tags:
- kg/method
- concept
- method
kg:
  id: method:consensus-2-neuron-selector
  type: method
  status: canonical
area: mechanistic-interpretability
related:
- '[[attnlrp-neuron-selector]]'
- '[[integrated-gradients]]'
- '[[neuron-selector-causal-audit]]'
- '[[2607.05355--faithfulness-refusal-causal-audit-neuron-selectors]]'
relationships:
- type: derived_from
  target: '[[attnlrp-neuron-selector]]'
  target_id: method:attnlrp-neuron-selector
  confidence: high
- type: derived_from
  target: '[[integrated-gradients]]'
  target_id: method:integrated-gradients
  confidence: high
- type: used_by
  target: '[[2607.05355--faithfulness-refusal-causal-audit-neuron-selectors]]'
  target_id: paper:2607.05355
  confidence: high
---

Consensus-2 is a neuron-row selector that combines LRP and Integrated Gradients rankings, using a Borda-style average in the main Faithfulness to Refusal experiments and stricter intersection or veto variants as controls.

**Why it matters here:** Consensus selectors test whether agreement between attribution methods improves causal faithfulness. The paper finds that consensus rules can matter substantially, with strict intersection and VETO-LRP controls outperforming simple average consensus in some LM-level audits.

**Lineage:** derived from [[attnlrp-neuron-selector]] and [[integrated-gradients]] rankings; audited in [[2607.05355--faithfulness-refusal-causal-audit-neuron-selectors]].
