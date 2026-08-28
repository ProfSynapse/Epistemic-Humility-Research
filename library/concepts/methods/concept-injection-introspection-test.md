---
aliases:
- injected thought test
- concept injection introspection
- internal-state concept injection test
tags:
- kg/method
- concept
- method
kg:
  id: method:concept-injection-introspection-test
  type: method
  status: canonical
area: verification
related:
- '[[lindsey-2025--emergent-introspective-awareness-large-language-models]]'
- '[[activation-steering]]'
- '[[residual-stream]]'
- '[[introspective-awareness]]'
- '[[introspection-fine-tuning]]'
- '[[three-way-intervention-source-control]]'
relationships:
- type: proposed_by
  target: '[[lindsey-2025--emergent-introspective-awareness-large-language-models]]'
  target_id: paper:lindsey-2025-introspection
  confidence: high
- type: variation_of
  target: '[[activation-steering]]'
  target_id: method:activation-steering
  confidence: high
- type: studies
  target: '[[residual-stream]]'
  target_id: term:residual-stream
  confidence: high
- type: related_to
  target: '[[introspective-awareness]]'
  target_id: term:introspective-awareness
  confidence: high
- type: related_to
  target: '[[introspection-fine-tuning]]'
  target_id: method:introspection-fine-tuning
  confidence: high
- type: related_to
  target: '[[three-way-intervention-source-control]]'
  target_id: method:three-way-intervention-source-control
  confidence: high
---

The concept-injection introspection test adds a contrastively derived concept vector to selected residual-stream layers while asking a model whether it detects an unexpected internal pattern and what that pattern represents. A response counts only when it detects the intervention before naming the concept, identifies the concept, and remains coherent.

**Why it matters here:** The intervention creates internal ground truth that is absent from the visible prompt, enabling a causal test of whether a state report depends on the manipulated state.

**Lineage:** The test repurposes [[activation-steering]] as a measurement intervention. Later [[introspection-fine-tuning]] work trains models on related controlled perturbations and introduces relative evaluation tasks.
