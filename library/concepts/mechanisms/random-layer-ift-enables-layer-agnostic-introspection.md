---
aliases:
- Random-layer IFT promotes layer-agnostic introspection
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:random-layer-ift-enables-layer-agnostic-introspection
  type: mechanism
  status: canonical
cause: "Sampling the perturbation layer during [[introspection-fine-tuning]] instead of always injecting at one fixed layer."
effect: "Better average [[sentence-localization-introspection]] across evaluation layers and strengths."
polarity: enables
related:
- '[[2607.14111--introspection-fine-tuning-ift-training-small-llms]]'
- '[[introspection-fine-tuning]]'
- '[[sentence-localization-introspection]]'
- '[[residual-stream]]'
relationships:
- type: supported_by
  target: '[[2607.14111--introspection-fine-tuning-ift-training-small-llms]]'
  target_id: paper:2607.14111
  confidence: high
- type: related_to
  target: '[[introspection-fine-tuning]]'
  target_id: method:introspection-fine-tuning
  confidence: high
- type: related_to
  target: '[[sentence-localization-introspection]]'
  target_id: metric:sentence-localization-introspection
  confidence: high
- type: related_to
  target: '[[residual-stream]]'
  target_id: term:residual-stream
  confidence: high
---

Section 4.3 and Table 5 show higher localization accuracy for random-layer
semantic IFT than fixed-layer semantic IFT at all three tested Llama sizes. The
authors interpret randomization as forcing a strategy that transfers across
residual-stream depths rather than monitoring one training-time layer.
