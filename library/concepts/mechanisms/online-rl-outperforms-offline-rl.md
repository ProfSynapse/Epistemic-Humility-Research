---
aliases:
- Online RL sampling outperforms offline RFT in later training
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:online-rl-outperforms-offline-rl
  type: mechanism
  status: canonical
cause: Using on-policy (real-time) data sampling during [[online-rl-training]]
effect: Greater performance gains over offline rejection-sampling fine-tuning, especially in later training stages
polarity: increases
related:
- '[[2402.03300--deepseekmath-grpo]]'
- '[[online-rl-training]]'
relationships:
- type: supported_by
  target: '[[2402.03300--deepseekmath-grpo]]'
  target_id: paper:2402.03300
  confidence: high
- type: related_to
  target: '[[online-rl-training]]'
  target_id: term:online-rl-training
---

Offline rejection-sampling fine-tuning fixes the training distribution at the time of data collection, so the policy quickly exhausts the learning signal once it surpasses the quality of the offline data. On-policy RL continuously generates new rollouts from the current policy, maintaining a fresh challenge signal throughout training. The DeepSeekMath paper (arXiv:2402.03300) shows this advantage grows in later stages, where offline-sampled data becomes stale relative to the improving policy.
