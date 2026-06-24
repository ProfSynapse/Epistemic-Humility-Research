---
aliases:
- Fine-grained Semantic Confidence Reward
- FiSCoRe method
tags:
- kg/method
- concept
- method
kg:
  id: method:fiscore
  type: method
  status: canonical
area: methods
related:
- '[[2510.24020--fiscore-semantic-confidence-reward]]'
- '[[group-relative-policy-optimization]]'
- '[[bidirectional-entailment-clustering]]'
- '[[semantic-entropy]]'
- '[[supervised-finetuning]]'
- '[[abstention]]'
- '[[knowledge-boundary]]'
- '[[pararel]]'
- '[[triviaqa]]'
- '[[sciq]]'
relationships:
- type: proposed_by
  target: '[[2510.24020--fiscore-semantic-confidence-reward]]'
  target_id: paper:2510.24020
  confidence: high
- type: related_to
  target: '[[group-relative-policy-optimization]]'
  target_id: method:group-relative-policy-optimization
  confidence: medium
- type: related_to
  target: '[[bidirectional-entailment-clustering]]'
  target_id: method:bidirectional-entailment-clustering
  confidence: medium
- type: related_to
  target: '[[semantic-entropy]]'
  target_id: method:semantic-entropy
  confidence: medium
- type: related_to
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
  confidence: medium
- type: related_to
  target: '[[abstention]]'
  target_id: term:abstention
  confidence: medium
- type: related_to
  target: '[[knowledge-boundary]]'
  target_id: term:knowledge-boundary
  confidence: medium
- type: related_to
  target: '[[pararel]]'
  target_id: dataset:pararel
  confidence: medium
- type: related_to
  target: '[[triviaqa]]'
  target_id: dataset:triviaqa
  confidence: medium
- type: related_to
  target: '[[sciq]]'
  target_id: dataset:sciq
  confidence: medium
---

A GRPO-based reinforcement learning framework for abstention fine-tuning that assigns per-sample confidence rewards by clustering G rollouts into semantic equivalence classes (via bidirectional NLI entailment) and rewarding the model when its verbalized confidence ('sure'/'unsure') aligns with whether the rollout's cluster size exceeds a threshold tau = ceil(G/2). An auxiliary accuracy reward prevents reward hacking through universal abstention.

**Why it matters here:** Replaces coarse global uncertainty signals (single entropy score or binary correctness label) with a per-sample cluster-size proxy for confidence, producing OOD-robust abstention where SFT baselines collapse. The GRPO-SE vs FiSCoRe comparison holds architecture and training data constant, isolating reward granularity as the key variable.

**Lineage:** Built on group-relative-policy-optimization and bidirectional-entailment-clustering (Kuhn et al. 2023 semantic entropy). Trained on pararel; evaluated on triviaqa, sciq, and Natural Questions. Proposes f1-rel-reliability-metric as companion evaluation.
