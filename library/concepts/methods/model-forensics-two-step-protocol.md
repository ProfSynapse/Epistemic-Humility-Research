---
aliases:
- Model forensics two-step protocol
- Read-CoT-then-intervene protocol
- Two-step forensics protocol
tags:
- kg/method
- concept
- method
kg:
  id: method:model-forensics-two-step-protocol
  type: method
  status: canonical
area: methods
related:
- '[[2606.26071--model-forensics-investigating-whether-concerning-behavior-reflects]]'
- '[[model-forensics]]'
- '[[counterfactual-environment-intervention]]'
- '[[cot-monitorability]]'
relationships:
- type: proposed_by
  target: '[[2606.26071--model-forensics-investigating-whether-concerning-behavior-reflects]]'
  target_id: paper:2606.26071
  confidence: high
- type: related_to
  target: '[[model-forensics]]'
  target_id: term:model-forensics
  confidence: high
- type: related_to
  target: '[[counterfactual-environment-intervention]]'
  target_id: method:counterfactual-environment-intervention
  confidence: high
- type: related_to
  target: '[[cot-monitorability]]'
  target_id: term:cot-monitorability
  confidence: medium
---

A baseline investigative protocol for distinguishing genuine misalignment from benign causes (confusion, miscalibration, overzealousness). Two steps, iterated as needed: (1) read the chain of thought to generate hypotheses about what drives a behavior, then (2) edit the prompt or environment to test those hypotheses, leaning on confirmed behavioral predictions and counterfactual effect sizes as evidence.

**Why it matters here:** it operationalizes the epistemic-humility stance that a concerning action does not by itself establish malign intent: motivation is underdetermined by behavior, so the protocol gathers the further evidence needed before attributing misalignment.

**Lineage:** combines CoT reading (subject to faithfulness limits) with environment counterfactuals; pairs with [[analysis-of-competing-hypotheses]] to weigh rival explanations and with [[sentence-resampling]] / [[repeated-resampling]] to localize causal trace segments.
