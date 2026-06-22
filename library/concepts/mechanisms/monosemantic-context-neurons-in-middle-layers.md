---
aliases:
- Middle layers contain dedicated monosemantic context neurons
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:monosemantic-context-neurons-in-middle-layers
  type: mechanism
  status: canonical
cause: High-level context features (language, programming language, data source) being sufficiently important and not mutually exclusive with other sequence-level features
effect: Middle-layer neurons dedicated exclusively to one context feature emerge; ablating a single such neuron in Pythia-70M increases French sequence loss by 8%, while in Pythia-6.9B the effect is only 0.2% (redundancy at scale)
polarity: enables
related:
- '[[2305.01610--finding-neurons-haystack-sparse-probing]]'
- '[[monosemanticity]]'
- '[[pythia-suite]]'
- '[[neuron-ablation]]'
relationships:
- type: supported_by
  target: '[[2305.01610--finding-neurons-haystack-sparse-probing]]'
  target_id: paper:2305.01610
  confidence: high
- type: related_to
  target: '[[monosemanticity]]'
  target_id: term:monosemanticity
- type: related_to
  target: '[[pythia-suite]]'
  target_id: model:pythia-suite
- type: related_to
  target: '[[neuron-ablation]]'
  target_id: method:neuron-ablation
---

In contrast to polysemantic early-layer neurons, middle layers of Pythia models contain genuinely monosemantic neurons dedicated to a single high-level context feature such as natural language identity or programming language (arXiv:2305.01610). In Pythia-70M, ablating a single French-language neuron raises loss on French text by 8%, confirming its functional necessity; in Pythia-6.9B the same ablation yields only a 0.2% loss increase, reflecting the redundancy that large-scale models develop through distributed representations. This size-dependent functional criticality illustrates how architectural scale shifts single neurons from irreplaceable to interchangeable for coarse context features.
