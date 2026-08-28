---
aliases:
- Weight steering preserves reasoning and final-answer consistency better than activation steering
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:weight-steering-preserves-reasoning-answer-consistency-better-than-activation-steering
  type: mechanism
  status: canonical
cause: "Contrastive weight steering edits the model parameters for evil multiple-choice behavior instead of adding a single-layer activation direction at inference."
effect: "Chain-of-thought reasoning and final answers remain more mutually consistent than under the tested activation-steering intervention."
polarity: decreases
related:
- '[[2511.05408--steering-language-models-weight-arithmetic]]'
- '[[contrastive-weight-steering]]'
- '[[activation-steering]]'
- '[[world-affecting]]'
relationships:
- type: supported_by
  target: '[[2511.05408--steering-language-models-weight-arithmetic]]'
  target_id: paper:2511.05408
  confidence: high
- type: related_to
  target: '[[contrastive-weight-steering]]'
  target_id: method:contrastive-weight-steering
  confidence: high
- type: related_to
  target: '[[activation-steering]]'
  target_id: method:activation-steering
  confidence: high
- type: related_to
  target: '[[world-affecting]]'
  target_id: dataset:world-affecting
  confidence: high
---

Figure 5 reports that weight steering changes evil multiple-choice answers more consistently with the preceding chain-of-thought, while activation steering raises the inconsistent-answer rate relative to the base model. This result is limited to the paper's controlled evil-MCQA setup and judge-based consistency evaluation.
