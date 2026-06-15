---
aliases:
- conservative RM
- Csv. RM
tags:
- kg/method
- concept
- method
kg:
  id: method:conservative-reward-model
  type: method
  status: canonical
area: methods
related:
- '[[2403.05612--unfamiliar-finetuning-examples]]'
- '[[supervised-finetuning]]'
- '[[factscore]]'
relationships:
- type: proposed_by
  target: '[[2403.05612--unfamiliar-finetuning-examples]]'
  target_id: paper:2403.05612
  confidence: high
- type: derived_from
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
- type: related_to
  target: '[[factscore]]'
  target_id: metric:factscore
---

A conservative reward model is trained to systematically underestimate rewards
on unfamiliar query/response pairs rather than overestimate them, reversing the
usual optimistic extrapolation bias of standard reward models. During RL
factuality finetuning, this conservative signal steers the policy toward
less-informative but non-hallucinating abstaining responses whenever it
encounters queries outside its reliable knowledge, because confidently wrong
answers receive low reward rather than spuriously high reward.

**Why it matters here:** [[reward-model-overestimation-undermines-rl-factuality]]
is a known failure mode when applying RL to improve factual accuracy. The
conservative RM directly counters that mechanism and pairs with [[answer-relabeling]]
as the RL-stage complement to the SFT-stage data fix. Its factuality gains are
tracked via [[factscore]], making it a concrete alternative to the plain SFT
and preference-optimization arms studied for abstention.

**Lineage:** extends [[supervised-finetuning]] (the base RM training procedure);
related to [[factscore]] (the evaluation metric it optimizes); proposed in
[[2403.05612--unfamiliar-finetuning-examples]].
