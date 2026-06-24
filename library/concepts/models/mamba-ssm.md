---
aliases:
- Mamba-2.8b
- selective SSM
- Mamba LM
- Mamba (State Space Model LM)
tags:
- kg/model
- concept
- model
kg:
  id: model:mamba-ssm
  type: model
  status: canonical
area: mechanistic-interpretability
related:
- '[[gpt-2-xl]]'
- '[[gpt-j-6b]]'
relationships:
- type: related_to
  target: '[[gpt-2-xl]]'
  target_id: model:gpt-2-xl
- type: related_to
  target: '[[gpt-j-6b]]'
  target_id: model:gpt-j-6b
---

Mamba is a family of language models built on selective state space models (SSMs) that replace the attention and MLP blocks of transformers with a single MambaBlock using input-dependent parameterization. Unlike transformers, Mamba processes sequences with linear-time recurrence rather than quadratic self-attention, yet achieves competitive language modeling perplexity. Mamba-2.8b is the largest variant studied in mechanistic interpretability work comparing SSM and transformer factual-recall circuits.

**Why it matters here:** Mamba provides a non-attention architecture baseline for probing whether factual-recall mechanisms (subject enrichment, attribute extraction) are universal or attention-specific, which bears on how broadly mechanistic findings about knowledge localization generalize.

**Lineage:** related to [[gpt-2-xl]] and [[gpt-j-6b]] as transformer counterparts used in parallel factual-recall studies.
