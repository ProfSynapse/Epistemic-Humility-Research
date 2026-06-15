---
aliases:
- ParaRel dataset
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:pararel
  type: dataset
  status: canonical
area: datasets
---

ParaRel is a factual question-answering benchmark covering relational knowledge
expressed through paraphrased cloze-style prompts. Each relation (e.g., "born
in", "capital of") is represented by multiple surface-form variations that probe
the same underlying fact, making it useful for assessing the consistency and
boundary of a model's knowledge.

**Why it matters here:** R-Tuning uses ParaRel as a primary evaluation dataset
for refusal-aware answering, measuring both in-domain and out-of-domain
performance of models trained to say "I don't know" when uncertain.

**Lineage:** a standalone factual-probe benchmark; no direct lineage to other
atoms in this vault.
