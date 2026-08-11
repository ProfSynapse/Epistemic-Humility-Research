---
aliases:
- WinoGrande
- Winogrande
- WinoGrande benchmark
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:winogrande
  type: dataset
  status: canonical
area: datasets
related:
- '[[2407.09298--transformer-layers-as-painters]]'
- '[[2607.14111--introspection-fine-tuning-ift-training-small-llms]]'
- '[[hellaswag]]'
- '[[mmlu]]'
relationships:
- type: evaluation_set_for
  target: '[[2407.09298--transformer-layers-as-painters]]'
  target_id: paper:2407.09298
  confidence: high
- type: used_by
  target: '[[2607.14111--introspection-fine-tuning-ift-training-small-llms]]'
  target_id: paper:2607.14111
  confidence: high
- type: related_to
  target: '[[hellaswag]]'
  target_id: dataset:hellaswag
  confidence: medium
- type: related_to
  target: '[[mmlu]]'
  target_id: dataset:mmlu
  confidence: medium
---

WinoGrande is an adversarially filtered benchmark of Winograd-schema-style pronoun-resolution problems. It tests whether a model can resolve ambiguous references using contextual world knowledge rather than shallow surface cues.

**Why it matters here:** The benchmark is used both to compare semantic tasks with more order-sensitive reasoning tasks and to check whether introspection training preserves general language-model capability.

**Lineage:** Used in arXiv:2407.09298 and [[2607.14111--introspection-fine-tuning-ift-training-small-llms]]; this note does not attribute its proposal to either paper.
