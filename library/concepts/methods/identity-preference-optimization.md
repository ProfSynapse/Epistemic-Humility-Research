---
aliases:
- IPO
- IPO alignment
- General Theoretical Paradigm for Preference Learning
tags:
- kg/method
- concept
- method
kg:
  id: method:identity-preference-optimization
  type: method
  status: canonical
area: methods
related:
- '[[2404.14723--insights-into-alignment-dpo-variants]]'
- '[[direct-preference-optimization]]'
- '[[kahneman-tversky-optimization]]'
- '[[contrastive-preference-optimization]]'
- '[[supervised-finetuning]]'
- '[[reinforcement-learning-from-human-feedback]]'
relationships:
- type: proposed_by
  target: '[[2404.14723--insights-into-alignment-dpo-variants]]'
  target_id: paper:2404.14723
  confidence: high
- type: related_to
  target: '[[direct-preference-optimization]]'
  target_id: method:direct-preference-optimization
  confidence: medium
- type: related_to
  target: '[[kahneman-tversky-optimization]]'
  target_id: method:kahneman-tversky-optimization
  confidence: medium
- type: related_to
  target: '[[contrastive-preference-optimization]]'
  target_id: method:contrastive-preference-optimization
  confidence: medium
- type: related_to
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
  confidence: medium
- type: related_to
  target: '[[reinforcement-learning-from-human-feedback]]'
  target_id: method:reinforcement-learning-from-human-feedback
  confidence: medium
---

An RL-free alignment method that reformulates the DPO objective into a general preference-learning loss (the h-function formulation) which explicitly avoids the overfitting and lack of regularization that DPO can exhibit. IPO does not require a separately trained reward model and operates on preference pairs, but replaces DPO's log-ratio surrogate with a squared-loss objective over the pairwise log-probability ratio minus a regularization target.

**Why it matters here:** IPO is the second non-DPO alignment variant evaluated in the locked training-regimen multi-scenario study. Its theoretical motivation is tighter regularization than DPO, making it a candidate for better-calibrated post-alignment behavior, though the empirical results here show it underperforms KTO on most tasks and requires the SFT warm-up for dialogue quality.

**Lineage:** Proposed by Azar et al. (2023, arXiv:2310.12036) as a general theoretical paradigm that subsumes DPO; variant of direct-preference-optimization.
