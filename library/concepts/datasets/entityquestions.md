---
aliases:
- EntityQ
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:entityquestions
  type: dataset
  status: canonical
area: datasets
---

EntityQuestions is a closed-book QA benchmark that converts factual (subject,
relation, object) triplets from Wikidata into natural-language question-answer
pairs, spanning biographical, geographical, and other knowledge types. Evaluation
is purely closed-book: no retrieved context is provided, so accuracy directly
reflects the model's parametric knowledge.

**Why it matters here:** The fine-tuning and evaluation corpus used in the
unfamiliar-finetuning-examples study (2405.05904) is drawn from EntityQuestions,
making it the primary dataset through which the relationship between SFT data
familiarity and hallucination is measured.

**Lineage:** no formal lineage; see [[unfamiliar-finetuning-examples]] for the
partitioning scheme applied to its training split.
