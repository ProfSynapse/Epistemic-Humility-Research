---
aliases:
- BioASQ QA
- BioASQ biomedical QA
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:bioasq
  type: dataset
  status: canonical
area: datasets
related:
- '[[2410.17234--semantic-entropy-abstention]]'
- '[[triviaqa]]'
- '[[natural-questions]]'
- '[[squad]]'
- '[[abstention]]'
relationships:
- type: proposed_by
  target: '[[2410.17234--semantic-entropy-abstention]]'
  target_id: paper:2410.17234
  confidence: high
- type: related_to
  target: '[[triviaqa]]'
  target_id: dataset:triviaqa
  confidence: medium
- type: related_to
  target: '[[natural-questions]]'
  target_id: dataset:natural-questions
  confidence: medium
- type: related_to
  target: '[[squad]]'
  target_id: dataset:squad
  confidence: medium
- type: related_to
  target: '[[abstention]]'
  target_id: term:abstention
  confidence: medium
---

A biomedical question-answering dataset from the BioASQ challenge (Tsatsaronis et al. 2015). Contains factoid questions about biomedical topics drawn from PubMed abstracts. Used in abstention fine-tuning evaluation under closed-book settings.

**Why it matters here:** A domain-specific QA dataset covering biomedical facts, complementing general-knowledge datasets (TriviaQA, NQ) to test whether abstention fine-tuning generalizes across domains.

**Lineage:** Tsatsaronis et al. (BMC Bioinformatics 2015). Used in abstention fine-tuning evaluation by Tjandra et al. (arXiv:2410.17234).
