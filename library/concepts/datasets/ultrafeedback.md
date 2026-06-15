---
aliases:
- UltraFeedback dataset
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:ultrafeedback
  type: dataset
  status: canonical
area: datasets
---

UltraFeedback is a large synthetic preference dataset where GPT-4 generates feedback on multiple model responses per instruction and assigns scalar quality ratings, rather than relying on human annotators. Each example bundles the instruction, several candidate responses, and AI-generated preference scores that can be binarised into chosen/rejected pairs for DPO or used directly as scalar signals for KTO.

**Why it matters here:** The KTO paper (Ethayarajh et al. 2024) shows that KTO matches or exceeds DPO on UltraFeedback, which is relevant to the SFT-vs-DPO-vs-KTO abstention study because UltraFeedback represents a realistic noisy, AI-generated feedback regime rather than clean human labels.

**Lineage:** used as an evaluation surface in [[2402.01306--kto-prospect-theoretic]].
