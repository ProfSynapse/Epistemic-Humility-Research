---
aliases:
- One shared doubt axis across unanswerability flavors
- cross-flavor transfer of the known/unknown detector
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:unanswerability-detection-shares-one-axis-across-flavors
  type: mechanism
  status: canonical
cause: "Training a linear known/unknown detector on questions of a single unanswerability flavor and evaluating it on every other flavor (L20/24/28, raw instruct base, pre-generation anchor)."
effect: "Detection transfers within about one point of home performance (off-diagonal AUROC 0.988 vs diagonal 0.998): for the basic answerable/unanswerable judgment there is one shared axis, not a per-flavor detector."
polarity: enables
related:
- '[[internal-flavor-geometry--category-fleet]]'
- '[[flavor-specific-doubt-residuals-persist]]'
- '[[known-unknown-direction]]'
- '[[answerability-probe-transfers-across-qa-datasets]]'
- '[[answerability-axis-present-without-task-training]]'
- '[[known-unknowns-taxonomy]]'
relationships:
- type: supported_by
  target: '[[internal-flavor-geometry--category-fleet]]'
  target_id: paper:internal-flavor-geometry
  confidence: high
- type: related_to
  target: '[[flavor-specific-doubt-residuals-persist]]'
  target_id: mechanism:flavor-specific-doubt-residuals-persist
  confidence: high
- type: related_to
  target: '[[known-unknown-direction]]'
  target_id: term:known-unknown-direction
  confidence: high
- type: related_to
  target: '[[answerability-probe-transfers-across-qa-datasets]]'
  target_id: mechanism:answerability-probe-transfers-across-qa-datasets
  confidence: high
- type: related_to
  target: '[[answerability-axis-present-without-task-training]]'
  target_id: mechanism:answerability-axis-present-without-task-training
  confidence: high
- type: related_to
  target: '[[known-unknowns-taxonomy]]'
  target_id: term:known-unknowns-taxonomy
  confidence: high
---

Session-0036 category-geometry arm. The flavor-to-flavor transfer matrix for a
linear known/unknown detector is nearly flat: every off-diagonal cell sits within
about one point of the diagonal. This is the within-model, within-dataset analogue
of the cross-dataset transfer result (KUQ to SelfAware at 0.983) and strengthens the
one-gate reading of the two-signal mechanism: the validated answerability gate is
genuinely one gate, not six flavor-specific gates that happen to co-fire. The
per-flavor structure that does exist lives in the residuals, not in the detection
axis itself.
