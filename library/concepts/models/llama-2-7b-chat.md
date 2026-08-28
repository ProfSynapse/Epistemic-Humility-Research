---
aliases:
- Llama-2-7b-chat
- Llama 2 7B Chat
- Llama-2-chat-7b
tags:
- kg/model
- concept
- model
kg:
  id: model:llama-2-7b-chat
  type: model
  status: canonical
area: models
related:
- '[[2511.05408--steering-language-models-weight-arithmetic]]'
- '[[llama-2]]'
relationships:
- type: related_to
  target: '[[2511.05408--steering-language-models-weight-arithmetic]]'
  target_id: paper:2511.05408
  confidence: high
- type: variation_of
  target: '[[llama-2]]'
  target_id: model:llama-2
  confidence: high
---

Llama-2-7b-chat is the seven-billion-parameter chat-tuned checkpoint in Meta's Llama 2 family. Fierro and Roger use it for the GSM8K fine-tuning and refusal-restoration experiment because newer models saturate the math benchmark.

**Why it matters here:** It provides a controlled model where capability gains and safety drift can both be observed after task-specific fine-tuning.

**Lineage:** A chat-tuned variant of [[llama-2]].
