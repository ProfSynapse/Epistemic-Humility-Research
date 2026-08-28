---
aliases:
- Activation consistency reduces sycophancy by aligning prompt states
- Clean-state alignment suppresses prompt-cue influence
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:activation-consistency-reduces-sycophancy-by-aligning-prompt-states
  type: mechanism
  status: canonical
cause: "Residual-stream states for clean and cue-wrapped versions of a prompt are patched or trained toward equality across shared prompt positions."
effect: "The wrapped cue has less influence on the model's multiple-choice answer, reducing measured sycophancy."
polarity: prevents
related:
- '[[2510.27062--consistency-training-helps-stop-sycophancy-jailbreaks]]'
- '[[activation-consistency-training]]'
- '[[sycophancy]]'
relationships:
- type: supported_by
  target: '[[2510.27062--consistency-training-helps-stop-sycophancy-jailbreaks]]'
  target_id: paper:2510.27062
  confidence: high
- type: related_to
  target: '[[activation-consistency-training]]'
  target_id: method:activation-consistency-training
  confidence: high
- type: related_to
  target: '[[sycophancy]]'
  target_id: term:sycophancy
  confidence: high
---

All-layer activation patching gives the strongest direct intervention, and ACT provides the trained analogue. The experiments show reduced cue sensitivity but do not identify a single localized sycophancy circuit.
