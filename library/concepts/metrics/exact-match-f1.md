---
aliases:
- EM
- exact match
- token-level F1
- SQuAD EM/F1
- word-level F1
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:exact-match-f1
  type: metric
  status: canonical
area: metrics
related:
- '[[1705.03551--triviaqa-dataset]]'
- '[[triviaqa]]'
- '[[squad]]'
- '[[abstain-accuracy]]'
- '[[reliable-accuracy]]'
- '[[self-knowledge-f1]]'
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
  target: '[[squad]]'
  target_id: dataset:squad
  confidence: medium
- type: related_to
  target: '[[abstain-accuracy]]'
  target_id: metric:abstain-accuracy
  confidence: medium
- type: related_to
  target: '[[reliable-accuracy]]'
  target_id: metric:reliable-accuracy
  confidence: medium
- type: related_to
  target: '[[self-knowledge-f1]]'
  target_id: metric:self-knowledge-f1
  confidence: medium
---

The pair of evaluation metrics standard in extractive reading comprehension benchmarks. Exact Match (EM) counts the fraction of predicted answers that match any acceptable answer string exactly after normalization. Token-level F1 measures the overlap between predicted and gold answer tokens, averaged over questions. For datasets with multiple valid aliases (such as TriviaQA), all aliases are tried and the maximum score is taken.

**Why it matters here:** EM and F1 are the primary metrics reported on TriviaQA and the baselines therein. Because TriviaQA answers are mostly Wikipedia entity titles with many valid aliases, EM is less penalized by surface variation than on span-extraction datasets. The metrics define what 'getting it right' means in downstream abstention experiments: a model that abstains on a question it would have gotten wrong improves effective EM.

**Lineage:** Introduced for SQuAD by Rajpurkar et al. (arXiv:1606.05250); adopted verbatim by TriviaQA (arXiv:1705.03551).
