---
aliases:
- Civil Comments
- Civil Comments toxicity dataset
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:civil-comments
  type: dataset
  status: canonical
area: datasets
related:
- '[[2510.21531--probe-based-fine-tuning-reducing-toxicity]]'
- '[[realtoxicityprompts]]'
relationships:
- type: used_by
  target: '[[2510.21531--probe-based-fine-tuning-reducing-toxicity]]'
  target_id: paper:2510.21531
  confidence: high
- type: related_to
  target: '[[realtoxicityprompts]]'
  target_id: dataset:realtoxicityprompts
  confidence: medium
---

Civil Comments is a corpus of public online comments with toxicity scores. The
paper trains probes and fine-tunes Gemma-3-1B on comments whose toxicity score
is at least 0.5.

**Why it matters here:** It provides a tractable testbed for training against a
latent toxicity readout and checking probe evasion.

**Lineage:** It is related to the generation-focused toxicity benchmark
[[realtoxicityprompts]].
