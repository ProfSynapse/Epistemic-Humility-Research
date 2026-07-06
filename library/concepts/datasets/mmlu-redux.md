---
aliases:
- MMLU-Redux
- MMLU Redux 2.0
- MMLU-Redux 2.0
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:mmlu-redux
  type: dataset
  status: canonical
area: benchmarks
related: []
relationships: []
---

MMLU-Redux is a cleaned version of the Massive Multitask Language Understanding
benchmark containing 5700 multiple-choice questions across 57 academic and
professional domains, filtered to 5280 questions after error annotation removed
mislabeled items. The benchmark emphasizes broad parametric knowledge recall
across disciplines rather than deep multi-step reasoning, making individual
questions answerable in a small number of tokens once the relevant fact is
retrieved.

**Why it matters here:** Because questions are largely recall-bound rather than
reasoning-bound, MMLU-Redux is well suited to probing performative
chain-of-thought: a model that knows the answer immediately may still generate
extended reasoning, and measuring when internal probes commit versus when emitted
tokens commit reveals the extent of that performance.

**Lineage:** derived from the original MMLU benchmark by re-annotation for label
quality; used as an evaluation surface for faithfulness and early-commitment
studies.
