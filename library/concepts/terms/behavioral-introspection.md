---
aliases:
- Behavioral introspection
- Privileged self-prediction
- Introspective access to behavioral tendencies
tags:
- kg/term
- concept
- term
kg:
  id: term:behavioral-introspection
  type: term
  status: canonical
area: terms
related:
- '[[2410.13787--looking-inward-language-models-can-learn-about]]'
- '[[self-prediction-training]]'
- '[[self-knowledge]]'
relationships:
- type: proposed_by
  target: '[[2410.13787--looking-inward-language-models-can-learn-about]]'
  target_id: paper:2410.13787
  confidence: high
- type: related_to
  target: '[[self-prediction-training]]'
  target_id: method:self-prediction-training
  confidence: high
- type: related_to
  target: '[[self-knowledge]]'
  target_id: term:self-knowledge
  confidence: high
---

Behavioral introspection is the paper's operational construct for knowledge
about a model's own hypothetical behavior that cannot be inferred from the
provided behavioral training data alone. The test requires the target model to
outperform another model trained on the same examples about the target.

**Why it matters here:** It concerns privileged prediction of simple output
properties. It is not direct evidence that a model reads a particular hidden
activation or answerability variable.
