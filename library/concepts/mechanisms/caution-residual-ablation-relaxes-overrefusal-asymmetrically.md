---
aliases:
- Caution-residual ablation relaxes over-refusal asymmetrically
- Caution is relaxable but not installable by steering
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:caution-residual-ablation-relaxes-overrefusal-asymmetrically
  type: mechanism
  status: canonical
cause: "Ablating the caution residual direction (activation steering at inference) in a small instruction-tuned model that over-refuses known questions."
effect: "Over-refusal on known questions drops from 0.994 to 0.030 with clean specificity, but no steering intervention installs abstention on genuine unknowns - caution is causally relaxable but not installable, an asymmetry specific to the abstention behavior."
polarity: decreases
related:
- '[[internal-paper3--knows-but-doesnt-say]]'
- '[[answerability-subspace-erasure-degrades-answerability-behavior]]'
- '[[entity-recognition-direction-gates-refusal-vs-hallucination]]'
- '[[refusal-direction]]'
- '[[residual-stream]]'
relationships:
- type: supported_by
  target: '[[internal-paper3--knows-but-doesnt-say]]'
  target_id: paper:internal-paper3
  confidence: high
- type: related_to
  target: '[[answerability-subspace-erasure-degrades-answerability-behavior]]'
  target_id: mechanism:answerability-subspace-erasure-degrades-answerability-behavior
  confidence: medium
- type: related_to
  target: '[[entity-recognition-direction-gates-refusal-vs-hallucination]]'
  target_id: mechanism:entity-recognition-direction-gates-refusal-vs-hallucination
  confidence: medium
- type: related_to
  target: '[[refusal-direction]]'
  target_id: term:refusal-direction
  confidence: high
- type: related_to
  target: '[[residual-stream]]'
  target_id: term:residual-stream
  confidence: medium
---

Paper 3 Result 3 uses activation steering as a causal probe of the doubt/caution
decomposition. Ablating the caution residual cuts over-refusal on known questions
0.994 to 0.030 with clean specificity (correct-on-known preserved), but no
intervention tried induces appropriate abstention on true unknowns. The control is
asymmetric: excess caution can be relaxed, missing caution cannot be installed by
steering. This mirrors the behavioral asymmetry that motivates reading (not steering)
the internal axes as the deployment route.
