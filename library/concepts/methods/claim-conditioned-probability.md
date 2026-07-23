---
aliases:
- CCP
- claim condition probability
- claim-level CCP scorer
tags:
- kg/method
- concept
- method
kg:
  id: method:claim-conditioned-probability
  type: method
  status: canonical
area: methods
related:
- '[[2604.13991--adaptive-conformal-factuality]]'
- '[[adaptive-conformal-factuality]]'
- '[[conditional-coverage]]'
- '[[hallucination]]'
- '[[calibration]]'
- '[[factscore]]'
relationships:
- type: proposed_by
  target: '[[2604.13991--adaptive-conformal-factuality]]'
  target_id: paper:2604.13991
  confidence: high
- type: related_to
  target: '[[adaptive-conformal-factuality]]'
  target_id: method:adaptive-conformal-factuality
  confidence: medium
- type: related_to
  target: '[[conditional-coverage]]'
  target_id: term:conditional-coverage
  confidence: medium
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
  confidence: medium
- type: related_to
  target: '[[calibration]]'
  target_id: term:calibration
  confidence: medium
- type: related_to
  target: '[[factscore]]'
  target_id: metric:factscore
  confidence: medium
---

A claim-level uncertainty scoring function for white-box LLMs that estimates the probability of a specific atomic claim being correct conditioned on the claim itself, rather than on surface properties like token order or claim length. CCP focuses uncertainty estimation on claim-specific semantic content, filtering out non-task-relevant factors that confound simpler token-probability measures.

**Why it matters here:** CCP is the strongest tested claim-level signal for filtering incorrect atomic claims in long-form generation (PR-AUC 0.360/0.367/0.238 on Mistral 7B / Llama3 8B / Gemma3 12B, outperforming Max Token Entropy across all three). It is the recommended input scorer for adaptive conformal factuality pipelines and is a candidate read-out after locked training-regimen arms.

**Lineage:** Introduced by Fadeeva et al. (2024, FActScore-related work); implemented in the LM-Polygraph library. Related to token-probability approaches like Maximum Probability and Perplexity but conditioned on the target claim.
