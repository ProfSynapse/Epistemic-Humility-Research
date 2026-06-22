---
aliases:
- uniform polytopes in superposition
- geometric structure of superposition
- feature geometry
- Geometry of Superposition
tags:
- kg/term
- concept
- term
kg:
  id: term:superposition-geometry
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[tc2022--toy-models-of-superposition]]'
- '[[toy-model-of-superposition]]'
relationships:
- type: proposed_by
  target: '[[tc2022--toy-models-of-superposition]]'
  target_id: paper:tc2022
  confidence: high
- type: derived_from
  target: '[[toy-model-of-superposition]]'
  target_id: method:toy-model-of-superposition
---

Superposition geometry is the empirical finding that when neural networks store features in superposition, the feature embedding vectors do not scatter arbitrarily but instead self-organize into geometric structures corresponding to uniform polytopes: digons, triangles, pentagons, tetrahedra, and square antiprisms, among others. The optimal placement of n feature vectors into m dimensions minimizes pairwise interference, connecting the problem formally to the Thomson problem of distributing unit charges uniformly on a sphere.

**Why it matters here:** The regularity of superposition geometry implies that interference between co-embedded features follows predictable patterns. For epistemic-humility research, this suggests that errors or hallucinations arising from feature collision may have geometric signatures that interpretability tools could detect or probe.

**Lineage:** derives from [[toy-model-of-superposition]]; introduced in [[tc2022--toy-models-of-superposition]].
