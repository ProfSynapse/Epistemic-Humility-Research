---
aliases:
- checkpoint-level representation tracing
- training-trajectory analysis
tags:
- kg/method
- concept
- method
kg:
  id: method:pretraining-checkpoint-tracing
  type: method
  status: canonical
area: training-dynamics
related:
- '[[2605.13329--tracing-persona-vectors-through-llm-pretraining]]'
- '[[difference-of-means-persona-extraction]]'
relationships:
- type: proposed_by
  target: '[[2605.13329--tracing-persona-vectors-through-llm-pretraining]]'
  target_id: paper:2605.13329
  confidence: high
- type: derived_from
  target: '[[difference-of-means-persona-extraction]]'
  target_id: method:difference-of-means-persona-extraction
---

Pretraining Checkpoint Tracing samples multiple checkpoints across the pretraining timeline (denser early, sparser later), extracts linear representations from each via contrastive mean-difference probes, and compares those representations for geometric evolution, emergence timing, and cross-checkpoint transfer. Applied to persona vectors in the originating work, it establishes when a given representation first appears and how its geometry refines as training data accumulates.

**Why it matters here:** Determining whether epistemic representations such as known-unknown directions or abstention geometry emerge early or late in pretraining distinguishes whether alignment training creates those axes or merely reshapes pre-existing structure.

**Lineage:** extends [[difference-of-means-persona-extraction]]; introduced in [[2605.13329--tracing-persona-vectors-through-llm-pretraining]].
