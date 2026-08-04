---
aliases:
- Classification-Correction Gap
- Decodability-Steerability Gap
tags:
- kg/term
- concept
- term
kg:
  id: term:decodability-steerability-gap
  type: term
  status: canonical
area: verification
introduced-by: "[[2605.05715--decodable-but-not-corrected-fixed-residual-stream]]"
related:
- '[[2605.05715--decodable-but-not-corrected-fixed-residual-stream]]'
- '[[probing-accuracy-task-importance-disconnect]]'
relationships:
- type: proposed_by
  target: '[[2605.05715--decodable-but-not-corrected-fixed-residual-stream]]'
  target_id: paper:2605.05715
  confidence: medium
- type: related_to
  target: '[[probing-accuracy-task-importance-disconnect]]'
  target_id: term:probing-accuracy-task-importance-disconnect
---

The decodability-steerability gap (also called the classification-correction gap) names the finding that a failure signal being linearly decodable from hidden states does not imply that a fixed linear intervention derived from the same signal can correct the failure it decodes.

**Why it matters here:** [[2605.05715--decodable-but-not-corrected-fixed-residual-stream]] documents this gap directly: Overthinking is decodable at 71.6% accuracy, but 29 linear steering configurations across five families produce Delta ~= 0, and the null result replicates cross-architecture and cross-domain.

**Lineage:** a specific instance of the broader [[probing-accuracy-task-importance-disconnect]], but stated as a decoding-vs-intervention gap rather than a decoding-vs-usage gap.
