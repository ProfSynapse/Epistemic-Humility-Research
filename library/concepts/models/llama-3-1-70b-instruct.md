---
aliases:
- Llama-3.1-70B-Instruct
- Llama 3.1 70B
tags:
- kg/model
- concept
- model
kg:
  id: model:llama-3-1-70b-instruct
  type: model
  status: canonical
area: models
related:
- '[[llama-3-1-8b-instruct]]'
- '[[2509.22067--rogue-scalpel-activation-steering-compromises-llm-safety]]'
relationships:
- type: related_to
  target: '[[llama-3-1-8b-instruct]]'
  target_id: model:llama-3-1-8b-instruct
  confidence: high
- type: used_by
  target: '[[2509.22067--rogue-scalpel-activation-steering-compromises-llm-safety]]'
  target_id: paper:2509.22067
  confidence: high
---

Llama-3.1-70B-Instruct is Meta's instruction-tuned 70-billion-parameter checkpoint from the Llama 3.1 release family, used as the largest-scale model in cross-family activation-steering safety evaluations.

**Why it matters here:** [[2509.22067--rogue-scalpel-activation-steering-compromises-llm-safety]] uses Llama-3.1-70B-Instruct to test whether steering vulnerabilities scale with model size; the aggregated universal steering vector achieves 50.4% harmful compliance on it, double the matched random-direction rate.

**Lineage:** the 70B-parameter checkpoint in the same Llama 3.1 release family as [[llama-3-1-8b-instruct]].
