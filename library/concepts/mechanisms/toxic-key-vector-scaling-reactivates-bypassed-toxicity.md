---
aliases:
- Toxic key-vector scaling reactivates bypassed toxicity
- Expanding toxic activation regions reverses DPO suppression
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:toxic-key-vector-scaling-reactivates-bypassed-toxicity
  type: mechanism
  status: canonical
cause: "Seven toxicity-associated MLP key vectors in DPO-trained GPT-2 Medium are scaled by a factor of ten."
effect: "Their activation regions expand and the model's toxicity score returns to its pre-DPO level without a reported perplexity or token-overlap F1 penalty."
polarity: enables
related:
- '[[2401.01967--mechanistic-understanding-alignment-algorithms-case-study-dpo]]'
- '[[dpo-distributed-offset-bypasses-toxic-mlp-activation-regions]]'
relationships:
- type: supported_by
  target: '[[2401.01967--mechanistic-understanding-alignment-algorithms-case-study-dpo]]'
  target_id: paper:2401.01967
  confidence: high
- type: related_to
  target: '[[dpo-distributed-offset-bypasses-toxic-mlp-activation-regions]]'
  target_id: mechanism:dpo-distributed-offset-bypasses-toxic-mlp-activation-regions
  confidence: high
---

The intervention supports the paper's bypass account because it restores activation of retained toxic components. It is a direct weight intervention on the studied model, not a prompt-only jailbreak.
