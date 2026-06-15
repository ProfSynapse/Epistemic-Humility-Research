---
aliases:
- Conservative reward model improves RL factuality finetuning
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:conservative-rm-improves-rl-factuality
  type: mechanism
  status: canonical
cause: Training a [[conservative-reward-model]] to underestimate rewards on unfamiliar inputs
effect: RL finetuning steers policy toward [[abstention|abstaining]] on unfamiliar queries, substantially improving fraction of true facts generated
polarity: increases
related:
- '[[2403.05612--unfamiliar-finetuning-examples]]'
- '[[conservative-reward-model]]'
- '[[abstention]]'
relationships:
- type: supported_by
  target: '[[2403.05612--unfamiliar-finetuning-examples]]'
  target_id: paper:2403.05612
  confidence: high
- type: related_to
  target: '[[conservative-reward-model]]'
  target_id: method:conservative-reward-model
- type: related_to
  target: '[[abstention]]'
  target_id: term:abstention
---

By deliberately underestimating reward on unfamiliar queries, the conservative reward model removes the incentive for the policy to generate hallucinated-but-plausible answers on those inputs. The RL signal then favors abstention (which receives a neutral reward) over hallucination (which receives a penalized reward). The unfamiliar-finetuning paper (arXiv:2403.05612) shows that this conservative RM approach substantially improves the fraction of true facts generated relative to a standard RM, validating reward model conservatism as an effective intervention for RL-based factuality training.
