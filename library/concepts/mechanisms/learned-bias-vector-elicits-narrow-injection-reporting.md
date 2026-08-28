---
aliases:
- Additive bias exposes latent injection detection
- Bias steering amplifies narrow introspective reports
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:learned-bias-vector-elicits-narrow-injection-reporting
  type: mechanism
  status: canonical
cause: "Training one additive MLP-output bias vector on injected and control examples shifts the model toward a conditional affirmative reporting style."
effect: "Detection and identification of held-out concept injections increase, without comparable gains on broader self-knowledge tasks and with losses on some faithfulness tests."
polarity: increases
related:
- '[[2603.21396--mechanisms-introspective-awareness]]'
- '[[activation-steering]]'
- '[[concept-injection-introspection-test]]'
- '[[evidence-carriers-suppress-default-negative-gates]]'
relationships:
- type: supported_by
  target: '[[2603.21396--mechanisms-introspective-awareness]]'
  target_id: paper:2603.21396
  confidence: high
- type: related_to
  target: '[[activation-steering]]'
  target_id: method:activation-steering
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

The learned vector suppresses the dominant default-negative gate and raises
held-out detection without increasing false positives in that evaluation. Its
logit-lens profile contains a generic affirmative component. It does not improve
HaluEval, reduces chain-of-thought faithfulness, and worsens prefill detection,
so the paper interprets it as narrow elicitation rather than general
introspective improvement.
