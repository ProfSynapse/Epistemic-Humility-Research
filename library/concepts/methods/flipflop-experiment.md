---
aliases:
- FlipFlop
- flip-flop experiment
- FlipFlop protocol
tags:
- kg/method
- concept
- method
kg:
  id: method:flipflop-experiment
  type: method
  status: canonical
area: methods
related:
- '[[2311.08596--flipflop-experiment]]'
- '[[sycophancy]]'
- '[[flipflop-effect]]'
- '[[legalbench]]'
- '[[sciq]]'
- '[[truthfulqa]]'
- '[[arc-challenge]]'
relationships:
- type: proposed_by
  target: '[[2311.08596--flipflop-experiment]]'
  target_id: paper:2311.08596
  confidence: high
- type: related_to
  target: '[[sycophancy]]'
  target_id: term:sycophancy
  confidence: medium
- type: related_to
  target: '[[flipflop-effect]]'
  target_id: metric:flipflop-effect
  confidence: medium
- type: related_to
  target: '[[legalbench]]'
  target_id: dataset:legalbench
  confidence: medium
- type: related_to
  target: '[[sciq]]'
  target_id: dataset:sciq
  confidence: medium
- type: related_to
  target: '[[truthfulqa]]'
  target_id: dataset:truthfulqa
  confidence: medium
- type: related_to
  target: '[[arc-challenge]]'
  target_id: dataset:arc-challenge
  confidence: medium
---

A two-turn evaluation protocol for measuring sycophantic answer revision in LLMs. In turn one the model completes a classification task; in turn two the model receives a challenger utterance (e.g., 'Are you sure?') without any new evidence and must decide whether to confirm or flip its initial label. An optional third confirmation turn recovers label extractions that the challenger response fails to resolve. The primary output metric is ΔFF (final accuracy minus initial accuracy).

**Why it matters here:** Provides a controlled, scalable diagnostic for sycophantic capitulation that ties model behavior directly to classification accuracy changes, enabling comparisons across model families, task domains, and challenger wordings.

**Lineage:** Proposed by Laban et al. 2023 (arXiv 2311.08596); builds on sycophancy observations in Perez et al. 2022 and Wei et al. 2023 (arXiv 2308.03958).
