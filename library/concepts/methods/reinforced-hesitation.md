---
aliases:
- RH
- reinforced hesitation training
- ternary RLVR
tags:
- kg/method
- concept
- method
kg:
  id: method:reinforced-hesitation
  type: method
  status: canonical
area: methods
related:
- '[[2511.11500--reinforced-hesitation]]'
- '[[ternary-reward-design]]'
- '[[ternary-reward-enables-abstention-over-hallucination]]'
- '[[group-relative-policy-optimization]]'
- '[[binary-grading-reinforces-hallucination]]'
- '[[abstention]]'
- '[[over-abstention]]'
- '[[rlvr-post-training-degrades-abstention]]'
- '[[reasoning-finetuning-degrades-abstention]]'
relationships:
- type: proposed_by
  target: '[[2511.11500--reinforced-hesitation]]'
  target_id: paper:2511.11500
  confidence: high
- type: related_to
  target: '[[ternary-reward-design]]'
  target_id: method:ternary-reward-design
  confidence: medium
- type: related_to
  target: '[[ternary-reward-enables-abstention-over-hallucination]]'
  target_id: mechanism:ternary-reward-enables-abstention-over-hallucination
  confidence: medium
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
  target: '[[over-abstention]]'
  target_id: term:over-abstention
  confidence: medium
- type: related_to
  target: '[[rlvr-post-training-degrades-abstention]]'
  target_id: mechanism:rlvr-post-training-degrades-abstention
  confidence: medium
- type: related_to
  target: '[[reasoning-finetuning-degrades-abstention]]'
  target_id: mechanism:reasoning-finetuning-degrades-abstention
  confidence: medium
---

A modification to RLVR post-training that replaces the binary reward (+1 correct, 0 wrong) with a ternary structure (+1 correct, 0 abstain, -lambda wrong), where the penalty lambda encodes domain-specific error costs and sets the rational confidence threshold for answering at 1/(1+lambda). Applied after pretraining and RLHF via Dr.GRPO with no architectural changes.

**Why it matters here:** The first controlled demonstration that a single scalar change to the RLVR reward tuple teaches difficulty-calibrated abstention: 60-95% on hard problems, 5-15% on easy problems, error rate collapse from 15% to below 2%, and an unexpected 25-30% inference compute reduction; all from varying lambda while holding architecture and optimizer constant.

**Lineage:** Extends binary RLVR (DeepSeek-R1, TULU-3) by adding an abstention option with neutral reward; shares the ternary reward structure with TruthRL (2509.25760) but focuses on difficulty calibration and the Pareto frontier across risk regimes rather than hallucination-vs-truth discrimination. Implemented on Qwen3-1.7B with Dr.GRPO.
