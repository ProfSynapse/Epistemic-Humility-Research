---
aliases:
- knowledge editing
- fact editing in LLMs
- model editing
tags:
- kg/method
- concept
- method
kg:
  id: method:model-editing
  type: method
  status: canonical
area: mechanistic-interpretability
related:
- '[[rank-one-model-editing]]'
- '[[knowledge-neurons]]'
- '[[knowledge-surgery]]'
relationships:
- type: related_to
  target: '[[rank-one-model-editing]]'
  target_id: method:rank-one-model-editing
- type: related_to
  target: '[[knowledge-neurons]]'
  target_id: term:knowledge-neurons
- type: related_to
  target: '[[knowledge-surgery]]'
  target_id: method:knowledge-surgery
---

Model editing is a family of techniques that update specific factual
associations stored in a pretrained language model's weights without retraining
the full model. Methods are evaluated on efficacy (the target fact is now
produced), generalization (paraphrase prompts also yield the new fact),
specificity (unrelated facts are unaffected), and sometimes fluency or
consistency of generated continuations.

**Why it matters here:** Model editing exposes the granularity at which
knowledge can be inserted or retracted, which bears directly on whether a model
can be made to correctly represent the boundaries of its own knowledge without
collateral damage to adjacent factual beliefs.

**Lineage:** subsumes [[rank-one-model-editing]] as a prominent instance;
overlaps with [[knowledge-neurons]] and [[knowledge-surgery]] as complementary
localization-then-edit pipelines.
