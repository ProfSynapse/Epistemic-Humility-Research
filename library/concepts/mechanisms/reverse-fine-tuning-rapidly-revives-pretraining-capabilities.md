---
aliases:
- Reverse fine-tuning rapidly revives pretraining capabilities
- Retained capabilities return sample-efficiently
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:reverse-fine-tuning-rapidly-revives-pretraining-capabilities
  type: mechanism
  status: canonical
cause: "A fine-tuned model is trained again on data requiring a capability that it acquired during pretraining but no longer expresses behaviorally."
effect: "The earlier behavior returns in fewer training iterations than in a comparison model that did not acquire the capability during pretraining."
polarity: enables
related:
- '[[2311.12786--mechanistically-analyzing-effects-fine-tuning-procedurally-defined]]'
- '[[reverse-fine-tuning]]'
- '[[fine-tuning-wrapper]]'
relationships:
- type: supported_by
  target: '[[2311.12786--mechanistically-analyzing-effects-fine-tuning-procedurally-defined]]'
  target_id: paper:2311.12786
  confidence: high
- type: related_to
  target: '[[reverse-fine-tuning]]'
  target_id: method:reverse-fine-tuning
  confidence: high
- type: related_to
  target: '[[fine-tuning-wrapper]]'
  target_id: term:fine-tuning-wrapper
  confidence: high
---

The paper reports faster restoration in PCFG, Tracr, and TinyStories settings than in comparison initializations that lack the same pretraining history. This is evidence for retention under the tested protocols, not a general proof that fine-tuning never removes capabilities.
