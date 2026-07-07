---
aliases:
- causal audit of neuron selectors
- neuron selector audit
- selector causal audit
tags:
- kg/method
- concept
- method
kg:
  id: method:neuron-selector-causal-audit
  type: method
  status: canonical
area: mechanistic-interpretability
related:
- '[[2607.05355--faithfulness-refusal-causal-audit-neuron-selectors]]'
- '[[neuron-row-masking]]'
- '[[selector-causal-faithfulness]]'
- '[[causal-intervention]]'
relationships:
- type: proposed_by
  target: '[[2607.05355--faithfulness-refusal-causal-audit-neuron-selectors]]'
  target_id: paper:2607.05355
  confidence: high
- type: uses
  target: '[[neuron-row-masking]]'
  target_id: method:neuron-row-masking
  confidence: high
- type: measures
  target: '[[selector-causal-faithfulness]]'
  target_id: metric:selector-causal-faithfulness
  confidence: high
- type: related_to
  target: '[[causal-intervention]]'
  target_id: method:causal-intervention
  confidence: high
---

A neuron selector causal audit tests whether a ranked list of neuron rows is causally meaningful by intervening on the rows and measuring the resulting change in model behavior. In the Faithfulness to Refusal paper, selectors are audited with Least-Relevant-First and Most-Relevant-First sweeps: a faithful selector should allow low-ranked rows to be masked with little damage and should make the model fail faster when high-ranked rows are masked.

**Why it matters here:** Epistemic-humility work often relies on probes, directions, or selectors that may be merely correlational. A causal audit forces those explanations to predict what happens under intervention, separating faithful internal evidence from stable but behaviorally irrelevant rankings.

**Lineage:** introduced for neuron-row selector validation in [[2607.05355--faithfulness-refusal-causal-audit-neuron-selectors]]; operationally a form of [[causal-intervention]] using [[neuron-row-masking]].
