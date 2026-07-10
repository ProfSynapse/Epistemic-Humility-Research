---
aliases:
- I-don't-know supervised fine-tuning
- Idk supervised finetuning
- Idk-SFT
tags:
- kg/method
- concept
- method
kg:
  id: method:idk-sft
  type: method
  status: canonical
area: methods
related:
- '[[2401.13275--can-ai-assistants-know-what-they-dont-know]]'
- '[[supervised-finetuning]]'
- '[[idk-dataset]]'
- '[[knowledge-quadrant-metric]]'
relationships:
- type: proposed_by
  target: '[[2401.13275--can-ai-assistants-know-what-they-dont-know]]'
  target_id: paper:2401.13275
  confidence: high
- type: derived_from
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
- type: related_to
  target: '[[idk-dataset]]'
  target_id: dataset:idk-dataset
- type: related_to
  target: '[[knowledge-quadrant-metric]]'
  target_id: metric:knowledge-quadrant-metric
---

Idk-SFT is supervised fine-tuning of a language model directly on the
model-specific [[idk-dataset]], training it to produce refusal responses for
questions below the [[ik-threshold]] and correct answers for questions above it.
It is the simplest alignment baseline in the Cheng et al. framework and requires
no preference pairs or reward signal beyond the binary known/unknown label.

**Why it matters here:** Idk-SFT is the SFT arm in the Cheng et al. ablation and
the closest analogue to the SFT baseline in the locked training-regimen SFT-vs-DPO-vs-KTO
abstention study; comparing it against preference-optimization variants
(DPO-style and RL-based) isolates the marginal value of learning from
contrastive or reward-weighted signals.

**Lineage:** derives from [[supervised-finetuning]]; proposed in
[[2401.13275--can-ai-assistants-know-what-they-dont-know]].
