---
aliases:
- selector faithfulness
- causal selector faithfulness
- neuron selector validity
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:selector-causal-faithfulness
  type: metric
  status: canonical
area: mechanistic-interpretability
related:
- '[[neuron-selector-causal-audit]]'
- '[[circuit-faithfulness]]'
- '[[2607.05355--faithfulness-refusal-causal-audit-neuron-selectors]]'
relationships:
- type: proposed_by
  target: '[[2607.05355--faithfulness-refusal-causal-audit-neuron-selectors]]'
  target_id: paper:2607.05355
  confidence: high
- type: related_to
  target: '[[circuit-faithfulness]]'
  target_id: metric:circuit-faithfulness
  confidence: medium
- type: measured_by
  target: '[[neuron-selector-causal-audit]]'
  target_id: method:neuron-selector-causal-audit
  confidence: high
---

Selector causal faithfulness is the degree to which a component-ranking method correctly predicts causal effects under intervention. In the Faithfulness to Refusal audit, it is operationalized by LeRF/MoRF curves and behavior-level refusal edits: a faithful selector should identify low-ranked rows that can be removed safely and high-ranked rows whose removal strongly changes the target behavior or loss.

**Why it matters here:** This metric captures the gap between a plausible explanation and a causally tested explanation. It is directly relevant when deciding whether an abstention, uncertainty, or refusal feature is a real control handle or merely a correlated diagnostic.

**Lineage:** proposed in [[2607.05355--faithfulness-refusal-causal-audit-neuron-selectors]]; related to [[circuit-faithfulness]] but evaluates selector rankings rather than a completed circuit.
