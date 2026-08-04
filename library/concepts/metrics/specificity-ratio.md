---
aliases:
- Specificity Ratio
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:specificity-ratio
  type: metric
  status: canonical
area: metrics
related:
- '[[2605.05715--decodable-but-not-corrected-fixed-residual-stream]]'
relationships:
- type: proposed_by
  target: '[[2605.05715--decodable-but-not-corrected-fixed-residual-stream]]'
  target_id: paper:2605.05715
  confidence: high
---

The specificity ratio quantifies how much of a failure-mode steering direction is specific to that failure versus shared with task-relevant computation, via a shared-specific decomposition of the direction. A low ratio means the direction overlaps heavily with directions needed for the underlying task.

**Why it matters here:** [[2605.05715--decodable-but-not-corrected-fixed-residual-stream]] reports a specificity ratio of only 0.119 (Llama-3.1-8B) / 0.152 (Qwen2.5-7B) for the Overthinking direction, evidence that the failure direction is representationally entangled with task-critical computation and explaining why fixed linear steering cannot correct it without damaging accuracy.

**Lineage:** proposed in arXiv:2605.05715 alongside the shared-specific decomposition analysis (Section 4.6, Appendix H).
