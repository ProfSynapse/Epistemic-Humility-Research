---
aliases:
- plasticity-stability dilemma SFT
- factual plasticity
- factual stability
- stability-plasticity tradeoff in SFT
tags:
- kg/term
- concept
- term
kg:
  id: term:factual-plasticity-stability-tradeoff
  type: term
  status: canonical
area: terms
related:
- '[[2604.15574--why-finetuning-encourages-hallucinations]]'
- '[[supervised-finetuning]]'
- '[[slick]]'
- '[[hallucination]]'
- '[[knowledge-boundary]]'
- '[[sft-unknown-examples-drive-hallucination]]'
- '[[sft-self-distillation]]'
relationships:
- type: proposed_by
  target: '[[2604.15574--why-finetuning-encourages-hallucinations]]'
  target_id: paper:2604.15574
  confidence: high
- type: related_to
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
  confidence: medium
- type: related_to
  target: '[[slick]]'
  target_id: method:slick
  confidence: medium
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
  confidence: medium
- type: related_to
  target: '[[knowledge-boundary]]'
  target_id: term:knowledge-boundary
  confidence: medium
- type: related_to
  target: '[[sft-unknown-examples-drive-hallucination]]'
  target_id: mechanism:sft-unknown-examples-drive-hallucination
  confidence: medium
- type: related_to
  target: '[[sft-self-distillation]]'
  target_id: method:sft-self-distillation
  confidence: medium
---

The tension in supervised fine-tuning between factual plasticity (the model's capacity to acquire new facts from training data) and factual stability (the model's ability to retain pre-existing parametric knowledge); increasing plasticity tends to increase forgetting of previously known facts, operationalized as held-out HighlyKnown accuracy decline.

**Why it matters here:** Provides the organizing frame for understanding why SFT on Unknown facts induces hallucinations and why parameter-group freezing or output-distribution regularization can selectively control the tradeoff without sacrificing task learning.

**Lineage:** Transplants the stability-plasticity dilemma from continual learning literature into the LLM fine-tuning setting; measurement operationalized via the SLiCK three-way split into task-learning, factual-plasticity, and factual-stability evaluation sets.
