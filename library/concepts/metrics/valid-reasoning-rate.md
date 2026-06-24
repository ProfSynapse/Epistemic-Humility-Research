---
aliases:
- VR
- structural reasoning reliability
- trace validity rate
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:valid-reasoning-rate
  type: metric
  status: canonical
area: metrics
related:
- '[[2605.21127--silent-reasoning-trace-suppression]]'
- '[[reasoning-trace-collapse]]'
- '[[thinkpack]]'
- '[[pass-at-k]]'
- '[[reasoning-fine-tuning]]'
relationships:
- type: proposed_by
  target: '[[2605.21127--silent-reasoning-trace-suppression]]'
  target_id: paper:2605.21127
  confidence: high
- type: related_to
  target: '[[reasoning-trace-collapse]]'
  target_id: term:reasoning-trace-collapse
  confidence: medium
- type: related_to
  target: '[[thinkpack]]'
  target_id: method:thinkpack
  confidence: medium
- type: related_to
  target: '[[pass-at-k]]'
  target_id: metric:pass-at-k
  confidence: medium
- type: related_to
  target: '[[reasoning-fine-tuning]]'
  target_id: method:reasoning-fine-tuning
  confidence: medium
---

The proportion of model outputs that contain a complete, non-empty reasoning trace that can be reliably separated from the final answer. Invalid reasoning is decomposed into empty rate (ER), missing rate (MR), and truncated rate (TR). Rpass@1 (reasoning-conditioned pass@1) is accuracy computed only over responses with valid reasoning.

**Why it matters here:** VR is the primary structural reliability metric for detecting reasoning-trace collapse. It decouples structural trace presence from answer correctness, making it essential for evaluating fine-tuned reasoning models when adaptation data lacks explicit traces.

**Lineage:** Introduced in Twist et al. 2026 (arXiv:2605.21127), Section 3 and Section 5.1, implemented in ThinkPack.
