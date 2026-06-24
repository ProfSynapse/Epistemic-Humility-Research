---
aliases:
- capability-as-safety conflation
- benchmark conflation
tags:
- kg/term
- concept
- term
kg:
  id: term:safetywashing
  type: term
  status: canonical
area: terms
related:
- '[[2503.03750--mask-benchmark-honesty]]'
- '[[epistemic-alignment]]'
- '[[truthfulqa]]'
- '[[mask-benchmark]]'
- '[[lies-of-commission]]'
- '[[hallucination]]'
relationships:
- type: proposed_by
  target: '[[2503.03750--mask-benchmark-honesty]]'
  target_id: paper:2503.03750
  confidence: high
- type: related_to
  target: '[[epistemic-alignment]]'
  target_id: term:epistemic-alignment
  confidence: medium
- type: related_to
  target: '[[truthfulqa]]'
  target_id: dataset:truthfulqa
  confidence: medium
- type: related_to
  target: '[[mask-benchmark]]'
  target_id: dataset:mask-benchmark
  confidence: medium
- type: related_to
  target: '[[lies-of-commission]]'
  target_id: term:lies-of-commission
  confidence: medium
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
  confidence: medium
---

The phenomenon in which improved model capabilities (such as factual accuracy) are presented or interpreted as evidence of improved safety or trustworthiness, without establishing that the underlying safety-relevant behavior (such as honesty, refusal, or alignment) has actually improved. Typical example: citing higher TruthfulQA scores as evidence of reduced lying propensity, when those scores reflect factual knowledge gains rather than honest intent.

**Why it matters here:** Motivates the need for benchmarks like MASK that directly measure the target safety property (lying) rather than capability proxies. Also explains why frontier models can top accuracy benchmarks while exhibiting high P(Lie) on commission-honesty evaluations.

**Lineage:** Defined and studied in Ren et al. (2024) safetywashing paper (2407.21792); applied diagnostically in the MASK benchmark (2503.03750). Related to the epistemic-alignment concern and to over-reliance on TruthfulQA as an honesty proxy.
