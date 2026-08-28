---
aliases:
- Introspection Fine-Tuning
- IFT
- activation introspection fine-tuning
tags:
- kg/method
- concept
- method
kg:
  id: method:introspection-fine-tuning
  type: method
  status: canonical
area: methods
related:
- '[[2607.14111--introspection-fine-tuning-ift-training-small-llms]]'
- '[[concept-injection-introspection-test]]'
- '[[supervised-finetuning]]'
- '[[activation-steering]]'
- '[[sentence-localization-introspection]]'
- '[[strength-comparison-introspection]]'
relationships:
- type: proposed_by
  target: '[[2607.14111--introspection-fine-tuning-ift-training-small-llms]]'
  target_id: paper:2607.14111
  confidence: high
- type: variation_of
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
  confidence: high
- type: derived_from
  target: '[[concept-injection-introspection-test]]'
  target_id: method:concept-injection-introspection-test
  confidence: high
- type: related_to
  target: '[[activation-steering]]'
  target_id: method:activation-steering
  confidence: high
- type: related_to
  target: '[[sentence-localization-introspection]]'
  target_id: metric:sentence-localization-introspection
  confidence: high
- type: related_to
  target: '[[strength-comparison-introspection]]'
  target_id: metric:strength-comparison-introspection
  confidence: high
---

Introspection Fine-Tuning is supervised fine-tuning on sentence-localization
examples generated from a model's own forward passes while a concept vector is
injected into selected residual-stream token positions. Training minimizes
cross-entropy on the correct sentence index and can optionally supervise the
injected concept name.

**Why it matters here:** IFT provides a direct intervention for training models
to report controlled internal perturbations. It therefore offers a concrete
bridge between activation-level causal interventions and learned self-monitoring.

**Lineage:** IFT trains the controlled activation-perturbation setting introduced
by the [[concept-injection-introspection-test]]. It is a variation of
[[supervised-finetuning]] whose examples are produced through
[[activation-steering]], and whose primary readout is
[[sentence-localization-introspection]].
