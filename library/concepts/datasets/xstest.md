---
aliases:
- XSTest
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:xstest
  type: dataset
  status: canonical
area: datasets
related: []
relationships: []
---

XSTest is a benchmark of prompts designed to probe exaggerated safety
behavior: it pairs safe prompts that superficially resemble unsafe ones (to
test for over-refusal) with genuinely unsafe prompts (to test that refusal
still occurs), letting evaluators separate under-refusal from over-refusal
rather than scoring safety compliance as a single number.

**Why it matters here:** it is used to check whether interventions on
massive-activation rigidity shift the over-refusal / under-refusal balance
rather than just aggregate safety scores.

**Lineage:** no direct predecessors encoded in this graph.
