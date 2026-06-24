---
aliases:
- IOI task
- IOI benchmark
- Indirect Object Identification (IOI) Task
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:indirect-object-identification
  type: dataset
  status: canonical
area: mechanistic-interpretability
related:
- '[[sparse-feature-circuits]]'
- '[[attribution-patching]]'
- '[[circuit-faithfulness]]'
relationships:
- type: related_to
  target: '[[sparse-feature-circuits]]'
  target_id: method:sparse-feature-circuits
- type: related_to
  target: '[[attribution-patching]]'
  target_id: method:attribution-patching
- type: related_to
  target: '[[circuit-faithfulness]]'
  target_id: metric:circuit-faithfulness
---

A controlled syntactic benchmark where a language model must complete sentences
of the form "Alice and Bob went to the store. Alice gave a snack to ___",
requiring identification of the indirect object (the character who did not
perform the action). Introduced by Wang et al. (2022) as a circuit-analysis
testbed for GPT-2, it isolates a specific multi-step reasoning pattern in a
fully interpretable setting where ground-truth subjects and objects are
explicit.

**Why it matters here:** The IOI task is a standard circuit-discovery vehicle in
mechanistic interpretability; understanding how circuits are found and evaluated
on it provides grounding for evaluating whether similar circuits mediate
epistemic behaviors such as refusal or abstention.

**Lineage:** used extensively as a test case for [[attribution-patching]] and
for evaluating [[circuit-faithfulness]] scores; also a founding benchmark for
[[sparse-feature-circuits]] methodology.
