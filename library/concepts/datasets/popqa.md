---
aliases:
- PopQA
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:popqa
  type: dataset
  status: canonical
area: datasets
related:
- '[[2212.10511--popqa-when-not-to-trust]]'
- '[[triviaqa]]'
- '[[entityquestions]]'
relationships:
- type: related_to
  target: '[[triviaqa]]'
  target_id: dataset:triviaqa
  confidence: medium
- type: related_to
  target: '[[entityquestions]]'
  target_id: dataset:entityquestions
  confidence: medium
---

PopQA (Mallen et al., 2023) is an open-domain question-answering benchmark of
entity-centric factoid questions built to probe knowledge of long-tail entities.
Each question is annotated with the subject entity's popularity (Wikipedia page
views), which lets studies separate performance on common entities from
performance on rare ones, where parametric recall is weakest and abstention is
most warranted.

**Why it matters here:** PopQA's long-tail design makes it a natural testbed for
knowledge-boundary and abstention behaviour: rare entities are exactly where a
calibrated model should hedge or decline. It is used in the epistemic-humility
literature, and as one of the four Q&A benchmarks in Grad Detect, alongside
[[triviaqa]] (factual recall), [[sciq]] (scientific knowledge), and
[[truthfulqa]] (adversarial truthfulness).

**Lineage:** a long-tail factoid QA testbed in the same family as [[triviaqa]]
and [[entityquestions]]; its distinguishing feature is the per-question entity
popularity annotation.
