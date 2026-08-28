---
aliases:
- Condition vectors gate behavior steering by input context
- Hidden-state condition sensing enables selective refusal
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:condition-vectors-gate-behavior-steering-by-input-context
  type: mechanism
  status: canonical
cause: "A hidden-state similarity test against a condition vector determines whether a refusal behavior vector is added during inference."
effect: "Refusal increases for prompts matching the condition while behavior on nonmatching prompts is largely preserved."
polarity: enables
related:
- '[[2409.05907--programming-refusal-conditional-activation-steering]]'
- '[[conditional-activation-steering]]'
- '[[condition-vector]]'
- '[[refusal-direction]]'
relationships:
- type: supported_by
  target: '[[2409.05907--programming-refusal-conditional-activation-steering]]'
  target_id: paper:2409.05907
  confidence: high
- type: related_to
  target: '[[conditional-activation-steering]]'
  target_id: method:conditional-activation-steering
  confidence: high
- type: related_to
  target: '[[condition-vector]]'
  target_id: term:condition-vector
  confidence: high
- type: related_to
  target: '[[refusal-direction]]'
  target_id: term:refusal-direction
  confidence: high
---

Across the tested models, CAST raised harmful refusal while producing much smaller changes in harmless refusal. Standard unconditional steering increased refusal across both classes.
