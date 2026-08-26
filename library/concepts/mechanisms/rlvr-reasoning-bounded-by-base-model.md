---
title: rlvr-reasoning-bounded-by-base-model
aliases:
- RLVR reasoning abilities originate from and are bounded by the base model
- RLVR narrows sampling rather than expanding reasoning capacity
- base models achieve higher pass@k than their RLVR-trained counterparts at large k
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:rlvr-reasoning-bounded-by-base-model
  type: mechanism
  status: canonical
cause: "Reinforcement Learning with Verifiable Rewards (RLVR), tested across six popular RL algorithms (PPO, GRPO, Reinforce++, RLOO, ReMax, DAPO) and math, code, and visual reasoning benchmarks, applied to a pretrained base model to train for improved reasoning."
effect: "RLVR-trained models outperform their own base model at small k (e.g., pass@1), but the base model achieves a higher pass@k score once k grows large; coverage and perplexity analyses trace this back to the RLVR-trained model's correct solutions already being reachable in the base model's own sampling distribution. RLVR raises sampling efficiency (the Sampling Efficiency Gap, RL pass@1 minus base pass@k at k=256) rather than expanding what the model can reach at all; all six algorithms tested perform similarly on this measure and remain far from the base model's own ceiling."
polarity: limits
related:
- '[[2504.13837--does-reinforcement-learning-really-incentivize-reasoning-capacity]]'
- '[[pass-at-k]]'
- '[[distillation-expands-reasoning-boundary-beyond-base]]'
- '[[policy-entropy-collapse-narrows-rlvr-reasoning-paths]]'
- '[[only-sft-installs-abstention-in-weights]]'
- '[[rl-insufficient-exploration-blocks-open-ended-abstention]]'
relationships:
- type: supported_by
  target: '[[2504.13837--does-reinforcement-learning-really-incentivize-reasoning-capacity]]'
  target_id: paper:2504.13837
  confidence: high
- type: related_to
  target: '[[pass-at-k]]'
  target_id: metric:pass-at-k
  confidence: high
- type: related_to
  target: '[[distillation-expands-reasoning-boundary-beyond-base]]'
  target_id: mechanism:distillation-expands-reasoning-boundary-beyond-base
  confidence: high
  evidence:
  - "2504.13837 Section 4.2 (contrast case, same paper)"
- type: related_to
  target: '[[policy-entropy-collapse-narrows-rlvr-reasoning-paths]]'
  target_id: mechanism:policy-entropy-collapse-narrows-rlvr-reasoning-paths
  confidence: medium
- type: related_to
  target: '[[only-sft-installs-abstention-in-weights]]'
  target_id: mechanism:only-sft-installs-abstention-in-weights
  confidence: medium
  evidence:
  - "reasoning-domain analogue: RL from a cold or near-cold start does not exceed what the base model already carries, matching this program's cold-start GRPO abstention finding"
- type: related_to
  target: '[[rl-insufficient-exploration-blocks-open-ended-abstention]]'
  target_id: mechanism:rl-insufficient-exploration-blocks-open-ended-abstention
  confidence: low
---

Yue et al. treat the base model as an upper bound and ask whether RLVR
training genuinely expands what an LLM can reason its way to, or merely
makes it more likely to sample solutions it already had access to. Using
pass@k at large k as the diagnostic (a metric insensitive to sampling
efficiency but sensitive to reachable coverage), they find RLVR-trained
models win at pass@1 but lose to their own untrained base at large k,
across math, code, and visual reasoning benchmarks and six RL algorithms.
Coverage and perplexity analyses confirm the correct solutions RLVR
elicits were already present in the base model's distribution; RLVR
narrows the effective sampling distribution toward them rather than
discovering anything new.

**Why it matters here:** this is the reasoning-domain statement of what
this program's own cold-start GRPO arm shows for abstention under a
structure-only prompt: a policy-gradient objective can sharpen a behavior
already latent in the base model's distribution without installing
anything new that survives removal of the eliciting signal. See
[[only-sft-installs-abstention-in-weights]] for the abstention-domain
parallel, and [[distillation-expands-reasoning-boundary-beyond-base]] for
this same paper's contrast case showing a different training signal
(distillation) genuinely does exceed the base ceiling.

**Lineage:** established in
[[2504.13837--does-reinforcement-learning-really-incentivize-reasoning-capacity]]
(Yue et al. 2025, NeurIPS 2025 Oral).
