---
aliases:
- SimpleQA-Verified
- SimpleQA Verified
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:simpleqa-verified
  type: dataset
  status: canonical
area: datasets
related:
- '[[2603.09906--thinking-recall-how-reasoning-unlocks-parametric-knowledge]]'
- '[[simpleqa]]'
- '[[knowledge-boundary]]'
relationships:
- type: variation_of
  target: '[[simpleqa]]'
  target_id: dataset:simpleqa
  confidence: high
- type: related_to
  target: '[[knowledge-boundary]]'
  target_id: term:knowledge-boundary
  confidence: medium
---

A 1,000-example subset of SimpleQA (Haas et al., 2025) that has been filtered and corrected for increased reliability, with per-question metadata flagging whether an item is multi-step or requires reasoning. It is a closed-book short-answer factuality benchmark used to probe parametric recall under controlled conditions.

**Why it matters here:** The single-hop vs multi-step metadata lets a study separate reasoning gains that come from question decomposition from gains that come from better parametric recall. In this paper 903 of 1,000 questions are single-hop, and reasoning helps the simple and complex subsets roughly equally, which isolates recall (not decomposition) as the driver.

**Lineage:** A cleaned variation of [[simpleqa]] (Wei et al., 2024); the verification and correction pass is from Haas et al. (2025).
