---
aliases:
- Prompt-only ReFT limits generation overhead
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:prompt-only-reft-bounds-decoding-overhead
  type: mechanism
  status: canonical
cause: "[[representation-finetuning]] applies learned interventions only to a fixed set of prompt positions."
effect: "The intervention cost is incurred while populating the initial key-value cache rather than at every generated token."
polarity: limits
related:
- '[[2404.03592--reft-representation-finetuning-language-models]]'
- '[[representation-finetuning]]'
- '[[low-rank-linear-subspace-reft]]'
relationships:
- type: supported_by
  target: '[[2404.03592--reft-representation-finetuning-language-models]]'
  target_id: paper:2404.03592
  confidence: high
- type: related_to
  target: '[[representation-finetuning]]'
  target_id: method:representation-finetuning
  confidence: high
- type: related_to
  target: '[[low-rank-linear-subspace-reft]]'
  target_id: method:low-rank-linear-subspace-reft
  confidence: high
---

The paper's inference analysis applies LoReFT only to prompt tokens. In the
reported LLaMA-1 7B condition with rank 8 at ten layers on the last prompt
token, the added runtime for generating 256 tokens was about 0.05 seconds.
