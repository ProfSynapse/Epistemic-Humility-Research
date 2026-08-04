---
aliases:
- Looping Parallel Layers Recovers Performance
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:looping-parallel-layers-recovers-performance
  type: mechanism
  status: canonical
cause: Looping a parallel-executed block of a frozen pretrained transformer's middle layers for a task-scaled number of iterations, instead of applying the parallel step only once
effect: Substantially recovers benchmark performance lost to a single parallel pass, making Looped Parallel the least-harmful reordering/parallel variant tested for both Llama2-7B and BERT-Large
polarity: increases
related:
- '[[2407.09298--transformer-layers-as-painters]]'
- '[[looped-parallel-layers]]'
- '[[reasoning-tasks-more-order-sensitive-than-semantic-tasks]]'
relationships:
- type: supported_by
  target: '[[2407.09298--transformer-layers-as-painters]]'
  target_id: paper:2407.09298
  confidence: high
- type: related_to
  target: '[[looped-parallel-layers]]'
  target_id: method:looped-parallel-layers
- type: related_to
  target: '[[reasoning-tasks-more-order-sensitive-than-semantic-tasks]]'
  target_id: mechanism:reasoning-tasks-more-order-sensitive-than-semantic-tasks
---

A single parallel pass over a span of middle layers (averaging their
independently computed outputs) degrades benchmark performance relative to
the original sequential order. Repeating that parallel step for a number of
iterations scaled to the task, feeding each iteration's output back in as the
next iteration's input, substantially recovers the lost performance. Across
both Llama2-7B and BERT-Large, this Looped Parallel variant is the least-
harmful of the order- and structure-perturbing interventions tested.

**Why it matters here:** This mechanism shows that the performance lost to
breaking sequential layer order is at least partly recoverable through
iterative refinement rather than strict sequential composition, softening
the order-sensitivity finding in
[[reasoning-tasks-more-order-sensitive-than-semantic-tasks]] and suggesting a
practical latency/accuracy trade-off: frozen models can run fewer distinct
layers more times rather than more distinct layers once.
