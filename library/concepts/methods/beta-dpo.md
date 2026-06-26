---
aliases:
- beta-DPO
- dynamic beta DPO
- Direct Preference Optimization with Dynamic Beta
tags:
- kg/method
- concept
- method
kg:
  id: method:beta-dpo
  type: method
  status: canonical
area: methods
related:
- '[[2407.08639--dpo-direct-preference-optimization-dynamic]]'
- '[[direct-preference-optimization]]'
- '[[preference-pair-data]]'
- '[[kl-divergence-penalty]]'
relationships:
- type: proposed_by
  target: '[[2407.08639--dpo-direct-preference-optimization-dynamic]]'
  target_id: paper:2407.08639
  confidence: high
- type: variation_of
  target: '[[direct-preference-optimization]]'
  target_id: method:direct-preference-optimization
  confidence: high
- type: uses
  target: '[[preference-pair-data]]'
  target_id: dataset:preference-pair-data
  confidence: high
- type: related_to
  target: '[[kl-divergence-penalty]]'
  target_id: term:kl-divergence-penalty
  confidence: high
---

Beta-DPO is a DPO variant that adjusts the beta tradeoff parameter at the batch
level using a pair-quality signal, then filters outlier preference pairs before
estimating the batch update.

**Why it matters here:** Our DPO rows can optimize the trainer objective while
barely improving epistemic-humility behavior. This method is direct evidence
that a static beta can be poorly matched to heterogeneous preference pairs.

**Lineage:** variation of [[direct-preference-optimization]] focused on dynamic
control of the beta/KL tradeoff.
