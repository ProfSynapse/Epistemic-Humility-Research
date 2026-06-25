---
aliases:
- Sentence resampling
- Resampling-based sentence importance
tags:
- kg/method
- concept
- method
kg:
  id: method:sentence-resampling
  type: method
  status: canonical
area: methods
related:
- '[[2606.26071--model-forensics-investigating-whether-concerning-behavior-reflects]]'
- '[[repeated-resampling]]'
relationships:
- type: related_to
  target: '[[2606.26071--model-forensics-investigating-whether-concerning-behavior-reflects]]'
  target_id: paper:2606.26071
  confidence: high
- type: related_to
  target: '[[repeated-resampling]]'
  target_id: method:repeated-resampling
  confidence: high
---

A trace-attribution method that estimates each sentence's causal influence on an outcome by resampling continuations from that point and measuring how the outcome rate shifts. In Model Forensics it surfaces which CoT sentences most push a model toward a behavior (the "huge task" remark for Kimi, self-consistency sentences for R1).

**Why it matters here:** it focuses scarce researcher effort on the trace segments that actually drive a concerning action, before designing counterfactuals.

**Lineage:** introduced by Bogdan et al. 2025; complemented by [[repeated-resampling]] for intervening on (not just measuring) influential sentences, and by turn-level resampling for long agentic trajectories.
