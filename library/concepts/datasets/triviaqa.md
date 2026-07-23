---
aliases:
- TriviaQA dataset
- trivia QA
- Trivia QA
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:triviaqa
  type: dataset
  status: canonical
area: datasets
---

TriviaQA (Joshi et al., 2017) is a large-scale reading-comprehension and
open-domain question-answering benchmark consisting of trivia questions paired
with verified answers and supporting evidence documents. The dataset contains
roughly 95,000 question-answer pairs across a Web and Wikipedia domain split.

**Why it matters here:** The alignment-for-honesty framework (and, by extension,
the locked training-regimen SFT-vs-DPO-vs-KTO study) uses TriviaQA as its primary evaluation
and training corpus: 87,622 training samples are used to construct the
model-specific idk fine-tuning sets, and 11,313 test samples serve as the
evaluation set for [[honesty-score]], [[prudence-score]], and
[[over-conservativeness-score]]. TriviaQA's factoid structure makes it well
suited for probing the boundary between known and unknown knowledge.

**Lineage:** no formal concept lineage; used across the epistemic-humility
literature as a standard factoid QA testbed alongside [[selfaware]] and
[[pararel]].
