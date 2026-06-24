---
aliases:
- DPH-RL
- Diversity-Preserving Hybrid RL
- DPH-F
- DPH-JS
- DPH-JS Generator
- DPH-JS Divergence Definition
tags:
- kg/method
- concept
- method
kg:
  id: method:dph-rl
  type: method
  status: canonical
area: methods
related:
- '[[2509.07430--choice-of-divergence-rlvr-diversity]]'
- '[[group-relative-policy-optimization]]'
- '[[proximal-policy-optimization]]'
- '[[kl-divergence-penalty]]'
- '[[reasoning-fine-tuning]]'
- '[[sft-self-distillation]]'
- '[[online-rl-training]]'
relationships:
- type: proposed_by
  target: '[[2509.07430--choice-of-divergence-rlvr-diversity]]'
  target_id: paper:2509.07430
  confidence: high
- type: related_to
  target: '[[group-relative-policy-optimization]]'
  target_id: method:group-relative-policy-optimization
  confidence: medium
- type: related_to
  target: '[[proximal-policy-optimization]]'
  target_id: method:proximal-policy-optimization
  confidence: medium
- type: related_to
  target: '[[kl-divergence-penalty]]'
  target_id: term:kl-divergence-penalty
  confidence: medium
- type: related_to
  target: '[[reasoning-fine-tuning]]'
  target_id: method:reasoning-fine-tuning
  confidence: medium
- type: related_to
  target: '[[sft-self-distillation]]'
  target_id: method:sft-self-distillation
  confidence: medium
- type: related_to
  target: '[[online-rl-training]]'
  target_id: term:online-rl-training
  confidence: medium
---

A RLVR training framework that replaces the standard reverse-KL penalty with a mass-covering f-divergence (forward-KL for DPH-F, Jensen-Shannon for DPH-JS). It splits the training corpus into a near-perfect dataset (high base-model accuracy) on which the f-divergence penalty is applied as a rehearsal constraint, and an exploration dataset (lower base-model accuracy) on which unrestricted PPO-clip optimization runs. The Generator-based implementation pre-samples the near-perfect responses from the initial policy into a static dataset, so no online reference-model forward passes are needed during training for that variant.

**Why it matters here:** Directly addresses the Pass@k vs. Pass@1 paradox in RLVR by preventing catastrophic forgetting and OOD generalization collapse without requiring external teacher models. Offers a compute-efficient alternative to maintaining a live reference policy during RL training, relevant to the Synaptic Tuner budget in Phase 1 training arms.

**Lineage:** Extends group-relative-policy-optimization and proximal-policy-optimization by replacing the reverse-KL divergence term with f-divergences from the broader f-divergence family; related to sft-self-distillation as an analogous rehearsal-through-anchoring mechanism.
