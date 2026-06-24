---
aliases:
- mode-seeking KL causes diversity collapse
- reverse-KL accelerates catastrophic forgetting
- reverse-KL collapses solution styles
- entropy collapse via reverse-KL
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:reverse-kl-narrows-policy-to-single-mode
  type: mechanism
  status: canonical
cause: "Training an LLM with a reverse-KL divergence penalty (mode-seeking) in an RLVR objective, which draws its expectation from the current policy so already-forgotten solution paths are never re-sampled"
effect: "The policy converges to a single high-probability solution mode, reducing Pass@k, collapsing solution-style diversity, and accelerating catastrophic forgetting of skills the base model previously held"
polarity: decreases
related:
- '[[2509.07430--choice-of-divergence-rlvr-diversity]]'
- '[[dph-rl]]'
- '[[mass-covering-divergence-preserves-policy-diversity]]'
- '[[kl-divergence-penalty]]'
- '[[group-relative-policy-optimization]]'
- '[[pass-at-k]]'
- '[[reasoning-fine-tuning]]'
relationships:
- type: supported_by
  target: '[[2509.07430--choice-of-divergence-rlvr-diversity]]'
  target_id: paper:2509.07430
  confidence: high
- type: related_to
  target: '[[dph-rl]]'
  target_id: method:dph-rl
  confidence: high
- type: related_to
  target: '[[mass-covering-divergence-preserves-policy-diversity]]'
  target_id: mechanism:mass-covering-divergence-preserves-policy-diversity
  confidence: high
- type: related_to
  target: '[[kl-divergence-penalty]]'
  target_id: term:kl-divergence-penalty
  confidence: high
- type: related_to
  target: '[[group-relative-policy-optimization]]'
  target_id: method:group-relative-policy-optimization
  confidence: high
- type: related_to
  target: '[[pass-at-k]]'
  target_id: metric:pass-at-k
  confidence: high
- type: related_to
  target: '[[reasoning-fine-tuning]]'
  target_id: method:reasoning-fine-tuning
  confidence: high
---

Reverse-KL is mode-seeking: it penalizes the policy for assigning mass to regions where the reference assigns low probability, but does not penalize it for dropping mass from regions where the reference assigns high probability. In the RLVR context where the expectation is over the current policy, once a solution strategy's probability drops, it stops contributing to the gradient and disappears. Style-diversity experiments (Appendix A, Figure 5) show that reverse-KL collapses outputs to a single solution style across 32 draws, while forward-KL produces 3+ styles in 60% of cases. The keep-rate evidence (Section 6.2) shows GRPO and DAPO (reverse-KL and no-KL respectively) solve only ~85% of previously-correct queries after training, consistent with this narrowing.
