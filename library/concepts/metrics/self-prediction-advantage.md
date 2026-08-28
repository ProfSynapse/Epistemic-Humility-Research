---
aliases:
- Self-prediction advantage
- Cross-prediction disadvantage
- Own-behavior prediction advantage
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:self-prediction-advantage
  type: metric
  status: canonical
area: metrics
related:
- '[[2410.13787--looking-inward-language-models-can-learn-about]]'
- '[[cross-prediction-introspection-test]]'
relationships:
- type: proposed_by
  target: '[[2410.13787--looking-inward-language-models-can-learn-about]]'
  target_id: paper:2410.13787
  confidence: high
- type: related_to
  target: '[[cross-prediction-introspection-test]]'
  target_id: method:cross-prediction-introspection-test
  confidence: high
---

Self-prediction advantage is the target model's accuracy at predicting its own
behavior minus a different model's accuracy at predicting that same target,
after matched behavioral training. Positive values on held-out tasks are the
paper's primary evidence for privileged behavioral self-knowledge.

**Why it matters here:** It makes the evidence depend on a matched cross-model
control rather than self-report accuracy alone.
