---
aliases:
- factual hallucination
- hallucinating
tags:
- kg/term
- concept
- term
kg:
  id: term:hallucination
  type: term
  status: canonical
area: terms
---

Hallucination refers to the tendency of a language model to generate factually
incorrect outputs that are inconsistent with its pre-existing parametric
knowledge. In the context of the unfamiliar-finetuning-examples line of work, it
is operationalized as degraded closed-book QA accuracy on held-out test questions
after SFT, relative to the base model.

**Why it matters here:** Hallucination is the failure mode that the abstention
training research aims to prevent. Understanding whether hallucination stems from
unfamiliar SFT examples (rather than from SFT itself) directly shapes the
intervention strategy for teaching [[abstention]] without inflating refusal rates.

**Lineage:** related to [[knowledge-boundary]], [[abstention]], and
[[over-hedging]] as complementary failure modes.
