---
aliases:
- Trigger tokens enable safety fine-tuning to generalize to jailbreaks
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:trigger-tokens-drive-safety-generalization
  type: mechanism
  status: canonical
cause: "Presence of surface-form trigger tokens in jailbreak prompts that strongly activate the [[dominant-refusal-direction]] during safety fine-tuning"
effect: "Safety fine-tuning generalises to new jailbreak attack instances that share those trigger tokens, even when the attack framing is novel"
polarity: enables
related:
- '[[2502.09674--hidden-dimensions-llm-alignment-multi-dimensional-analysis]]'
- '[[dominant-refusal-direction]]'
- '[[trigger-removal-attack]]'
- '[[safety-residual-space]]'
relationships:
- type: supported_by
  target: '[[2502.09674--hidden-dimensions-llm-alignment-multi-dimensional-analysis]]'
  target_id: paper:2502.09674
  confidence: high
- type: related_to
  target: '[[dominant-refusal-direction]]'
  target_id: term:dominant-refusal-direction
- type: related_to
  target: '[[trigger-removal-attack]]'
  target_id: method:trigger-removal-attack
- type: related_to
  target: '[[safety-residual-space]]'
  target_id: term:safety-residual-space
---

Safety fine-tuning teaches the model to strongly activate the dominant refusal direction in response to certain surface-level cues (trigger tokens) associated with harmful intent. When new jailbreaks include those same tokens, the fine-tuning generalises because the dominant direction is already associated with those surface features (arXiv:2502.09674). Conversely, attacks that systematically remove or paraphrase trigger tokens bypass the trained refusal signal, explaining why [[trigger-removal-attack]] strategies can succeed even against heavily safety-tuned models.
