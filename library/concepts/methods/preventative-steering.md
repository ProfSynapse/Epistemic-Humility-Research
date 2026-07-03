---
aliases:
- training-time steering
- proactive persona steering
tags:
- kg/method
- concept
- method
kg:
  id: method:preventative-steering
  type: method
  status: canonical
area: steering
related:
- '[[2507.21509--persona-vectors-monitoring-controlling-character-traits-language]]'
- '[[activation-steering]]'
- '[[persona-vectors]]'
relationships:
- type: proposed_by
  target: '[[2507.21509--persona-vectors-monitoring-controlling-character-traits-language]]'
  target_id: paper:2507.21509
  confidence: high
- type: derived_from
  target: '[[activation-steering]]'
  target_id: method:activation-steering
---

Preventative steering adds a persona direction vector to the model's hidden states at every training step, steering the model toward an undesired trait during finetuning rather than away from it at inference time. By saturating the direction during training, the method relieves optimization pressure to shift along that axis in order to fit task data, so the model learns the new skill without acquiring the associated persona. Empirically, preventative steering better preserves general capabilities (measured by MMLU) than post-hoc inference-time steering while achieving comparable or stronger trait suppression.

**Why it matters here:** Calibration and abstention finetuning can inadvertently install overconfidence or sycophancy as side effects; preventative steering offers a mechanism to neutralize such trait drift during the training pass itself, without requiring a separate correction stage after deployment.

**Lineage:** extends [[activation-steering]] from inference-time to training-time application; requires [[persona-vectors]] to supply the steering direction; contrasts with post-hoc [[contrastive-activation-addition]] applied at inference.
