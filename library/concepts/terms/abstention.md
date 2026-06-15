---
aliases:
- I don't know response
- abstention response
- idk sign
- refusal response
- idk response
- refusal to answer
- saying I don't know
- IDK refusal
- LLM abstention
- abstain
- I don't know
- selective abstention
- IDK response
tags:
- kg/term
- concept
- term
kg:
  id: term:abstention
  type: term
  status: canonical
area: terms
---

Abstention is the behavior of an LLM deliberately declining to provide a
factual answer to a question, typically by producing a natural-language
expression of uncertainty or ignorance (for example, "I don't know" or "I'm not
sure"). It is treated in the epistemic-humility literature as the correct
response when a question falls outside the model's [[knowledge-boundary]], in
contrast to hallucinating a plausible but incorrect answer.

**Why it matters here:** Abstention is the target behavior the Phase 1
SFT-vs-DPO-vs-KTO study seeks to induce and measure. The central tension is
that training for abstention risks [[over-abstention]] (declining answerable
questions), so the study evaluates each training method against both
[[prudence-score]] (beneficial abstention) and [[over-conservativeness-score]]
(harmful abstention), using [[abstention-rate]] as an aggregate signal.

**Lineage:** operationalized as a measurable behavior via [[abstention-rate]];
decomposed into beneficial and spurious components by [[honesty-oriented-sft]]
and related metrics; surveyed broadly in [[2407.18418--know-your-limits-abstention-survey]].
