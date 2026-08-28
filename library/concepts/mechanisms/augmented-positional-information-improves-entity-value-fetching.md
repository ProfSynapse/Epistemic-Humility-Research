---
aliases:
- Augmented positional information improves entity value fetching
- Fine-tuning sharpens positional entity tracking
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:augmented-positional-information-improves-entity-value-fetching
  type: mechanism
  status: canonical
cause: "Arithmetic fine-tuning enhances positional information transmitted by shared and added entity-tracking circuit components."
effect: "Value Fetcher heads locate the queried object's position more effectively and raise entity-tracking accuracy."
polarity: enables
related:
- '[[2402.14811--fine-tuning-enhances-existing-mechanisms-case-study]]'
- '[[cross-model-activation-patching]]'
- '[[entity-tracking-box-task]]'
relationships:
- type: supported_by
  target: '[[2402.14811--fine-tuning-enhances-existing-mechanisms-case-study]]'
  target_id: paper:2402.14811
  confidence: high
- type: related_to
  target: '[[cross-model-activation-patching]]'
  target_id: method:cross-model-activation-patching
  confidence: high
- type: related_to
  target: '[[entity-tracking-box-task]]'
  target_id: dataset:entity-tracking-box-task
  confidence: high
---

Cross-model patching identifies the Position Transmitter and especially the Value Fetcher as improved steps. Transplanting their activations from arithmetic-tuned models into LLaMA-7B raises base performance, and Value Fetcher patching recovers the fine-tuned accuracy.
