---
aliases:
- AOC
- area over curve
- faithfulness AOC
- Faithfulness Area-Over-Curve (AOC)
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:faithfulness-area-over-curve
  type: metric
  status: canonical
area: verification
related:
- '[[2307.13702--measuring-faithfulness-chain-thought-reasoning]]'
- '[[early-answering]]'
- '[[adding-mistakes]]'
relationships:
- type: proposed_by
  target: '[[2307.13702--measuring-faithfulness-chain-thought-reasoning]]'
  target_id: paper:2307.13702
  confidence: high
- type: derived_from
  target: '[[early-answering]]'
  target_id: method:early-answering
---

The Faithfulness Area-Over-Curve (AOC) is a scalar summary of CoT faithfulness experiments that aggregates a performance curve over truncation lengths or perturbation counts into a single number. In [[early-answering]] experiments each curve point is model accuracy at a given CoT prefix length; in [[adding-mistakes]] experiments each point reflects accuracy when a fixed count of errors is injected into the chain. Each point is weighted by the fraction of test samples at that CoT length before summing, so the aggregate reflects the empirical distribution of reasoning trace lengths. Higher AOC indicates more post-hoc rationalization: the model's answer depends less on the visible reasoning steps, placing it closer to the unfaithful extreme of the 0-to-1 scale.

**Why it matters here:** AOC converts a multi-point faithfulness curve into a single comparable scalar, enabling cross-model ranking of how much CoT reasoning is genuinely predictive of the answer versus confabulated after the answer is fixed. That gap between stated reasoning and actual decision process is central to the [[epistemic-humility]] concern that models may report calibrated uncertainty without that uncertainty actually governing their outputs.

**Lineage:** derives from the [[early-answering]] and [[adding-mistakes]] experimental interventions; introduced in [[2307.13702--measuring-faithfulness-chain-thought-reasoning]].
