---
aliases:
- zero-shot composition
- unseen behavior composition
- combinatorial generalization
- Compositional Generalization (in LLM steering)
- compositional transfer
- systematic generalization
- zero-shot compositional transfer
tags:
- kg/term
- concept
- term
kg:
  id: term:compositional-generalization
  type: term
  status: canonical
area: steering
related: []
relationships: []
---

Compositional generalization is the ability of a steering or training method to satisfy novel combinations of behaviors at inference time without having been trained on those specific combinations. The key axes of difficulty are unseen behavior pairs (held-out behavior combinations not present during composition training) and unseen numbers of behaviors (for example, 3-way composition learned only from 2-way examples). Achieving this property requires a model or steering system to treat individual behavioral directions as separable, recombinable primitives rather than entangled, holistic patterns.

**Why it matters here:** Compositional generalization is the central evaluation criterion for multi-behavior activation-steering methods: a method that cannot generalize beyond its training combinations provides only narrow coverage, while one that achieves zero-shot composition can be deployed over the combinatorial space of target behaviors from a compact set of primitives.

**Lineage:** no direct derivation; a prerequisite for scalable [[activation-steering]] and the main success criterion evaluated in [[steer2adapt]] and related frameworks.
