---
aliases:
- CPO
- CPO alignment
- Constrictive Preference Optimization
tags:
- kg/method
- concept
- method
kg:
  id: method:contrastive-preference-optimization
  type: method
  status: canonical
area: methods
related:
- '[[2404.14723--insights-into-alignment-dpo-variants]]'
- '[[direct-preference-optimization]]'
- '[[kahneman-tversky-optimization]]'
- '[[identity-preference-optimization]]'
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
  target: '[[identity-preference-optimization]]'
  target_id: method:identity-preference-optimization
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

An RL-free alignment method that combines a maximum-likelihood SFT loss with a reference-model-free preference loss derived from DPO, eliminating the need to load a separate reference policy during training. By removing the reference model from memory, CPO reduces peak GPU memory and enables training larger models at lower cost than DPO.

**Why it matters here:** CPO is notable for two findings in this study: it can skip the SFT warm-up and still match SFT-trained dialogue quality on MT-Bench (unlike DPO and IPO), and it achieves the highest GSM8K score in Scenario 3 while being the lowest on MT-Bench in the same scenario. This asymmetry is relevant to the locked training-regimen experiment because CPO combines an SFT-style completion loss with preference optimization, which could interact differently with abstention training than pure preference methods.

**Lineage:** Proposed by Xu et al. (2024, arXiv:2401.08417); variation of direct-preference-optimization that drops the reference model.
