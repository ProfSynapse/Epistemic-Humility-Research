---
aliases:
- Cooperate
- cooperative multi-LLM abstention
- LLM cooperative abstention
- Cooperate (multi-LLM abstention)
tags:
- kg/method
- concept
- method
kg:
  id: method:multi-llm-cooperate
  type: method
  status: canonical
area: methods
related:
- '[[2402.00367--dont-hallucinate-abstain]]'
- '[[multi-llm-compete]]'
- '[[self-consistency]]'
relationships:
- type: proposed_by
  target: '[[2402.00367--dont-hallucinate-abstain]]'
  target_id: paper:2402.00367
  confidence: high
- type: variation_of
  target: '[[multi-llm-compete]]'
  target_id: method:multi-llm-compete
- type: related_to
  target: '[[self-consistency]]'
  target_id: method:self-consistency
---

Multi-LLM Cooperate is an abstention method in which multiple expert language
models each provide natural-language feedback on a candidate answer, and a
separate judge LLM synthesises that feedback to decide whether to accept the
answer or abstain. The cooperative framing differs from [[multi-llm-compete]] in
that the expert models collaborate toward a shared verdict rather than competing
for dominance, leveraging complementary knowledge coverage to reduce both
hallucination and over-abstention.

**Why it matters here:** Multi-LLM Cooperate establishes a multi-model ceiling
for the abstention task, against which the single-model SFT, DPO, and KTO
fine-tuning approaches in the locked training-regimen study can be benchmarked to understand how
much of the gap is attributable to training method versus ensemble-level knowledge
breadth.

**Lineage:** variant of [[multi-llm-compete]] (same paper, cooperative rather
than competitive verdict aggregation); related to [[self-consistency]] via the
shared principle of aggregating multiple model outputs before committing to a
decision.
