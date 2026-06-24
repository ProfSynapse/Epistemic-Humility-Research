---
aliases:
- ERFT
- extended refusal fine-tuning
- extended-refusal dataset fine-tuning
tags:
- kg/method
- concept
- method
kg:
  id: method:extended-refusal-fine-tuning
  type: method
  status: canonical
area: methods
related:
- '[[2505.19056--abliteration-defense-dose-response]]'
- '[[weight-orthogonalization]]'
- '[[supervised-finetuning]]'
- '[[refusal-direction]]'
- '[[safety-refusal]]'
- '[[refusal-direction-mediates-refusal]]'
relationships:
- type: proposed_by
  target: '[[2505.19056--abliteration-defense-dose-response]]'
  target_id: paper:2505.19056
  confidence: high
- type: related_to
  target: '[[weight-orthogonalization]]'
  target_id: method:weight-orthogonalization
  confidence: medium
- type: related_to
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
  confidence: medium
- type: related_to
  target: '[[refusal-direction]]'
  target_id: term:refusal-direction
  confidence: medium
- type: related_to
  target: '[[safety-refusal]]'
  target_id: term:safety-refusal
  confidence: medium
- type: related_to
  target: '[[refusal-direction-mediates-refusal]]'
  target_id: mechanism:refusal-direction-mediates-refusal
  confidence: medium
---

A supervised fine-tuning method that trains models to respond to harmful prompts with semantically rich three-part refusals (neutral topic overview, explicit refusal, ethical rationale) instead of brief formulaic refusals, with the goal of distributing the refusal signal across multiple latent dimensions so that single-direction weight-surgery attacks cannot collapse it.

**Why it matters here:** Demonstrates that output form (not just training objective) determines whether a safety behavior is concentrated in a single removable direction or spread across the representation space; the principle extends to any behavior that could be targeted by activation-editing.

**Lineage:** Proposed by Abu Shairah et al. (2505.19056) as a practical defense against Arditi et al.'s abliteration attack (2406.11717).
