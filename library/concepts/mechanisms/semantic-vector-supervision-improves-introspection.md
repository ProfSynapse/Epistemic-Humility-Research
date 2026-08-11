---
aliases:
- Semantic concept vectors provide a stronger introspection training signal than Gaussian noise
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:semantic-vector-supervision-improves-introspection
  type: mechanism
  status: canonical
cause: "Training [[introspection-fine-tuning]] with semantic [[steering-vector]] perturbations instead of Gaussian-noise perturbations."
effect: "Higher [[sentence-localization-introspection]] accuracy, especially for the Llama 3.2 1B model."
polarity: increases
related:
- '[[2607.14111--introspection-fine-tuning-ift-training-small-llms]]'
- '[[introspection-fine-tuning]]'
- '[[steering-vector]]'
- '[[sentence-localization-introspection]]'
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
  target: '[[steering-vector]]'
  target_id: term:steering-vector
  confidence: high
- type: related_to
  target: '[[sentence-localization-introspection]]'
  target_id: metric:sentence-localization-introspection
  confidence: high
---

Table 2 shows average localization accuracy of 60.6 percent for random-layer
semantic-vector IFT on Llama 1B, compared with 14.9 percent for random-layer
Gaussian IFT. Section 4.3 interprets this gap as evidence that semantic
perturbations teach a more generalizable introspective signal than random noise.
