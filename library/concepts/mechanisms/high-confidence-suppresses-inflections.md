---
aliases:
- High Internal Confidence Suppresses Reasoning Inflection Points
- high confidence suppresses backtracking
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:high-confidence-suppresses-inflections
  type: mechanism
  status: canonical
cause: "High internal [[linear-probe|probe]] confidence at early reasoning steps (model already committed to a final answer)"
effect: "Rate of inflection points (backtracking, reconsiderations, 'aha' moments) per reasoning step in the generated chain-of-thought"
polarity: decreases
related:
- '[[2603.05488--reasoning-theater-disentangling-model-beliefs-chain-thought]]'
- '[[linear-probe]]'
- '[[attention-probing]]'
- '[[chain-of-thought-faithfulness]]'
- '[[probe-calibration-enables-early-exit]]'
relationships:
- type: supported_by
  target: '[[2603.05488--reasoning-theater-disentangling-model-beliefs-chain-thought]]'
  target_id: paper:2603.05488
  confidence: high
- type: related_to
  target: '[[linear-probe]]'
  target_id: method:linear-probe
- type: related_to
  target: '[[attention-probing]]'
  target_id: method:attention-probing
- type: related_to
  target: '[[chain-of-thought-faithfulness]]'
  target_id: term:chain-of-thought-faithfulness
- type: related_to
  target: '[[probe-calibration-enables-early-exit]]'
  target_id: mechanism:probe-calibration-enables-early-exit
---

arXiv:2603.05488 measures attention-head probe confidence at each step of the reasoning trace and finds that when confidence is already high at step t, the model rarely introduces backtracking tokens or shifts the reasoning direction at t+1. This makes inflection points a reliable proxy for whether the CoT is doing genuine deliberation versus merely elaborating a predetermined answer. The suppression of inflections by high probe confidence provides a mechanistic account of why performative CoT looks superficially like reasoning yet contains no decision-changing moments.
