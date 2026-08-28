---
aliases:
- Larger models show stronger activation introspection
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:model-scale-improves-activation-introspection
  type: mechanism
  status: canonical
cause: "Increasing model size within the evaluated Llama 3.2 and Gemma 4 families."
effect: "Generally higher [[sentence-localization-introspection]] and [[strength-comparison-introspection]] accuracy for controlled residual-stream perturbations."
polarity: increases
related:
- '[[2607.14111--introspection-fine-tuning-ift-training-small-llms]]'
- '[[sentence-localization-introspection]]'
- '[[strength-comparison-introspection]]'
- '[[llama-3-2-1b]]'
- '[[llama-3-2-3b]]'
- '[[gemma-4]]'
relationships:
- type: supported_by
  target: '[[2607.14111--introspection-fine-tuning-ift-training-small-llms]]'
  target_id: paper:2607.14111
  confidence: high
- type: related_to
  target: '[[sentence-localization-introspection]]'
  target_id: metric:sentence-localization-introspection
  confidence: high
- type: related_to
  target: '[[strength-comparison-introspection]]'
  target_id: metric:strength-comparison-introspection
  confidence: high
- type: related_to
  target: '[[llama-3-2-1b]]'
  target_id: model:llama-3-2-1b
  confidence: high
- type: related_to
  target: '[[llama-3-2-3b]]'
  target_id: model:llama-3-2-3b
  confidence: high
- type: related_to
  target: '[[gemma-4]]'
  target_id: model:gemma-4
  confidence: high
---

Figure 2 reports that models above 1B parameters perform reliably above chance
on both relative introspection metrics, while the 1B model performs at or below
chance and accuracy generally rises with scale. The trend is not strictly
monotonic, so this mechanism records a supported tendency rather than a sharp
universal threshold.
