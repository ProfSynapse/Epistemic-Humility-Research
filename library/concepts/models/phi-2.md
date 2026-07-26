---
aliases:
- Phi-2
- Microsoft Phi-2
tags:
- kg/model
- concept
- model
kg:
  id: model:phi-2
  type: model
  status: canonical
area: mechanistic-interpretability
related:
- '[[2406.16254--confidence-regulation-neurons-language-models]]'
relationships:
- type: studied_by
  target: '[[2406.16254--confidence-regulation-neurons-language-models]]'
  target_id: paper:2406.16254
  confidence: medium
---

Phi-2 is Microsoft's 2.7B-parameter decoder-only transformer trained
predominantly on curated "textbook-quality" synthetic and filtered web data,
released in December 2023.

**Why it matters here:** Stolfo et al. use Phi-2 as one of the model families
in which they confirm the presence of entropy neurons, showing the
LayerNorm-mediated confidence-regulation mechanism recurs in a
synthetic-data-trained model distinct from GPT-2/Pythia/LLaMA2's more standard
web-scale pretraining mixtures.

**Lineage:** no formal derivation edges recorded in this vault yet.
