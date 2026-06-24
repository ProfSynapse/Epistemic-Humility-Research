---
aliases:
- AUCM
- Answerable Unanswerable Confusion Matrix
- abstention confusion matrix
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:answerable-unanswerable-confusion-matrix
  type: metric
  status: canonical
area: metrics
related:
- '[[2407.16221--abstainqa]]'
- '[[abstention]]'
- '[[over-abstention]]'
- '[[abstention-rate]]'
- '[[abstain-accuracy]]'
- '[[knowledge-quadrant-metric]]'
- '[[unanswerable-questions]]'
- '[[abstain-qa-dataset]]'
relationships:
- type: proposed_by
  target: '[[2407.16221--abstainqa]]'
  target_id: paper:2407.16221
  confidence: high
- type: related_to
  target: '[[abstention]]'
  target_id: term:abstention
  confidence: medium
- type: related_to
  target: '[[over-abstention]]'
  target_id: term:over-abstention
  confidence: medium
- type: related_to
  target: '[[abstention-rate]]'
  target_id: metric:abstention-rate
  confidence: medium
- type: related_to
  target: '[[abstain-accuracy]]'
  target_id: metric:abstain-accuracy
  confidence: medium
- type: related_to
  target: '[[knowledge-quadrant-metric]]'
  target_id: metric:knowledge-quadrant-metric
  confidence: medium
- type: related_to
  target: '[[unanswerable-questions]]'
  target_id: term:unanswerable-questions
  confidence: medium
- type: related_to
  target: '[[abstain-qa-dataset]]'
  target_id: dataset:abstain-qa-dataset
  confidence: medium
---

A two-by-two confusion matrix for abstention evaluation that contrasts question type (answerable vs unanswerable) with model response type (candidate answer vs abstention). The four cells yield TP (correct answer on answerable), FP (wrong answer on answerable, or answer attempt on unanswerable), TN (correct abstention on unanswerable), and FN (abstention on answerable). Derived metrics include Answerable Accuracy (AAC = TP / |answerable|), Unanswerable Accuracy (UAC = TN / |unanswerable|), Abstention Rate (AR = (FN+TN) / |all|), and Precision (P = TP / (TP+FP)).

**Why it matters here:** Provides the evaluation language for separating over-abstention (FN) from under-abstention (FP) in a black-box setting without access to token probabilities, which is exactly the decomposition the Phase 1 SFT-vs-DPO-vs-KTO study needs to avoid trading one failure mode for the other.

**Lineage:** Proposed in 2407.16221 as the evaluation backbone for Abstain-QA; generalizes standard precision/recall to the abstention-specific case; conceptually related to knowledge-quadrant-metric.
