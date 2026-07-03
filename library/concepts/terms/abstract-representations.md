---
aliases:
- parallel abstract representations
- high-parallelism representations
- abstract neural representations
- Abstract (Parallel) Representations
tags:
- kg/term
- concept
- term
kg:
  id: term:abstract-representations
  type: term
  status: canonical
area: neuroscience
related: []
relationships: []
---

Abstract representations are neural encodings in which changing one compositional variable produces the same directional shift in activation space regardless of the settings of all other variables: the representational geometry is parallel across contexts. This property is operationalized by the [[parallelism-score]] (PS near 1 signals high abstraction) and contrasts with context-specific or entangled encodings in which the same conceptual change maps to different directions depending on the surrounding context. Abstract representations are measurable in both biological neural systems via fMRI and in artificial networks via hidden-layer activations, making them a cross-domain geometric signature of [[compositional-generalization]].

**Why it matters here:** If a model's internal uncertainty or knowledge-state representations are abstract in this sense, they can generalize to novel query contexts without retraining, which is the core desideratum for robust epistemic humility. Entangled representations predict brittle, context-locked behavior.

**Lineage:** quantified by [[parallelism-score]]; promoted in ANNs by [[primitives-pretraining]]; tested in the [[c-pro-task]] paradigm; shares structural motivation with [[disentangled-representation]] in machine learning.
