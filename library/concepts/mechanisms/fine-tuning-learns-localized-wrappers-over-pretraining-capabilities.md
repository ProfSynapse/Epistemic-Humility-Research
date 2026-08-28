---
aliases:
- Fine-tuning learns localized wrappers over pretraining capabilities
- Local wrapper preserves pretrained computation
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:fine-tuning-learns-localized-wrappers-over-pretraining-capabilities
  type: mechanism
  status: canonical
cause: "Continued fine-tuning at a smaller learning rate adapts a model to a downstream task for which an existing pretraining capability is relevant."
effect: "A localized transformation changes output behavior while information associated with the earlier capability remains recoverable from intermediate representations."
polarity: modulates
related:
- '[[2311.12786--mechanistically-analyzing-effects-fine-tuning-procedurally-defined]]'
- '[[fine-tuning-wrapper]]'
- '[[linear-probe]]'
relationships:
- type: supported_by
  target: '[[2311.12786--mechanistically-analyzing-effects-fine-tuning-procedurally-defined]]'
  target_id: paper:2311.12786
  confidence: high
- type: related_to
  target: '[[fine-tuning-wrapper]]'
  target_id: term:fine-tuning-wrapper
  confidence: high
- type: related_to
  target: '[[linear-probe]]'
  target_id: method:linear-probe
  confidence: high
---

In the paper's Tracr and PCFG experiments, targeted pruning restores the earlier behavior and linear probes still decode information needed for the pretraining task. The TinyStories experiments provide a smaller language-model extension in which twist-related information declines only slightly after behavioral suppression.
