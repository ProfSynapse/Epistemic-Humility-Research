---
aliases:
- margin score
- representation margin
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:factuality-margin-score
  type: metric
  status: canonical
area: mechanistic-interpretability
related:
- '[[2601.20834--linear-representations-language-models-can-change-dramatically]]'
- '[[linear-probe]]'
relationships:
- type: proposed_by
  target: '[[2601.20834--linear-representations-language-models-can-change-dramatically]]'
  target_id: paper:2601.20834
  confidence: high
- type: derived_from
  target: '[[linear-probe]]'
  target_id: method:linear-probe
---

The factuality margin score is a scalar summary of probe-classification quality
along a linear concept direction: for each question, the probe logit for the
factual answer minus the probe logit for the non-factual answer, summed over the
question set. A positive margin indicates the identified direction correctly
separates factual from non-factual answers; a negative margin indicates the
direction has inverted relative to ground truth, meaning the probe now classifies
factual answers as non-factual. The metric captures not just accuracy but the
signed orientation of the representation direction, which is needed to detect
direction flips in multi-turn settings.

**Why it matters here:** Epistemic-humility probing relies on linear directions
being stably oriented toward the correct class; the factuality margin score
provides an operational test of whether a probe direction remains faithful across
contexts or conversation turns.

**Lineage:** derived from [[linear-probe]] as a signed aggregation of probe logit
differences rather than a threshold-based accuracy count.
