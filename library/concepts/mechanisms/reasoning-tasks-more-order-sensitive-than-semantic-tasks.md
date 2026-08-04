---
aliases:
- Reasoning Tasks Are More Order-Sensitive Than Semantic Tasks
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:reasoning-tasks-more-order-sensitive-than-semantic-tasks
  type: mechanism
  status: canonical
cause: Executing a frozen pretrained transformer's middle layers in reversed, random, or parallel order rather than the trained sequential order
effect: Mathematical/reasoning benchmarks (ARC, GSM8K) degrade substantially more than semantic benchmarks (HellaSwag, WinoGrande) under the same reordering interventions
polarity: increases
related:
- '[[2407.09298--transformer-layers-as-painters]]'
- '[[layer-order-permutation]]'
- '[[parallel-layer-execution]]'
relationships:
- type: supported_by
  target: '[[2407.09298--transformer-layers-as-painters]]'
  target_id: paper:2407.09298
  confidence: high
- type: related_to
  target: '[[layer-order-permutation]]'
  target_id: method:layer-order-permutation
- type: related_to
  target: '[[parallel-layer-execution]]'
  target_id: method:parallel-layer-execution
---

Applying reversed, random, or parallel layer execution to the middle-layer
block of a frozen pretrained transformer harms mathematical and reasoning
benchmarks (ARC, GSM8K) more than semantic and commonsense benchmarks
(HellaSwag, WinoGrande). This suggests reasoning-style tasks depend more on
step-order-sensitive sequential composition across layers, while semantic-
style tasks are more tolerant of computation being reordered or performed
non-sequentially.

**Why it matters here:** This mechanism refines the middle-layer-
substitutability picture along a task-type axis: substitutability and order-
tolerance are not uniform properties of the middle-layer block but depend on
what kind of computation the downstream task demands, which motivates
[[looping-parallel-layers-recovers-performance|looping]] as a partial fix
for the reasoning-task degradation caused by parallel execution.
