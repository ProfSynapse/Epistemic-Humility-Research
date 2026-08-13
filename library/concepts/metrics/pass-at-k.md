---
aliases:
- Pass@k
- Pass@1
- Pass@8
- Pass@16
- Pass@64
- multi-attempt accuracy
- pass rate at k attempts
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:pass-at-k
  type: metric
  status: canonical
area: metrics
related:
- '[[pass-k]]'
- '[[2509.07430--choice-of-divergence-rlvr-diversity]]'
- '[[reasoning-fine-tuning]]'
- '[[group-relative-policy-optimization]]'
- '[[dph-rl]]'
- '[[online-rl-training]]'
relationships:
- type: proposed_by
  target: '[[2509.07430--choice-of-divergence-rlvr-diversity]]'
  target_id: paper:2509.07430
  confidence: high
- type: related_to
  target: '[[reasoning-fine-tuning]]'
  target_id: method:reasoning-fine-tuning
  confidence: medium
- type: related_to
  target: '[[group-relative-policy-optimization]]'
  target_id: method:group-relative-policy-optimization
  confidence: medium
- type: related_to
  target: '[[dph-rl]]'
  target_id: method:dph-rl
  confidence: medium
- type: related_to
  target: '[[online-rl-training]]'
  target_id: term:online-rl-training
  confidence: medium
- type: different_from
  target: '[[pass-k]]'
  target_id: metric:pass-k
  confidence: high
  note: "Opposite quantifier: pass@k requires AT LEAST ONE of k attempts to succeed, pass^k requires ALL k. Near-identical surface forms; do not conflate."
---

A sampling-based evaluation metric that measures the probability of generating at least one correct solution within k independent attempts from the same model. Pass@1 corresponds to greedy or single-sample accuracy; higher k values assess solution diversity and the model's ability to cover multiple valid reasoning paths. Formally, Pass@k = 1 - C(n-c, k) / C(n, k) where n samples are drawn and c are correct.

**Why it matters here:** Exposes the diversity-accuracy tradeoff in RLVR: a model can improve Pass@1 (greedy accuracy) while degrading Pass@k (coverage), revealing catastrophic forgetting of diverse solution paths even when headline accuracy improves. It is the central outcome variable in DPH-RL evaluation and a diagnostic for whether RL training narrows or preserves the policy's solution distribution.

**Lineage:** Used as evaluation standard in reasoning-fine-tuning and RLVR literature; adopted here as the primary outcome metric for comparing DPH-RL variants against GRPO and DAPO baselines.
