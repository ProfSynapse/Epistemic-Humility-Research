---
aliases:
- TruthRL
- truthfulness-driven RL
- TruthRL framework
tags:
- kg/method
- concept
- method
kg:
  id: method:truthrl
  type: method
  status: canonical
area: methods
related:
- '[[2509.25760--truthrl-incentivizing-truthful-llms]]'
- '[[group-relative-policy-optimization]]'
- '[[binary-grading-reinforces-hallucination]]'
- '[[online-rl-outperforms-offline-rl]]'
- '[[knowledge-boundary]]'
- '[[abstention]]'
- '[[hallucination]]'
- '[[idk-sft]]'
- '[[supervised-finetuning]]'
- '[[direct-preference-optimization]]'
- '[[over-abstention]]'
relationships:
- type: proposed_by
  target: '[[2509.25760--truthrl-incentivizing-truthful-llms]]'
  target_id: paper:2509.25760
  confidence: high
- type: related_to
  target: '[[group-relative-policy-optimization]]'
  target_id: method:group-relative-policy-optimization
  confidence: medium
- type: related_to
  target: '[[binary-grading-reinforces-hallucination]]'
  target_id: mechanism:binary-grading-reinforces-hallucination
  confidence: medium
- type: related_to
  target: '[[online-rl-outperforms-offline-rl]]'
  target_id: mechanism:online-rl-outperforms-offline-rl
  confidence: medium
- type: related_to
  target: '[[knowledge-boundary]]'
  target_id: term:knowledge-boundary
  confidence: medium
- type: related_to
  target: '[[abstention]]'
  target_id: term:abstention
  confidence: medium
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
  confidence: medium
- type: related_to
  target: '[[idk-sft]]'
  target_id: method:idk-sft
  confidence: medium
- type: related_to
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
  confidence: medium
- type: related_to
  target: '[[direct-preference-optimization]]'
  target_id: method:direct-preference-optimization
  confidence: medium
- type: related_to
  target: '[[over-abstention]]'
  target_id: term:over-abstention
  confidence: medium
---

A reinforcement learning framework implemented with GRPO that directly optimizes LLM truthfulness via a ternary reward signal (+1 correct, 0 abstain, -1 hallucinate), training models to reduce hallucinations both by answering correctly and by abstaining appropriately when knowledge is insufficient.

**Why it matters here:** Provides direct evidence that reward signal granularity (ternary vs. binary) determines whether RL training suppresses or preserves abstention capability, with up to 28.9 pp hallucination reduction and 21.1 pp truthfulness gain over vanilla RL across four benchmarks and two backbone families.

**Lineage:** Builds on group-relative-policy-optimization (GRPO) as the optimizer; contrasts with supervised-finetuning and direct-preference-optimization as offline alternatives; the knowledge boundary probing component extends idk-sft-style annotation to provide baselines rather than the core method.
