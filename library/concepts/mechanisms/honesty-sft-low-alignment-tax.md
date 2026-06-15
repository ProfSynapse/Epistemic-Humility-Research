---
aliases:
- Honesty SFT Incurs Low Alignment Tax
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:honesty-sft-low-alignment-tax
  type: mechanism
  status: canonical
cause: '[[honesty-oriented-sft]] that teaches a model to refuse unknown questions while correctly answering known ones'
effect: Negligible reduction in general helpfulness scores relative to standard SFT, indicating a low [[alignment-tax]]
polarity: decreases
related:
- '[[2312.07000--alignment-for-honesty]]'
- '[[honesty-oriented-sft]]'
- '[[alignment-tax]]'
relationships:
- type: supported_by
  target: '[[2312.07000--alignment-for-honesty]]'
  target_id: paper:2312.07000
  confidence: high
- type: related_to
  target: '[[honesty-oriented-sft]]'
  target_id: method:honesty-oriented-sft
- type: related_to
  target: '[[alignment-tax]]'
  target_id: term:alignment-tax
---

Because honesty-oriented SFT only changes model behavior on a subset of questions (those outside the knowledge boundary), it does not substantially alter the model's responses to questions it can correctly answer. The alignment-for-honesty paper (arXiv:2312.07000) measures helpfulness on standard benchmarks after honesty SFT and finds negligible degradation, suggesting that teaching abstention does not erode general instruction-following ability. This is a favorable trade-off relative to the [[over-hedging]] failure mode seen in reward-based approaches.
