---
aliases:
- Activation steering can confound binary introspection detection through affirmative bias
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:activation-steering-induces-affirmative-response-bias
  type: mechanism
  status: canonical
cause: "Injecting a [[steering-vector]] into a small model's [[residual-stream]] while eliciting a binary yes-or-no report."
effect: "A content-independent increase in affirmative logits that makes apparent binary introspection detection indistinguishable from response bias."
polarity: increases
related:
- '[[2607.14111--introspection-fine-tuning-ift-training-small-llms]]'
- '[[activation-steering]]'
- '[[steering-vector]]'
- '[[residual-stream]]'
relationships:
- type: supported_by
  target: '[[2607.14111--introspection-fine-tuning-ift-training-small-llms]]'
  target_id: paper:2607.14111
  confidence: high
- type: related_to
  target: '[[activation-steering]]'
  target_id: method:activation-steering
  confidence: high
- type: related_to
  target: '[[steering-vector]]'
  target_id: term:steering-vector
  confidence: high
- type: related_to
  target: '[[residual-stream]]'
  target_id: term:residual-stream
  confidence: high
---

In Figure 1 and Section 2.3.1, the adjusted yes-versus-no logit shift for an
introspection question tracks the same shift for factual-no controls with
correlation r = 0.999 across 40 layer-strength settings. The near-zero net
signal indicates that binary detection is not isolating sensitivity to the
injected concept in the tested small-model setting.
