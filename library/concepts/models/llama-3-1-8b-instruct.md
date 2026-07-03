---
aliases:
- Llama-3.1-8B-Instruct
- Llama 3 8B
- Llama 3.1 8B
- Llama 3.1 8B Instruct
tags:
- kg/model
- concept
- model
kg:
  id: model:llama-3-1-8b-instruct
  type: model
  status: canonical
area: models
related:
- '[[llama3-8b]]'
relationships:
- type: related_to
  target: '[[llama3-8b]]'
  target_id: model:llama3-8b
---

Llama-3.1-8B-Instruct is Meta's instruction-tuned 8-billion-parameter language model from the Llama 3.1 release family, trained with RLHF-style alignment on top of the Llama 3.1 base. The instruction-tuning installs a safety residual space with a dominant refusal direction and several secondary directions that collectively regulate refusal behavior, making it a natural subject for mechanistic safety analysis. It supports a 128k-token context window and is publicly available, enabling reproducible mechanistic experiments.

**Why it matters here:** As the primary subject for safety fine-tuning (supervised safety fine-tuning and DPO) and mechanistic decomposition of the refusal subspace in several studies, this checkpoint is the empirical anchor for claims about the [[dominant-refusal-direction]], [[safety-residual-space]], and [[trigger-removal-attack]] analyses.

**Lineage:** instruction-tuned descendant of the Llama 3.1 base; see [[llama3-8b]] for the earlier 8B checkpoint used in related mechanistic studies.
