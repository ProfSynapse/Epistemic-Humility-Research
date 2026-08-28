---
aliases:
- Injected concepts can be detected before verbalization
- Residual perturbations causally ground introspective reports
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:concept-injection-grounds-internal-state-self-report
  type: mechanism
  status: canonical
cause: "A semantic concept vector is injected into the residual stream while the model is prompted to detect an unexpected internal state."
effect: "On a minority of trials, the model reports the intervention and identifies its concept before mentioning that concept in sampled output."
polarity: causes
related:
- '[[2603.21396--mechanisms-introspective-awareness]]'
- '[[lindsey-2025--emergent-introspective-awareness-large-language-models]]'
- '[[concept-injection-introspection-test]]'
- '[[introspective-awareness]]'
- '[[activation-steering]]'
relationships:
- type: supported_by
  target: '[[2603.21396--mechanisms-introspective-awareness]]'
  target_id: paper:2603.21396
  confidence: medium
- type: supported_by
  target: '[[lindsey-2025--emergent-introspective-awareness-large-language-models]]'
  target_id: paper:lindsey-2025-introspection
  confidence: high
- type: related_to
  target: '[[concept-injection-introspection-test]]'
  target_id: method:concept-injection-introspection-test
  confidence: high
- type: related_to
  target: '[[introspective-awareness]]'
  target_id: term:introspective-awareness
  confidence: high
- type: related_to
  target: '[[activation-steering]]'
  target_id: method:activation-steering
  confidence: high
---

Claude Opus 4.1 reached about 20 percent correct detection and identification
at its best layer and strength. [[2603.21396--mechanisms-introspective-awareness]]
adds open-weight circuit evidence that injection-dependent features causally
affect detection. Failures remain common, and the open-weight study does not
include a matched prompt-only source control.
