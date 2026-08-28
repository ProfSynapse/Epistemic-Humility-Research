---
aliases:
- strength comparison
- strength-comparison accuracy
- perturbation strength comparison
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:strength-comparison-introspection
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

Strength-comparison introspection measures whether a model can identify which of
two sentences received the stronger activation injection. Counterbalanced
sub-trials swap the strong and weak injection between positions, and accuracy is
computed from the argmax over the two sentence-index logits with 50 percent
chance performance.

**Why it matters here:** The matched-pairs design controls positional preference
and tests sensitivity to perturbation magnitude without relying on yes-or-no
self-reports.

**Lineage:** [[2512.12411--detecting-disturbance-nuanced-view-introspective-abilities-llms]]
introduces the metric using [[activation-steering]] as a controlled
intervention. It later serves as a held-out transfer evaluation for
[[introspection-fine-tuning]].
