---
aliases:
- decoding uncertainty
- U_dec
- sampling-induced uncertainty
tags:
- kg/term
- concept
- term
kg:
  id: term:decoding-randomness
  type: term
  status: canonical
area: terms
related:
- '[[2603.24967--uncertainty-source-decomposition]]'
- '[[uncertainty-source-decomposition]]'
- '[[input-ambiguity]]'
- '[[self-consistency]]'
- '[[consistency-based-confidence]]'
- '[[hallucination]]'
- '[[calibration]]'
relationships:
- type: proposed_by
  target: '[[2603.24967--uncertainty-source-decomposition]]'
  target_id: paper:2603.24967
  confidence: high
- type: related_to
  target: '[[uncertainty-source-decomposition]]'
  target_id: method:uncertainty-source-decomposition
  confidence: medium
- type: related_to
  target: '[[input-ambiguity]]'
  target_id: term:input-ambiguity
  confidence: medium
- type: related_to
  target: '[[self-consistency]]'
  target_id: method:self-consistency
  confidence: medium
- type: related_to
  target: '[[consistency-based-confidence]]'
  target_id: method:consistency-based-confidence
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

A component of LLM uncertainty arising from stochastic sampling during generation, measured as semantic disagreement across N repeated samples drawn from stochastic decoding strategies (temperature sampling, top-k, top-p). Deterministic decoding strategies (greedy, beam search) produce no variance and thus cannot express this component.

**Why it matters here:** For smaller models and certain tasks, decoding randomness is the dominant failure predictor, and the choice of stochastic versus deterministic decoding strategy substantially affects AUROC. This is a confound in any evaluation that fixes decoding strategy.

**Lineage:** Defined as U_dec in Taparia et al. 2026 (arXiv:2603.24967). Operationalizes sampling variance as an uncertainty source distinct from knowledge gaps or input ambiguity.
