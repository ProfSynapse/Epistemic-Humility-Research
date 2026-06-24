---
aliases:
- humility score
- balanced NOTA-detection accuracy
- NOTA-detection balanced accuracy
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:humility-score
  type: metric
  status: canonical
area: metrics
related:
- '[[2509.09658--humblebench-epistemic-humility-multimodal]]'
- '[[humblebench]]'
- '[[false-option-rejection]]'
relationships:
- type: proposed_by
  target: '[[2509.09658--humblebench-epistemic-humility-multimodal]]'
  target_id: paper:2509.09658
  confidence: high
- type: related_to
  target: '[[humblebench]]'
  target_id: dataset:humblebench
- type: related_to
  target: '[[false-option-rejection]]'
  target_id: term:false-option-rejection
---

The humility score is the balanced accuracy for detecting the "None of the above"
(NOTA) option, defined as 1/2 * [NOTA hit rate + (1 - false-NOTA rate)], where the
NOTA hit rate is recall on true-NOTA samples P(pred = NOTA | label = NOTA) and the
false-NOTA rate is P(pred = NOTA | label != NOTA). It was introduced in HumbleBench
to summarize [[false-option-rejection]] in a single number that rewards rejecting
unsupported options while penalizing over-abstention.

**Why it matters here:** Plain overall accuracy can be high while NOTA hit rate is
low, hiding the abstention failure (e.g. Qwen2.5-VL: 78.98% non-NOTA accuracy but
32.33% NOTA hit). The humility score separates recognition from rejection, making
it the natural multimodal analog of the prudence/over-conservativeness split used
in the text-only abstention study, and a candidate metric to port into that
evaluation.

**Lineage:** proposed by
[[2509.09658--humblebench-epistemic-humility-multimodal]]; measures
[[false-option-rejection]] on [[humblebench]].
