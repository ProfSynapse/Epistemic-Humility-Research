---
aliases:
- Probe Calibration Enables Accurate Adaptive Computation
- calibrated probe enables early stopping
- probe-guided early exit
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:probe-calibration-enables-early-exit
  type: mechanism
  status: canonical
cause: "A well-calibrated [[attention-probing|attention probe]] whose confidence closely tracks forced-answer accuracy step-by-step throughout the reasoning trace"
effect: "Ability to halt token generation early once the probe crosses a confidence threshold, with minimal accuracy loss relative to full-length generation"
polarity: enables
related:
- '[[2603.05488--reasoning-theater-disentangling-model-beliefs-chain-thought]]'
- '[[attention-probing]]'
- '[[probe-guided-early-exit]]'
- '[[chain-of-thought-faithfulness]]'
- '[[high-confidence-suppresses-inflections]]'
relationships:
- type: supported_by
  target: '[[2603.05488--reasoning-theater-disentangling-model-beliefs-chain-thought]]'
  target_id: paper:2603.05488
  confidence: high
- type: related_to
  target: '[[attention-probing]]'
  target_id: method:attention-probing
- type: related_to
  target: '[[probe-guided-early-exit]]'
  target_id: method:probe-guided-early-exit
- type: related_to
  target: '[[chain-of-thought-faithfulness]]'
  target_id: term:chain-of-thought-faithfulness
- type: related_to
  target: '[[high-confidence-suppresses-inflections]]'
  target_id: mechanism:high-confidence-suppresses-inflections
---

arXiv:2603.05488 trains attention-head probes to predict the final answer at intermediate reasoning steps and shows the probes reach forced-answer accuracy well before the reasoning trace ends on performative examples. Because probe confidence converges early and tracks accuracy, a simple threshold rule can trigger early exit with negligible accuracy degradation, yielding significant inference savings. This mechanism depends on probe calibration: an overconfident or poorly calibrated probe would trigger early exit on genuinely hard steps where continued reasoning still matters.
