---
aliases:
- SFT cold-start enables RLVR clarification learning
- cold-start SFT needed for clarification quality
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:sft-cold-start-enables-rlvr-clarification
  type: mechanism
  status: canonical
cause: "Supervised fine-tuning on structured abstention-and-clarification traces before GRPO training"
effect: "Post-refusal clarification quality (U-Clar) is preserved or improved during subsequent RLVR; without SFT, RL alone fails to acquire clarification behavior"
polarity: enables
related:
- '[[2604.17073--abstain-r1]]'
- '[[rlvr-post-training-degrades-abstention]]'
- '[[sft-abstention-causes-over-refusal]]'
- '[[clarification-aware-rlvr-reward]]'
- '[[abstain-r1]]'
- '[[abstain-cot]]'
relationships:
- type: supported_by
  target: '[[2604.17073--abstain-r1]]'
  target_id: paper:2604.17073
  confidence: high
- type: related_to
  target: '[[rlvr-post-training-degrades-abstention]]'
  target_id: mechanism:rlvr-post-training-degrades-abstention
  confidence: high
- type: related_to
  target: '[[sft-abstention-causes-over-refusal]]'
  target_id: mechanism:sft-abstention-causes-over-refusal
  confidence: high
- type: related_to
  target: '[[clarification-aware-rlvr-reward]]'
  target_id: method:clarification-aware-rlvr-reward
  confidence: high
- type: related_to
  target: '[[abstain-r1]]'
  target_id: model:abstain-r1
  confidence: high
- type: related_to
  target: '[[abstain-cot]]'
  target_id: dataset:abstain-cot
  confidence: high
---

Ablation experiments in Table 2 show that removing the SFT cold-start stage while keeping RLVR training collapses U-Clar from 55.1% to 8.5% even though U-Ref remains high at 65.1%. This shows that GRPO with the clarification-aware reward can learn when to refuse without the SFT phase, but cannot learn what to say after refusing. The SFT traces provide the model with the format and semantic content of correct clarifications; the RL phase then reinforces and sharpens the behavior under reward, but it cannot introduce the clarification behavior from scratch. The asymmetry between U-Ref and U-Clar in the ablation is the diagnostic signature: refusal is learnable from the reward signal alone, but clarification requires supervised exposure to reference clarification content.
