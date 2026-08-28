---
aliases:
- Refusal ablation reveals suppressed injection detection
- Denial training inhibits introspective reports
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:refusal-direction-suppresses-concept-injection-detection
  type: mechanism
  status: canonical
cause: "A post-trained model retains a [[refusal-direction]] and a learned disposition to deny having thoughts or internal states."
effect: "True injection-detection reports are suppressed along with false positives, while [[directional-ablation]] or targeted preference training increases true detection."
polarity: decreases
related:
- '[[2603.21396--mechanisms-introspective-awareness]]'
- '[[refusal-direction]]'
- '[[directional-ablation]]'
- '[[direct-preference-optimization]]'
- '[[concept-injection-introspection-test]]'
relationships:
- type: supported_by
  target: '[[2603.21396--mechanisms-introspective-awareness]]'
  target_id: paper:2603.21396
  confidence: high
- type: related_to
  target: '[[refusal-direction]]'
  target_id: term:refusal-direction
  confidence: high
- type: related_to
  target: '[[directional-ablation]]'
  target_id: method:directional-ablation
  confidence: high
- type: related_to
  target: '[[direct-preference-optimization]]'
  target_id: method:direct-preference-optimization
  confidence: high
- type: related_to
  target: '[[concept-injection-introspection-test]]'
  target_id: method:concept-injection-introspection-test
  confidence: high
---

Refusal-direction ablation increases true detection across five tested models,
and a magnitude-matched random direction does not reproduce the effect. DPO on
preferences that affirm internal states also raises true detection while style
controls do not. The gate circuit persists after refusal ablation, so the paper
treats refusal as an output suppressor rather than the detection circuit itself.
