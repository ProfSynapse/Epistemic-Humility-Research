---
aliases:
- gaslight control for steering awareness
- prompt versus activation intervention discrimination
- three-way introspection source test
tags:
- kg/method
- concept
- method
kg:
  id: method:three-way-intervention-source-control
  type: method
  status: canonical
area: verification
related:
- '[[2605.26242--can-llms-introspect-reality-check]]'
- '[[concept-injection-introspection-test]]'
- '[[second-order-computation-condition]]'
- '[[activation-steering]]'
relationships:
- type: proposed_by
  target: '[[2605.26242--can-llms-introspect-reality-check]]'
  target_id: paper:2605.26242
  confidence: high
- type: variation_of
  target: '[[concept-injection-introspection-test]]'
  target_id: method:concept-injection-introspection-test
  confidence: high
- type: related_to
  target: '[[second-order-computation-condition]]'
  target_id: term:second-order-computation-condition
  confidence: high
- type: related_to
  target: '[[activation-steering]]'
  target_id: method:activation-steering
  confidence: high
---

The three-way intervention source control compares an ordinary trial, a residual-stream concept injection, and a prompt-only instruction that biases the model toward the same concept. The response options separately name no intervention, input manipulation, and activation intervention, forcing activation-specific monitoring and generic irregularity detection to make different predictions.

**Why it matters here:** The added prompt-only condition tests whether binary injection reports identify the intervention source or only an unusual state.

**Lineage:** It extends the [[concept-injection-introspection-test]] with a matched input intervention. Passing this source test would still not by itself establish second-order computation.
