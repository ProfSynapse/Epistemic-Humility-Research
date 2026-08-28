---
aliases:
- sentence localization
- sentence-localization accuracy
- introspection via localization
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:sentence-localization-introspection
  type: metric
  status: canonical
area: metrics
related:
- '[[2512.12411--detecting-disturbance-nuanced-view-introspective-abilities-llms]]'
- '[[2607.14111--introspection-fine-tuning-ift-training-small-llms]]'
- '[[introspection-fine-tuning]]'
- '[[activation-steering]]'
relationships:
- type: proposed_by
  target: '[[2512.12411--detecting-disturbance-nuanced-view-introspective-abilities-llms]]'
  target_id: paper:2512.12411
  confidence: high
- type: proposed_by
  target: '[[2607.14111--introspection-fine-tuning-ift-training-small-llms]]'
  target_id: paper:2607.14111
  confidence: high
- type: related_to
  target: '[[introspection-fine-tuning]]'
  target_id: method:introspection-fine-tuning
  confidence: high
- type: related_to
  target: '[[activation-steering]]'
  target_id: method:activation-steering
  confidence: high
---

Sentence-localization introspection measures whether a model can identify which
of N labeled sentences received an activation injection. Each trial cycles the
same injection across positions and scores the argmax over sentence-index token
logits, giving chance accuracy of 1/N.

**Why it matters here:** Relative position selection avoids a global affirmative
response bias and demands spatially precise access to a controlled internal
perturbation.

**Lineage:** [[2512.12411--detecting-disturbance-nuanced-view-introspective-abilities-llms]]
introduces the metric for controlled [[activation-steering]]. It later becomes
the supervised target used by [[introspection-fine-tuning]].
