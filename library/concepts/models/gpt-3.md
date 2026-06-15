---
aliases:
- GPT3
- davinci
- GPT-3-175B
- GPT-3
tags:
- kg/model
- concept
- model
kg:
  id: model:gpt-3
  type: model
  status: canonical
area: models
related:
- '[[palm-2]]'
- '[[instructgpt]]'
relationships:
- type: related_to
  target: '[[palm-2]]'
  target_id: model:palm-2
- type: related_to
  target: '[[instructgpt]]'
  target_id: model:instructgpt
---

GPT-3 is OpenAI's 175-billion parameter autoregressive language model trained
on a large web corpus. It demonstrated strong few-shot learning across diverse
tasks without gradient updates, establishing the scale at which emergent
in-context capabilities become broadly reliable. The base (davinci) variant
predates RLHF instruction-tuning and thus serves as a clean baseline for
studying what calibration properties the pretrained distribution holds before
any alignment finetuning.

**Why it matters here:** GPT-3 is the primary model used in the verbalized
calibration finetuning study ([[2205.14334--teaching-models-uncertainty-in-words]])
to show that uncertainty expression can be learned via SFT even from a model
with no prior instruction-following training, grounding the broader claim that
calibrated abstention is a trainable skill.

**Lineage:** [[instructgpt]] is a later instruction-tuned and RLHF-aligned
descendant; [[palm-2]] is a contemporaneous large-scale autoregressive model
used in related calibration evaluations.
