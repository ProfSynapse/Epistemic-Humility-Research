---
aliases:
- LongElicitPrompts
- Long Elicit Prompts
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:long-elicit-prompts
  type: dataset
  status: canonical
area: datasets
related:
- '[[2608.24988--does-fine-tuning-undo-activation-steering-behavioural]]'
- '[[embedded-activation-steering]]'
relationships:
- type: proposed_by
  target: '[[2608.24988--does-fine-tuning-undo-activation-steering-behavioural]]'
  target_id: paper:2608.24988
  confidence: high
- type: related_to
  target: '[[embedded-activation-steering]]'
  target_id: method:embedded-activation-steering
  confidence: medium
---

LongElicitPrompts contains 408 open-ended prompts designed to elicit long
responses. The paper uses paired prompts with and without a brevity instruction
to estimate and evaluate a brevity direction.

**Why it matters here:** It supplies a controlled behavioral target for testing
whether an embedded steering edit survives later training.

**Lineage:** The authors created it for the brevity-amplification experiments.
