---
aliases:
- Hypothetical self-prediction benchmark
- Looking Inward introspection dataset
- Behavioral-property self-prediction dataset
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:hypothetical-self-prediction-benchmark
  type: dataset
  status: canonical
area: datasets
related:
- '[[2410.13787--looking-inward-language-models-can-learn-about]]'
- '[[mmlu]]'
- '[[self-prediction-training]]'
relationships:
- type: proposed_by
  target: '[[2410.13787--looking-inward-language-models-can-learn-about]]'
  target_id: paper:2410.13787
  confidence: high
- type: related_to
  target: '[[mmlu]]'
  target_id: dataset:mmlu
  confidence: medium
- type: related_to
  target: '[[self-prediction-training]]'
  target_id: method:self-prediction-training
  confidence: high
---

The hypothetical self-prediction benchmark pairs prompts with properties of a
specific model's separately sampled response, such as its second character,
number parity, selected option group, or ethical stance. Six source datasets
are used for training and six are held out for evaluation while behavior
property types remain shared.

**Why it matters here:** It supplies model-specific labels for training and
testing [[behavioral-introspection]] across unseen prompt distributions.
