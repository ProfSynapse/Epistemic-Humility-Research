---
aliases:
- LLM knowledge gap
- missing knowledge
tags:
- kg/term
- concept
- term
kg:
  id: term:knowledge-gap
  type: term
  status: canonical
area: terms
---

A knowledge gap is missing or outdated information in an LLM's parametric
knowledge that prevents it from answering a question correctly. It arises from
training-data cutoffs, coverage gaps, or domain sparsity, and is distinct from
reasoning failure: the model simply was never exposed to the fact.

**Why it matters here:** Identifying knowledge gaps is the core motivation for
abstention research; the locked training-regimen study examines whether SFT, DPO, and KTO can
teach a model to recognize its own gaps and abstain rather than hallucinate.

**Lineage:** closely related to [[knowledge-boundary]] (the boundary between
what the model knows and does not know) and to [[hallucination]] (the failure
mode that knowledge-gap-aware abstention is designed to prevent).
