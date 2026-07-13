---
aliases:
- three-component uncertainty decomposition
- LLM uncertainty anatomy
- U_input/U_know/U_dec framework
tags:
- kg/method
- concept
- method
kg:
  id: method:uncertainty-source-decomposition
  type: method
  status: canonical
area: methods
related:
- '[[2603.24967--uncertainty-source-decomposition]]'
- '[[lora-ensemble]]'
- '[[input-ambiguity]]'
- '[[decoding-randomness]]'
- '[[knowledge-gap]]'
- '[[consistency-based-confidence]]'
- '[[self-consistency]]'
- '[[hallucination]]'
- '[[calibration]]'
relationships:
- type: proposed_by
  target: '[[2603.24967--uncertainty-source-decomposition]]'
  target_id: paper:2603.24967
  confidence: high
- type: related_to
  target: '[[lora-ensemble]]'
  target_id: method:lora-ensemble
  confidence: medium
- type: related_to
  target: '[[input-ambiguity]]'
  target_id: term:input-ambiguity
  confidence: medium
- type: related_to
  target: '[[decoding-randomness]]'
  target_id: term:decoding-randomness
  confidence: medium
- type: related_to
  target: '[[knowledge-gap]]'
  target_id: term:knowledge-gap
  confidence: medium
- type: related_to
  target: '[[consistency-based-confidence]]'
  target_id: method:consistency-based-confidence
  confidence: medium
- type: related_to
  target: '[[self-consistency]]'
  target_id: method:self-consistency
  confidence: medium
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
  confidence: medium
- type: related_to
  target: '[[calibration]]'
  target_id: term:calibration
  confidence: medium
---

A diagnostic framework that decomposes LLM uncertainty into three semantic components measured independently: U_input (input ambiguity, estimated via disagreement across K semantically equivalent paraphrases), U_know (knowledge-gap uncertainty, estimated via ensemble disagreement across M independently trained LoRA adapters), and U_dec (decoding randomness, estimated via disagreement across N repeated samples under stochastic decoding). The components are not strictly orthogonal and their sum can exceed total uncertainty.

**Why it matters here:** Replaces single-score or aleatoric/epistemic uncertainty with a three-way decomposition that identifies which source dominates for a given model, dataset, and scale, enabling targeted interventions rather than undifferentiated uncertainty reduction. Applicable as a before/after measurement protocol around locked training-regimen arms.

**Lineage:** Proposed in Taparia et al. 2026 (arXiv:2603.24967). Builds on consistency-based-confidence and self-consistency for the sampling component; introduces the LoRA ensemble as the knowledge-gap measurement arm.
