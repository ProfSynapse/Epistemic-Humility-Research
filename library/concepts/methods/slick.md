---
aliases:
- Sampling-based Categorization of Knowledge
- knowledge categorization
- SliCK (Sampling-based Categorization of Knowledge)
tags:
- kg/method
- concept
- method
kg:
  id: method:slick
  type: method
  status: canonical
area: methods
related:
- '[[2405.05904--finetuning-new-knowledge-hallucinations]]'
- '[[knowledge-boundary]]'
- '[[p-correct]]'
- '[[unfamiliar-finetuning-examples]]'
relationships:
- type: proposed_by
  target: '[[2405.05904--finetuning-new-knowledge-hallucinations]]'
  target_id: paper:2405.05904
  confidence: high
- type: derived_from
  target: '[[knowledge-boundary]]'
  target_id: term:knowledge-boundary
- type: related_to
  target: '[[p-correct]]'
  target_id: metric:p-correct
- type: related_to
  target: '[[unfamiliar-finetuning-examples]]'
  target_id: term:unfamiliar-finetuning-examples
---

SliCK (Sampling-based Categorization of Knowledge) classifies each fine-tuning
example into one of four knowledge tiers (HighlyKnown, MaybeKnown, WeaklyKnown,
Unknown) by computing a continuous P_Correct score from multiple independently
sampled model outputs and thresholding that score. The Unknown tier marks facts
that are most likely absent from the model's pre-training distribution, making
them candidates for hallucination risk when included in supervised fine-tuning.

**Why it matters here:** SliCK operationalizes the knowledge-boundary concept
that motivates abstention training: by tagging which training examples fall
outside the model's knowledge, it allows researchers to study how Unknown
examples drive hallucination and how abstention methods should handle them.

**Lineage:** extends [[knowledge-boundary]] by turning it from a binary notion
into a four-tier continuous-score taxonomy; relies on [[p-correct]] as the
underlying measurement primitive.
