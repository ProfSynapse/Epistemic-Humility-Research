---
aliases:
- RLVR Post-Training Degrades Abstention
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:rlvr-post-training-degrades-abstention
  type: mechanism
  status: canonical
cause: Adding a reinforcement learning with verifiable reward (RLVR) stage on top of SFT+DPO post-training
effect: Decreased [[abstention-recall]] relative to the DPO checkpoint, suggesting that optimizing for verifiable correctness hurts uncertainty handling
polarity: decreases
related:
- '[[2506.09038--abstentionbench]]'
- '[[abstention-recall]]'
relationships:
- type: supported_by
  target: '[[2506.09038--abstentionbench]]'
  target_id: paper:2506.09038
  confidence: high
- type: related_to
  target: '[[abstention-recall]]'
  target_id: metric:abstention-recall
---

SFT and DPO together can produce a model with reasonable abstention behavior, but adding an RLVR stage on top reverses these gains. The verifiable correctness reward is incompatible with abstention because the reward signal only fires when the model commits to an answer that can be checked, and abstention responses receive no reward regardless of their appropriateness. AbstentionBench (arXiv:2506.09038) demonstrates this rollback empirically, finding that RLVR checkpoints consistently underperform their DPO predecessors on abstention recall.
