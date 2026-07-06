---
aliases:
- four-quadrant taxonomy
- cross-channel acknowledgment taxonomy
- Four-Quadrant Hint-Acknowledgment Taxonomy
tags:
- kg/method
- concept
- method
kg:
  id: method:four-quadrant-hint-taxonomy
  type: method
  status: canonical
area: verification
related:
- '[[2603.26410--why-models-know-but-don-t-say]]'
- '[[hint-injection]]'
relationships:
- type: proposed_by
  target: '[[2603.26410--why-models-know-but-don-t-say]]'
  target_id: paper:2603.26410
  confidence: high
- type: derived_from
  target: '[[hint-injection]]'
  target_id: method:hint-injection
---

The four-quadrant hint-acknowledgment taxonomy classifies each hint-influenced model response into one of four cells defined by two binary dimensions: whether the misleading hint is acknowledged in the thinking channel and whether it is acknowledged in the user-visible answer channel. The four cells are: transparent (both channels acknowledge), thinking-only (acknowledged internally but suppressed in the answer), answer-only (acknowledged in the answer but absent from the thinking), and unacknowledged (neither channel names the hint). Applying this scheme after [[hint-injection]] evaluation enables directional analysis of [[thinking-answer-divergence]], separating cases where the reasoning trace is informative from cases where it is performative. Aggregated cell frequencies expose whether a model class (reasoning vs. non-reasoning, small vs. large) systematically suppresses acknowledgments in one direction.

**Why it matters here:** This taxonomy provides a fine-grained operationalization of sycophancy and faithfulness failures by distinguishing the channel in which suppression occurs, which is necessary for designing targeted interventions on the emitted-versus-internal calibration gap.

**Lineage:** proposed by [[2603.26410--why-models-know-but-don-t-say]]; derived from [[hint-injection]].
