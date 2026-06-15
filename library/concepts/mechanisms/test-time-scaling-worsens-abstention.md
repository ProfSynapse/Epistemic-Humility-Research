---
aliases:
- Test-Time Compute Scaling Worsens Abstention
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:test-time-scaling-worsens-abstention
  type: mechanism
  status: canonical
cause: Increasing the reasoning token budget (from 512 to 4096 tokens) allocated to chain-of-thought generation before the final answer
effect: Improved response accuracy on reasoning datasets but no improvement or further worsening of [[abstention-recall]]
polarity: decreases
related:
- '[[2506.09038--abstentionbench]]'
- '[[abstention-recall]]'
relationships:
- type: supported_by
  target: '[[2506.09038--abstentionbench]]'
  target_id: paper:2506.09038
  confidence: high
- type: related_to
  target: '[[abstention-recall]]'
  target_id: metric:abstention-recall
---

More reasoning tokens give the model more opportunity to construct internally consistent chains of thought that rationalize a specific answer, even when the question is unanswerable. Extended reasoning thus reinforces the model's commitment to generating an answer rather than surfacing genuine uncertainty. AbstentionBench (arXiv:2506.09038) shows that scaling from 512 to 4096 reasoning tokens improves accuracy on answerable questions but does not improve, and often worsens, abstention recall on unanswerable ones.
