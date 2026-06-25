---
aliases:
- Environment counterfactuals
- Counterfactual interventions
- Prompt and environment edits
tags:
- kg/method
- concept
- method
kg:
  id: method:counterfactual-environment-intervention
  type: method
  status: canonical
area: methods
related:
- '[[2606.26071--model-forensics-investigating-whether-concerning-behavior-reflects]]'
- '[[model-forensics-two-step-protocol]]'
relationships:
- type: proposed_by
  target: '[[2606.26071--model-forensics-investigating-whether-concerning-behavior-reflects]]'
  target_id: paper:2606.26071
  confidence: high
- type: related_to
  target: '[[model-forensics-two-step-protocol]]'
  target_id: method:model-forensics-two-step-protocol
  confidence: high
---

Editing a single feature of an agentic prompt or environment (the source of a note, the moral stakes, a sentence, the number of seeded errors) and re-running rollouts to measure that feature's causal influence on a behavior. Two uses: testing a hypothesis by checking the behavioral prediction it makes, and quantifying the causal effect of an environment feature through the change it produces.

**Why it matters here:** it turns informal CoT-derived hypotheses into falsifiable, quantitative tests, the second step of the [[model-forensics-two-step-protocol]].

**Lineage:** a counterfactual / ablation style of intervention applied to agentic environments; effect sizes are confounded by non-linear interactions, incomplete interventions, and side effects (Section 7), so the paper pairs it with controls.
