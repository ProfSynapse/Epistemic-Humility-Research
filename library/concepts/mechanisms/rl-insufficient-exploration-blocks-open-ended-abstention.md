---
aliases:
- exploration failure blocks abstention in open-ended QA
- base model hesitancy starves RL of abstention signal
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:rl-insufficient-exploration-blocks-open-ended-abstention
  type: mechanism
  status: canonical
cause: "A base LLM that rarely produces IDK responses spontaneously on open-ended QA tasks (empirically 0.03% IDK rate on MATH before training)"
effect: "RL-only RLVR training fails to induce abstention because the group of sampled outputs almost never contains an IDK action, providing zero group-relative advantage signal for abstention; the policy remains stuck at 0.0% IDK even after 500 training steps"
polarity: prevents
related:
- '[[2601.20126--rewarding-intellectual-humility]]'
- '[[ternary-reward-enables-abstention-over-hallucination]]'
- '[[group-relative-policy-optimization]]'
- '[[abstention]]'
- '[[abstention-recall]]'
- '[[rl-sft-random-abstention]]'
- '[[policy-entropy-collapse-narrows-rlvr-reasoning-paths]]'
relationships:
- type: supported_by
  target: '[[2601.20126--rewarding-intellectual-humility]]'
  target_id: paper:2601.20126
  confidence: high
- type: related_to
  target: '[[ternary-reward-enables-abstention-over-hallucination]]'
  target_id: mechanism:ternary-reward-enables-abstention-over-hallucination
  confidence: high
- type: related_to
  target: '[[group-relative-policy-optimization]]'
  target_id: method:group-relative-policy-optimization
  confidence: high
- type: related_to
  target: '[[abstention]]'
  target_id: term:abstention
  confidence: high
- type: related_to
  target: '[[abstention-recall]]'
  target_id: metric:abstention-recall
  confidence: high
- type: related_to
  target: '[[rl-sft-random-abstention]]'
  target_id: method:rl-sft-random-abstention
  confidence: high
- type: related_to
  target: '[[policy-entropy-collapse-narrows-rlvr-reasoning-paths]]'
  target_id: mechanism:policy-entropy-collapse-narrows-rlvr-reasoning-paths
  confidence: high
---

On the Hendrycks MATH open-ended QA task, Granite-3.3-2B-Instruct trained with RL-only RLVR achieves 0.0% IDK rate at r_abs = -0.25, identical to the base model behavior (Table 2). The base model with the IDK prompt achieves only 0.03% IDK, meaning almost no sampled rollout in any GRPO group contains an abstention response. Without at least one IDK sample per group, the group-relative advantage cannot create a positive gradient toward abstention. Adding a supervised abstention warm-up (RL-SFT-Random) seeds the policy with enough IDK behavior that RL can amplify it, yielding 39% IDK at r_abs = -0.5 (Table 2).
