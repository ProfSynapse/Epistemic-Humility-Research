---
aliases:
- Knowledge fine-tuning erodes the unknown-query abstention boundary
- Disjoint knowledge updates collapse prior abstention behavior
- New fact tuning makes unsupported queries appear answerable
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:knowledge-finetuning-erodes-unknown-query-abstention-boundary
  type: mechanism
  status: canonical
cause: "Conventional full-parameter or low-rank fine-tuning memorizes a disjoint set of new facts without preserving the base model on nearby unknown inputs."
effect: "Previously separated unknown-query representations drift toward supported-query representations and the model replaces abstention with fabricated answers."
polarity: causes
related:
- '[[2506.14387--seat-sparse-entity-aware-tuning-knowledge-adaptation]]'
- '[[supervised-finetuning]]'
- '[[low-rank-adaptation]]'
- '[[abstention]]'
- '[[hallucination]]'
relationships:
- type: supported_by
  target: '[[2506.14387--seat-sparse-entity-aware-tuning-knowledge-adaptation]]'
  target_id: paper:2506.14387
  confidence: high
- type: related_to
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
  confidence: high
- type: related_to
  target: '[[low-rank-adaptation]]'
  target_id: method:low-rank-adaptation
  confidence: high
- type: related_to
  target: '[[abstention]]'
  target_id: term:abstention
  confidence: high
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
  confidence: high
---

Across PISTOL, TOFU, and post-cutoff news updates, ordinary full fine-tuning
preserved target memorization but reduced both automated and human abstention to
zero. LoRA also caused large losses. PCA visualizations associate the behavior
with loss of separation between supported and unsupported query activations,
but they do not identify a causal circuit.
