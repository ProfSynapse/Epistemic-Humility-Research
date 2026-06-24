---
aliases:
- selective entropy floor preserves rollout diversity
- PAEC entropy floor mechanism
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:position-aware-entropy-penalty-preserves-exploration
  type: mechanism
  status: canonical
cause: "Applying a one-sided quadratic lower-bound entropy penalty only at token positions identified as decision-sensitive by the soft mask (high nucleus entropy, small top-two log-probability gap)"
effect: "Prevention of entropy collapse at decision-sensitive positions while leaving low-entropy positions unperturbed, resulting in improved rollout diversity and majority-vote accuracy"
polarity: enables
related:
- '[[2606.08543--rl-diversity-collapse]]'
- '[[paec]]'
- '[[policy-entropy-collapse]]'
- '[[policy-entropy-collapse-narrows-rlvr-reasoning-paths]]'
- '[[group-relative-policy-optimization]]'
relationships:
- type: supported_by
  target: '[[2606.08543--rl-diversity-collapse]]'
  target_id: paper:2606.08543
  confidence: high
- type: related_to
  target: '[[paec]]'
  target_id: method:paec
  confidence: high
- type: related_to
  target: '[[policy-entropy-collapse]]'
  target_id: term:policy-entropy-collapse
  confidence: high
- type: related_to
  target: '[[policy-entropy-collapse-narrows-rlvr-reasoning-paths]]'
  target_id: mechanism:policy-entropy-collapse-narrows-rlvr-reasoning-paths
  confidence: high
- type: related_to
  target: '[[group-relative-policy-optimization]]'
  target_id: method:group-relative-policy-optimization
  confidence: high
---

PAEC establishes an anchor entropy H_0 from the first K=4 training steps and sets a per-position floor H_low = rho_min * H_0. The penalty L_penalty = [max(0, H_low - H_bar)]^2 fires only when entropy at a selected position falls below the floor, remaining inactive when entropy is healthy. The soft mask (quantile threshold rho=0.8) ensures the penalty targets the top 20% most uncertain positions rather than all tokens. Ablations show removing the penalty alone drops Avg Maj from 41.6 to 38.8 and removing the mask drops it to 38.3, confirming both components are necessary.
