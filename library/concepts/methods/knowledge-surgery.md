---
aliases:
- knowledge editing via neurons
- neuron-level fact update
- knowledge erasing
- Knowledge Surgery (Neuron-Level Fact Editing)
tags:
- kg/method
- concept
- method
kg:
  id: method:knowledge-surgery
  type: method
  status: canonical
area: mechanistic-interpretability
related:
- '[[2104.08696--knowledge-neurons-pretrained-transformers]]'
- '[[knowledge-attribution]]'
- '[[knowledge-neurons]]'
- '[[model-editing]]'
relationships:
- type: proposed_by
  target: '[[2104.08696--knowledge-neurons-pretrained-transformers]]'
  target_id: paper:2104.08696
  confidence: high
- type: derived_from
  target: '[[knowledge-attribution]]'
  target_id: method:knowledge-attribution
- type: related_to
  target: '[[model-editing]]'
  target_id: method:model-editing
---

Knowledge Surgery edits factual knowledge stored in a pretrained Transformer without fine-tuning by directly modifying the value-slot weight vectors in FFN second layers that correspond to identified [[knowledge-neurons]]. A fact update replaces the weight vector to redirect the model toward a new tail entity; knowledge erasure zeroes out the value vectors for the targeted relation. Because the operation targets only the neurons identified by [[knowledge-attribution]], it can be applied with surgical precision and minimal collateral damage.

**Why it matters here:** Demonstrating that factual knowledge can be erased or redirected at the neuron level has direct implications for understanding the boundary between a model's stable stored knowledge and its susceptibility to hallucination or post-training behavioral change.

**Lineage:** requires [[knowledge-attribution]] to identify target neurons; a neuron-level alternative to weight-matrix editing approaches like [[model-editing]].
