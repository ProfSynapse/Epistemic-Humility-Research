---
title: Toy Models of Superposition
tags:
- kg/paper
- paper
- epistemic-humility
- mechanistic-interpretability
kg:
  id: paper:tc2022
  type: paper
  status: canonical
year: 2022
url: https://transformer-circuits.pub/2022/toy_model/index.html
area: mechanistic-interpretability
status: fetched
source: blog
source_kind: transformer-circuits
authors:
- Nelson Elhage
- Tristan Hume
- Catherine Olsson
- et al. (Anthropic, Transformer Circuits Thread)
models: []
metrics: []
fulltext: ../fulltext/tc2022--toy-models-of-superposition.html
provenance: 'Awesome-MI ingest batch 2 2026-06-19: non-arxiv source; prose extracted from page HTML into fulltext/. Not in manifest.yaml (arxiv-keyed).'
related:
- '[[toy-model-of-superposition]]'
- '[[superposition-phase-diagram]]'
- '[[superposition-geometry]]'
- '[[superposition-hypothesis]]'
- '[[polysemanticity]]'
- '[[linear-representation-hypothesis]]'
- '[[privileged-basis]]'
- '[[sparsity-enables-superposition]]'
- '[[superposition-causes-polysemanticity]]'
- '[[superposition-creates-adversarial-vulnerability]]'
- '[[importance-sparsity-governs-superposition-phase]]'
relationships:
- type: proposes
  target: '[[toy-model-of-superposition]]'
  target_id: method:toy-model-of-superposition
- type: proposes
  target: '[[superposition-phase-diagram]]'
  target_id: method:superposition-phase-diagram
- type: proposes
  target: '[[superposition-geometry]]'
  target_id: term:superposition-geometry
- type: studies
  target: '[[superposition-hypothesis]]'
  target_id: term:superposition-hypothesis
- type: studies
  target: '[[polysemanticity]]'
  target_id: term:polysemanticity
- type: studies
  target: '[[linear-representation-hypothesis]]'
  target_id: term:linear-representation-hypothesis
- type: studies
  target: '[[privileged-basis]]'
  target_id: term:privileged-basis
- type: supports
  target: '[[sparsity-enables-superposition]]'
  target_id: mechanism:sparsity-enables-superposition
- type: supports
  target: '[[superposition-causes-polysemanticity]]'
  target_id: mechanism:superposition-causes-polysemanticity
- type: supports
  target: '[[superposition-creates-adversarial-vulnerability]]'
  target_id: mechanism:superposition-creates-adversarial-vulnerability
- type: supports
  target: '[[importance-sparsity-governs-superposition-phase]]'
  target_id: mechanism:importance-sparsity-governs-superposition-phase
proposes: ["[[toy-model-of-superposition]]", "[[superposition-phase-diagram]]", "[[superposition-geometry]]"]
studies: ["[[superposition-hypothesis]]", "[[polysemanticity]]", "[[linear-representation-hypothesis]]", "[[privileged-basis]]"]
mechanisms: ["[[sparsity-enables-superposition]]", "[[superposition-causes-polysemanticity]]", "[[superposition-creates-adversarial-vulnerability]]", "[[importance-sparsity-governs-superposition-phase]]"]
---
## Abstract

<!-- non-arxiv source; see fulltext/ for full prose -->

## Summary

<!-- filled during extraction -->

## Relevance to experiment

<!-- mech-interp of features/superposition; mechanism program probing context -->

## Claims

- Small ReLU networks trained on 5 sparse features in 2 hidden dimensions learn to represent all 5 features in superposition rather than discarding 3, demonstrating that neural networks can store more features than dimensions when features are sparse. (Introduction / Figure 1 (5-feature 2-dimension toy model)) [[superposition-hypothesis]]
- The transition between not-learned, superposition, and dedicated-dimension regimes is a first-order phase change governed jointly by feature sparsity and relative feature importance, confirmed analytically in the 2-feature 1-hidden-dimension theoretical model. (Section 'Superposition as a Phase Change') [[superposition-phase-diagram]]
- In uniform superposition (equal importance and sparsity), features organize into geometric structures corresponding to uniform polytopes—digons (1/2), triangles (2/3), tetrahedra (3/4), pentagons (2/5), square antiprisms (3/8)—with fractional feature dimensionalities clustering at these values. (Section 'The Geometry of Superposition' / feature dimensionality scatter plot) [[superposition-geometry]]
- At least some circuits (absolute value computation) can be performed while features are stored in superposition, supporting the hypothesis that real neural networks noisily simulate larger, highly sparse networks. (Section 'Computation in Superposition') [[toy-model-of-superposition]]
