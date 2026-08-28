---
aliases:
- Qwen2.5-1.5B
- Qwen2.5-1.5B-Instruct
- Qwen/Qwen2.5-1.5B-Instruct
tags:
- kg/model
- concept
- model
kg:
  id: model:qwen2-5-1-5b
  type: model
  status: canonical
area: models
related:
- '[[2607.19317--circuitkit-circuit-discovery-evaluation-application-toolkit-mechanistic]]'
- '[[qwen3]]'
relationships:
- type: studied_by
  target: '[[2607.19317--circuitkit-circuit-discovery-evaluation-application-toolkit-mechanistic]]'
  target_id: paper:2607.19317
  confidence: high
- type: related_to
  target: '[[qwen3]]'
  target_id: model:qwen3
  confidence: medium
---

Qwen2.5-1.5B is a compact Qwen language model with rotary embeddings, grouped-query attention, and untied embeddings. CircuitKIT studies the base-sized family in cross-family discovery and uses the instruction-tuned checkpoint for its custom-data refusal circuit case study.

**Why it matters here:** It provides a small instruction-tuned model on which paired and clean-only circuit routes can be compared for a safety-relevant behavior.

**Lineage:** A Qwen 2.5 family model, related to the later [[qwen3]] family used elsewhere in this research program.
