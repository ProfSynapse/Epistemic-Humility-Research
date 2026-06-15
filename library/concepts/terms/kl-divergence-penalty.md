---
aliases:
- KL penalty
- KL regularization
- KL constraint
tags:
- kg/term
- concept
- term
kg:
  id: term:kl-divergence-penalty
  type: term
  status: canonical
area: methods
related:
- '[[reinforcement-learning-from-human-feedback]]'
- '[[direct-preference-optimization]]'
- '[[proximal-policy-optimization]]'
relationships:
- type: related_to
  target: '[[reinforcement-learning-from-human-feedback]]'
  target_id: method:reinforcement-learning-from-human-feedback
- type: related_to
  target: '[[direct-preference-optimization]]'
  target_id: method:direct-preference-optimization
- type: related_to
  target: '[[proximal-policy-optimization]]'
  target_id: method:proximal-policy-optimization
---

The KL-divergence penalty is a regularization term in preference-learning objectives that measures the divergence between the fine-tuned policy and a frozen reference policy (usually the SFT checkpoint), and adds it as a per-token cost to prevent the optimizer from exploiting the reward model or collapsing generation diversity. In RLHF it appears explicitly as a reward shaping term; in DPO it is implicitly encoded in the reparameterized loss, so the reference policy still constrains the trained policy without a separate KL coefficient tuning step.

**Why it matters here:** The KL penalty determines how far any of the three training arms (SFT, DPO, KTO) can shift the model toward abstention before degrading other capabilities, which connects directly to the alignment-tax measurement in the Phase 1 study.

**Lineage:** appears explicitly in [[reinforcement-learning-from-human-feedback]] and [[proximal-policy-optimization]]; absorbed implicitly into [[direct-preference-optimization]] and [[kahneman-tversky-optimization]].
