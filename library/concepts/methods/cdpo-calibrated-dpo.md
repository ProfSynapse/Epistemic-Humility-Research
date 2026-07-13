---
aliases:
- CDPO
- Calibrated DPO
tags:
- kg/method
- concept
- method
kg:
  id: method:cdpo-calibrated-dpo
  type: method
  status: canonical
area: methods
related:
- '[[2410.09724--taming-overconfidence-rlhf]]'
- '[[direct-preference-optimization]]'
- '[[ppo-m-calibrated-reward-modeling]]'
relationships:
- type: proposed_by
  target: '[[2410.09724--taming-overconfidence-rlhf]]'
  target_id: paper:2410.09724
  confidence: high
- type: derived_from
  target: '[[direct-preference-optimization]]'
  target_id: method:direct-preference-optimization
  confidence: high
- type: related_to
  target: '[[ppo-m-calibrated-reward-modeling]]'
  target_id: method:ppo-m-calibrated-reward-modeling
  confidence: high
---

CDPO augments the standard DPO loss with a confidence-calibration term. Each
training sample is paired with chosen and rejected responses carrying random high
and low confidence scores, and the loss is extended to prefer high confidence on
chosen responses and low confidence on rejected ones; the original DPO term is
retained to prevent forgetting.

**Why it matters here:** CDPO shows the PPO-M calibration idea ports directly to
[[direct-preference-optimization]], the offline preference method used in the
locked training-regimen arms, without sacrificing task accuracy or instruction-following. It is
the concrete candidate for a calibration-aware loss augmentation on the DPO arm.

**Lineage:** the DPO-compatible extension of the PPO-M calibration loss, proposed
in the same paper (§5.2).
