---
aliases:
- Bias Benchmark for QA
- Bias Benchmark for QA (BBQ)
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:bbq
  type: dataset
  status: canonical
area: benchmarks
related: []
relationships: []
---

BBQ is a hand-built benchmark that tests stereotype bias in question-answering
models across nine social bias categories (e.g., age, gender, race, religion).
Each item presents an ambiguous context and a question about a target individual,
with three answer choices: stereotype-aligned, counter-stereotyped, and
"unknown". A disambiguated version of each item adds context that resolves the
ambiguity, allowing separate measurement of bias under ambiguous and
disambiguated conditions; the gap between conditions reveals whether models
default to stereotypes when evidence is absent.

**Why it matters here:** BBQ probes a failure mode adjacent to epistemic
humility: a model that asserts stereotype-aligned answers when the context is
genuinely ambiguous exhibits [[overconfidence]] about social facts it cannot
know, mirroring the dynamic that motivates calibrated abstention in factual
question-answering.

**Lineage:** No formal method lineage; related in spirit to [[sycophancy]]
(social-pressure-driven answer shifts) and [[overconfidence]] (asserting claims
beyond available evidence).
