---
aliases:
- Looped Parallel
- looped parallel execution
tags:
- kg/method
- concept
- method
kg:
  id: method:looped-parallel-layers
  type: method
  status: canonical
area: mechanistic-interpretability
related:
- '[[2407.09298--transformer-layers-as-painters]]'
- '[[parallel-layer-execution]]'
relationships:
- type: proposed_by
  target: '[[2407.09298--transformer-layers-as-painters]]'
  target_id: paper:2407.09298
  confidence: medium
- type: variation_of
  target: '[[parallel-layer-execution]]'
  target_id: method:parallel-layer-execution
---

Looped Parallel repeats [[parallel-layer-execution|parallel layer
execution]] on the same middle-layer span for a fixed number of iterations,
scaled to the task, feeding each iteration's combined output back in as the
next iteration's input instead of applying the parallel step only once.

**Why it matters here:** Looping recovers most of the performance a single
parallel pass loses, making Looped Parallel the least-harmful of the
reordering/parallel variants tested for both Llama2-7B and BERT-Large, and
suggesting the middle-layer block behaves like an iterative refinement
process rather than a fixed sequence of distinct transformations.

**Lineage:** a variation of [[parallel-layer-execution|parallel layer
execution]] proposed in arXiv:2407.09298.
