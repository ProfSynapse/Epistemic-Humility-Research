---
aliases:
- knowledge localization
- localization of factual knowledge
- subject last token effect
tags:
- kg/term
- concept
- term
kg:
  id: term:factual-recall-localization
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[hallucination]]'
- '[[knowledge-boundary]]'
- '[[mid-layer-mlp-mediates-factual-recall]]'
- '[[factual-association-recall-mechanism]]'
relationships:
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
- type: related_to
  target: '[[knowledge-boundary]]'
  target_id: term:knowledge-boundary
- type: related_to
  target: '[[mid-layer-mlp-mediates-factual-recall]]'
  target_id: mechanism:mid-layer-mlp-mediates-factual-recall
- type: related_to
  target: '[[factual-association-recall-mechanism]]'
  target_id: term:factual-association-recall-mechanism
---

Factual recall localization is the empirical finding that factual recall in language models is mediated by specific layers and token positions rather than being uniformly distributed. Middle-layer MLPs at the last subject token show strong causal effects (the "early site"), while later attention layers at the last prompt token mediate attribute retrieval and output projection (the "late site"). This two-site structure has been confirmed across both transformer and SSM architectures.

**Why it matters here:** If factual knowledge is localized, then targeted interventions (editing, suppression, auditing) become feasible, directly informing strategies for controlling hallucination and calibrating a model's expressed confidence to its actual stored knowledge.

**Lineage:** related to [[mid-layer-mlp-mediates-factual-recall]] (the specific MLP causal finding), [[factual-association-recall-mechanism]] (the broader functional account), [[hallucination]] (failure mode when localization breaks down), and [[knowledge-boundary]] (the conceptual limit factual localization helps operationalize).
