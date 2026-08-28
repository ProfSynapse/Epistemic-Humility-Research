---
aliases:
- CB-LLM
- CB-LLMs
- Concept Bottleneck Large Language Models
- concept-bottleneck language model
tags:
- kg/method
- concept
- method
kg:
  id: method:concept-bottleneck-large-language-model
  type: method
  status: canonical
area: methods
related:
- '[[2412.07992--concept-bottleneck-large-language-models]]'
- '[[concept-bottleneck-layer]]'
- '[[adversarial-debiasing]]'
relationships:
- type: proposed_by
  target: '[[2412.07992--concept-bottleneck-large-language-models]]'
  target_id: paper:2412.07992
  confidence: high
- type: required_by
  target: '[[concept-bottleneck-layer]]'
  target_id: term:concept-bottleneck-layer
  confidence: high
- type: related_to
  target: '[[adversarial-debiasing]]'
  target_id: method:adversarial-debiasing
  confidence: high
---

Concept Bottleneck Large Language Models insert a layer of supervised, human-interpretable concept neurons before a linear prediction or token-unembedding layer. The generation variant pairs those neurons with unsupervised features and adversarially removes concept information from the unsupervised path so output remains controllable through the named neurons.

**Why it matters here:** The architecture makes a supervised internal concept signal part of the causal path to autoregressive token generation.

**Lineage:** It extends the [[concept-bottleneck-layer]] design to large-scale text classification and autoregressive generation, with [[adversarial-debiasing]] used to prevent concept leakage through the parallel unsupervised path.
