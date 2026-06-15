---
aliases:
- P_Correct
- P(Correct)
- sampling-based correctness score
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:p-correct
  type: metric
  status: canonical
area: metrics
related:
- '[[2405.05904--finetuning-new-knowledge-hallucinations]]'
- '[[slick]]'
- '[[knowledge-boundary]]'
- '[[p-true]]'
- '[[p-ik]]'
relationships:
- type: proposed_by
  target: '[[2405.05904--finetuning-new-knowledge-hallucinations]]'
  target_id: paper:2405.05904
  confidence: high
- type: related_to
  target: '[[slick]]'
  target_id: method:slick
- type: related_to
  target: '[[knowledge-boundary]]'
  target_id: term:knowledge-boundary
- type: related_to
  target: '[[p-true]]'
  target_id: method:p-true
- type: related_to
  target: '[[p-ik]]'
  target_id: method:p-ik
---

P_Correct is a continuous measure of a model's factual knowledge about a
specific question-answer pair, computed as the fraction of independently sampled
model outputs that match the ground-truth answer. Rather than relying on a single
generation or a calibrated log-probability, it aggregates across multiple samples
to estimate how reliably the model can produce the correct response.

**Why it matters here:** P_Correct is the measurement primitive that [[slick]]
uses to assign knowledge-tier labels to fine-tuning examples, which in turn lets
abstention studies identify which training examples lie outside the model's
knowledge boundary and are therefore likely to induce hallucination.

**Lineage:** related to [[p-true]] and [[p-ik]] as sibling sampling-based or
probability-based self-knowledge measures; used as a prerequisite input to
[[slick]] for knowledge categorization.
