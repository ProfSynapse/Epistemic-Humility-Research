---
aliases:
- Injection detection and concept naming dissociate
- Detection and forced identification peak at different depths
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:detection-and-identification-use-distinct-introspection-circuits
  type: mechanism
  status: canonical
cause: "Detection asks whether an internal perturbation occurred, while forced identification asks the model to decode the injected concept after an affirmative prefill."
effect: "Detection depends on middle-layer MLP gates, whereas concept identification peaks later and remains comparatively intact when detection gates are ablated."
polarity: decouples
related:
- '[[2603.21396--mechanisms-introspective-awareness]]'
- '[[concept-injection-introspection-test]]'
- '[[evidence-carriers-suppress-default-negative-gates]]'
relationships:
- type: supported_by
  target: '[[2603.21396--mechanisms-introspective-awareness]]'
  target_id: paper:2603.21396
  confidence: high
- type: related_to
  target: '[[concept-injection-introspection-test]]'
  target_id: method:concept-injection-introspection-test
  confidence: high
- type: related_to
  target: '[[evidence-carriers-suppress-default-negative-gates]]'
  target_id: mechanism:evidence-carriers-suppress-default-negative-gates
  confidence: high
---

Detection peaks for middle-layer injections, while forced identification rises
toward later layers. Ablating negative-answer gate features sharply reduces
detection but only modestly reduces forced identification. The paper therefore
treats detection and semantic readout as partly independent computations rather
than one shared ability.
