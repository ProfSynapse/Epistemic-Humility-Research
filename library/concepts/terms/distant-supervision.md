---
aliases:
- distantly supervised
- distant supervision for QA
- automatic evidence labeling
tags:
- kg/term
- concept
- term
kg:
  id: term:distant-supervision
  type: term
  status: canonical
area: terms
related:
- '[[1705.03551--triviaqa-dataset]]'
- '[[triviaqa]]'
- '[[abstention]]'
- '[[knowledge-boundary]]'
- '[[unanswerable-questions]]'
relationships:
- type: proposed_by
  target: '[[1705.03551--triviaqa-dataset]]'
  target_id: paper:1705.03551
  confidence: high
- type: related_to
  target: '[[triviaqa]]'
  target_id: dataset:triviaqa
  confidence: medium
- type: related_to
  target: '[[abstention]]'
  target_id: term:abstention
  confidence: medium
- type: related_to
  target: '[[knowledge-boundary]]'
  target_id: term:knowledge-boundary
  confidence: medium
- type: related_to
  target: '[[unanswerable-questions]]'
  target_id: term:unanswerable-questions
  confidence: medium
---

A training paradigm in which labels are inferred automatically from weak heuristics rather than direct annotation. In reading comprehension, this means assuming that a document containing the answer string does answer the question, without human verification of whether the document actually supplies sufficient reasoning context.

**Why it matters here:** TriviaQA evidence documents are distantly supervised: the presence of the answer string in a document is taken as proof that the document answers the question, but human verification shows this assumption holds only roughly 75-80% of the time. Knowing that roughly 20-25% of training triples are mislabeled in this way is critical for interpreting low EM baselines and designing abstention-aware evaluation splits.

**Lineage:** Term from Mintz et al. (ACL 2009) for relation extraction; adapted to reading comprehension by Joshi et al. (arXiv:1705.03551).
