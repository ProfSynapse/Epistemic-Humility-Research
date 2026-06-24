---
aliases:
- ternary reward
- three-way reward
- ternary grading
tags:
- kg/method
- concept
- method
kg:
  id: method:ternary-reward-design
  type: method
  status: canonical
area: methods
related:
- '[[2509.25760--truthrl-incentivizing-truthful-llms]]'
- '[[group-relative-policy-optimization]]'
- '[[binary-grading-reinforces-hallucination]]'
- '[[abstention]]'
- '[[hallucination]]'
- '[[over-abstention]]'
- '[[truthrl]]'
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
  target: '[[abstention]]'
  target_id: term:abstention
  confidence: medium
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
  confidence: medium
- type: related_to
  target: '[[over-abstention]]'
  target_id: term:over-abstention
  confidence: medium
- type: related_to
  target: '[[truthrl]]'
  target_id: method:truthrl
  confidence: medium
---

A reward function for RL-based LLM training that distinguishes three output categories: correct answer (+1), abstention (0), and hallucination (-1). Under group-relative advantage estimation (GRPO), this produces a positive gradient toward abstention over hallucination in groups where no correct answer is sampled.

**Why it matters here:** The key technical insight of TruthRL: binary reward (-1 for both abstention and hallucination) gives the policy zero signal to prefer abstention; the ternary signal creates a strict ordering hallucination < abstention < correct without requiring annotated out-of-knowledge labels.

**Lineage:** Contrasts with binary-grading-reinforces-hallucination, which describes the failure mode this design overcomes; implemented inside group-relative-policy-optimization; related to idk-sft as an alternative mechanism for teaching abstention.
