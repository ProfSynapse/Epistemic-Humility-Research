---
aliases:
- LLaMA-2-7B
- Meta LLaMA 2
- LLaMA-2
tags:
- kg/model
- concept
- model
kg:
  id: model:llama-2
  type: model
  status: canonical
area: mechanistic-interpretability
related: []
relationships: []
---

LLaMA-2 is Meta's open-weight autoregressive language model family, released in 2023 at sizes from 7B to 70B parameters, trained on approximately 2 trillion tokens of public text. The family includes both base (pretrained) and chat (RLHF-finetuned) variants, making it a standard testbed for mechanistic-interpretability experiments that compare base versus aligned representations. Empirical work has used LLaMA-2 to validate that embedding and unembedding steering vectors for matching concepts are nontrivially aligned and that semantically unrelated concepts are nearly orthogonal, confirming theoretical predictions from the latent conditional model.

**Why it matters here:** LLaMA-2 serves as a standard reference checkpoint for validating whether internal readout axes (answerability, correctness) found in one model family generalise to independently trained architectures, and it provides a controlled baseline for ablation studies on how post-training affects confidence geometry.

**Lineage:** no formal derivation edges.
