---
aliases:
- Conversational Question Answering
- CoQA dataset
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:coqa
  type: dataset
  status: canonical
area: datasets
related:
- '[[2302.09664--semantic-uncertainty-kuhn]]'
- '[[triviaqa]]'
- '[[semantic-entropy]]'
- '[[auroc]]'
relationships:
- type: proposed_by
  target: '[[2302.09664--semantic-uncertainty-kuhn]]'
  target_id: paper:2302.09664
  confidence: high
- type: related_to
  target: '[[triviaqa]]'
  target_id: dataset:triviaqa
  confidence: medium
- type: related_to
  target: '[[semantic-entropy]]'
  target_id: method:semantic-entropy
  confidence: medium
- type: related_to
  target: '[[auroc]]'
  target_id: metric:auroc
  confidence: medium
---

An open-book conversational question answering benchmark (Reddy et al. 2019) in which models answer a sequence of questions about a supporting passage. Development split contains approximately 8000 questions. Answers are longer and more variable than TriviaQA, making exact matching difficult and length-normalisation important for entropy estimation.

**Why it matters here:** Standard open-book QA evaluation used alongside TriviaQA in semantic entropy and related uncertainty estimation papers. Provides a contrast case to closed-book QA: its longer, more variable answers mean length-normalised entropy performs comparably to semantic entropy at high temperatures.

**Lineage:** Reddy, Chen, and Manning (2019). Used as a benchmark in Kuhn et al. (arXiv:2302.09664) and related uncertainty estimation work.
