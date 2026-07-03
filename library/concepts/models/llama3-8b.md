---
aliases:
- Llama3-8B
- Meta Llama 3 8B
- LLaMA 3-8B
tags:
- kg/model
- concept
- model
kg:
  id: model:llama3-8b
  type: model
  status: canonical
area: models
related:
- '[[llama-3-1-8b-instruct]]'
- '[[llama-2]]'
relationships:
- type: related_to
  target: '[[llama-3-1-8b-instruct]]'
  target_id: model:llama-3-1-8b-instruct
- type: related_to
  target: '[[llama-2]]'
  target_id: model:llama-2
---

LLaMA 3 8B is Meta's 8-billion-parameter open-weight language model from the LLaMA 3 family, trained on approximately 15 trillion tokens of web and curated data. It is available in both base and instruction-following variants and is widely used as a testbed for mechanistic interpretability experiments due to its tractable size, public weight release, and broad adoption as a reference point in the literature.

**Why it matters here:** It serves as a primary evaluation host in probing experiments that test whether latent truth representations (predicted by [[truth-co-occurrence-hypothesis]]) are linearly readable from hidden states, establishing that epistemic-humility-relevant structure is present in a concrete, openly available model without requiring proprietary access.

**Lineage:** member of the LLaMA 3 family; the instruction-following derivative is [[llama-3-1-8b-instruct]]; related to the LLaMA 2 line via [[llama-2]].
