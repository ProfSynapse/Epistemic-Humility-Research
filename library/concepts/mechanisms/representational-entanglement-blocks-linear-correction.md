---
aliases:
- Representational Entanglement Blocks Linear Correction
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:representational-entanglement-blocks-linear-correction
  type: mechanism
  status: canonical
cause: "A failure-mode direction (e.g., Overthinking) in the residual stream sharing most of its variance with task-relevant computation (specificity ratio <= 0.152)"
effect: "Fixed linear steering along that direction cannot correct the failure without damaging task accuracy: uniform shared-direction steering costs -12.1pp and LEACE-style concept erasure costs -3.6pp (p=0.01), while 10 random-direction erasures of equal rank cost only +0.3pp"
polarity: prevents
related:
- '[[2605.05715--decodable-but-not-corrected-fixed-residual-stream]]'
- '[[leace]]'
- '[[specificity-ratio]]'
- '[[decodability-steerability-gap]]'
relationships:
- type: supported_by
  target: '[[2605.05715--decodable-but-not-corrected-fixed-residual-stream]]'
  target_id: paper:2605.05715
  confidence: high
- type: related_to
  target: '[[leace]]'
  target_id: method:leace
- type: related_to
  target: '[[specificity-ratio]]'
  target_id: metric:specificity-ratio
- type: related_to
  target: '[[decodability-steerability-gap]]'
  target_id: term:decodability-steerability-gap
contradicted-by: []
---

[[2605.05715--decodable-but-not-corrected-fixed-residual-stream]] shows the Overthinking failure direction is causally entangled with task-relevant computation, not merely correlated with it: forcing correction via uniform shared-direction steering costs -12.1pp of accuracy, and LEACE-style concept erasure costs -3.6pp (p=0.01), while 10 matched-rank random-direction erasures cost only +0.3pp. Because the specificity ratio is just 0.119-0.152, most of the direction's variance is shared with task computation, so any linear intervention strong enough to move the failure signal also perturbs the computation the model needs to answer correctly.
