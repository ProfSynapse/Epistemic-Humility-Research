---
aliases:
- persona vector
- trait direction
- character trait direction
- persona direction
- character trait vector
- behavioral trait direction
tags:
- kg/method
- concept
- method
kg:
  id: method:persona-vectors
  type: method
  status: canonical
area: steering
related:
- '[[2507.21509--persona-vectors-monitoring-controlling-character-traits-language]]'
- '[[activation-steering]]'
- '[[difference-in-means]]'
relationships:
- type: proposed_by
  target: '[[2507.21509--persona-vectors-monitoring-controlling-character-traits-language]]'
  target_id: paper:2507.21509
  confidence: high
- type: derived_from
  target: '[[activation-steering]]'
  target_id: method:activation-steering
---

Persona vectors are linear directions in a model's residual stream that correspond to specific character or personality traits such as sycophancy, hallucination, or harmful intent. They are extracted by an automated pipeline that generates contrastive system prompts, collects model responses, and computes the [[difference-in-means]] between trait-expressing and trait-suppressing activation sets. A single persona vector supports three downstream uses: monitoring via projection onto hidden states during inference, behavioral control via addition to residual activations, and pre-finetuning dataset screening via the [[projection-difference]] metric.

**Why it matters here:** Sycophancy and overconfident output are trait-like patterns that epistemic humility training aims to suppress; persona vectors provide a geometry-grounded probe for verifying that a training intervention moves these traits in the intended direction rather than installing them as side effects.

**Lineage:** derived from [[activation-steering]]; uses [[difference-in-means]] as the extraction primitive; [[preventative-steering]] applies the resulting vector at training time rather than inference time.
