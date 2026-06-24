---
aliases:
- Statement Accuracy Prediction based on Language Model Activations
- SAPLMA classifier
- hidden-layer truthfulness probe
tags:
- kg/method
- concept
- method
kg:
  id: method:saplma
  type: method
  status: canonical
area: methods
related:
- '[[2304.13734--internal-state-knows-lying]]'
- '[[linear-probe]]'
- '[[truth-direction]]'
- '[[self-knowledge]]'
- '[[generation-discrimination-gap]]'
- '[[mass-mean-probing]]'
relationships:
- type: proposed_by
  target: '[[2304.13734--internal-state-knows-lying]]'
  target_id: paper:2304.13734
  confidence: high
- type: related_to
  target: '[[linear-probe]]'
  target_id: method:linear-probe
  confidence: medium
- type: related_to
  target: '[[truth-direction]]'
  target_id: term:truth-direction
  confidence: medium
- type: related_to
  target: '[[self-knowledge]]'
  target_id: term:self-knowledge
  confidence: medium
- type: related_to
  target: '[[generation-discrimination-gap]]'
  target_id: term:generation-discrimination-gap
  confidence: medium
- type: related_to
  target: '[[mass-mean-probing]]'
  target_id: method:mass-mean-probing
  confidence: medium
---

A lightweight feedforward classifier (three hidden layers: 256/128/64 units, ReLU, sigmoid output) trained on hidden-layer activations of an LLM at a single chosen layer to predict whether a statement is true or false. Trained on activations from held-out topics and tested on unseen topics to force topic-general truthfulness detection rather than topic memorization. Requires no fine-tuning of the base LLM.

**Why it matters here:** Demonstrates that an LLM's internal state encodes statement truthfulness well beyond what prompting-based or embedding-based methods can recover, motivating hidden-state probing as a practical truth-detection strategy without modifying model weights.

**Lineage:** Proposed in Azaria and Mitchell (2023, arXiv 2304.13734); contemporaneous with Burns et al. CCS but distinguishes itself by out-of-distribution topic evaluation and by not requiring rephrasing of statements into questions.
