---
aliases:
- Stanford Question Answering Dataset
- SQuAD 1.1
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:squad
  type: dataset
  status: canonical
area: datasets
related:
- '[[2410.17234--semantic-entropy-abstention]]'
- '[[triviaqa]]'
- '[[bioasq]]'
- '[[natural-questions]]'
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
  target: '[[bioasq]]'
  target_id: dataset:bioasq
  confidence: medium
- type: related_to
  target: '[[natural-questions]]'
  target_id: dataset:natural-questions
  confidence: medium
- type: related_to
  target: '[[abstention]]'
  target_id: term:abstention
  confidence: medium
---

A reading comprehension dataset of crowdsourced QA pairs over Wikipedia articles (Rajpurkar et al. 2016). In abstention fine-tuning experiments it is used closed-book with passage context stripped, turning it into a factoid knowledge test.

**Why it matters here:** Used as the primary out-of-distribution test dataset in the Mult experiment (training on TriviaQA, BioASQ, NQ; evaluating on SQuAD), making it the canonical cross-domain generalization probe in this paper.

**Lineage:** Rajpurkar et al. (arXiv:1606.05250, EMNLP 2016). Used in closed-book abstention evaluation by Tjandra et al. (arXiv:2410.17234).
