---
aliases:
- correctness-direction identifiability sharpens with scale, conditional on layer choice
- scale-conditional crystallization of the correctness direction (M3)
- layer choice mediates whether correctness geometry sharpens with scale
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:correctness-identifiability-sharpens-with-scale-under-adaptive-layer-choice
  type: mechanism
  status: canonical
cause: "On the identical-pool Amendment-X raw-instruct-base ladder (Qwen3 1.7B/8B/14B, matched-n N*=377/377 correct/wrong), correctness-direction identifiability (the crystallization index c, E1 split-half k=1 reliability, full-n primary) is measured at two different layer choices per scale: the scale-adaptive best-dial layer (the per-scale layer with highest correct-vs-wrong AUROC: 1.7B L21, 8B L20, 14B L28) versus a fixed relative depth (~0.6 of each scale's layer count: 1.7B L17, 8B L22, 14B L24)."
effect: "Under the scale-adaptive best-dial layer choice, c rises monotonically with scale (-0.062 -> +0.086 -> +0.240, Delta_c 0.302, clearing the frozen-band trend threshold under both sigma readings, z=1.645 one-sided, seed-stable within 0.008). Under the fixed relative-depth layer choice, c does not rise monotonically (+0.033 -> +0.129 -> +0.075, dipping at 14B). Because correctness-geometry-scale-ladder's registered gate required the rise under BOTH layer choices, the disagreement resolves as the pre-stated middle ground M3 rather than a clean PASS: correctness-direction identifiability sharpening with scale is real at the scale-adaptive layer but not established as a scale-intrinsic property independent of layer choice. A window-scan robustness check found the trend is layer-robust in a broader sense (every 8B-window layer's c exceeds every 1.7B-window layer's c), and a selection-provenance check found the best-dial layers are not cherry-picked for direction reliability (at 1.7B/8B they sit among the LOWEST-c layers of their own window), so the layer-choice dependence is not an artifact of either check, only of the REQUIRE-BOTH conjunction itself."
polarity: mediates
related:
- '[[correctness-geometry-scale-ladder]]'
- '[[correctness-direction-weakly-identified-defeats-cosine-rotation-probe]]'
- '[[l2-logistic-bootstrap-svd-cannot-resolve-multidim-discriminative-subspace]]'
- '[[epistemic-readouts-are-late-compression-summaries]]'
relationships:
- type: supported_by
  target: '[[correctness-geometry-scale-ladder]]'
  target_id: experiment:correctness-geometry-scale-ladder
  confidence: medium
  evidence:
  - experiments/correctness-geometry-scale-ladder/AMENDMENT.md#outcome (G1 resolution
    on the real run)
- type: related_to
  target: '[[correctness-direction-weakly-identified-defeats-cosine-rotation-probe]]'
  target_id: mechanism:correctness-direction-weakly-identified-defeats-cosine-rotation-probe
  confidence: high
  evidence:
  - experiments/correctness-geometry-scale-ladder/AMENDMENT.md (Motivation and
    posture; this cell was built to test whether that mechanism's weak
    identifiability at Qwen3-4B is a small-model artifact)
- type: related_to
  target: '[[l2-logistic-bootstrap-svd-cannot-resolve-multidim-discriminative-subspace]]'
  target_id: mechanism:l2-logistic-bootstrap-svd-cannot-resolve-multidim-discriminative-subspace
  confidence: medium
  evidence:
  - experiments/correctness-geometry-scale-ladder/AMENDMENT.md (Estimators,
    "FORBIDDEN" clause; the ladder's own primary estimator (E1, k=1 split-half
    reliability) was chosen specifically to avoid this mechanism's k>1
    subspace-reliability limit)
- type: related_to
  target: '[[epistemic-readouts-are-late-compression-summaries]]'
  target_id: mechanism:epistemic-readouts-are-late-compression-summaries
  confidence: low
  status: proposed
  note: "Conjectural link only, not asserted by either source doc: the scale axis
    this mechanism measures (identifiability vs. model size, at a correctness
    dial) and the depth axis that hypothesis measures (readability vs. layer
    depth, at a family-atlas read panel) are different instruments studying
    different signals; no resolved gate connects them."
---

`correctness-geometry-scale-ladder` set out to test whether the correctness
direction's weak identifiability at Qwen3-4B
([[correctness-direction-weakly-identified-defeats-cosine-rotation-probe]]:
stable AUROC, unstable split-half direction) is a small-model artifact that
crystallizes with scale. The answer the resolved cell supports is
conditional rather than clean: identifiability does sharpen monotonically
from 1.7B to 14B, but only when the layer read at each scale is chosen
adaptively (the layer with the best correct-vs-wrong readout at that scale),
not when a single fixed relative depth is read at every scale. Both
registered layer choices were required to show the rise before the cell
would call the hypothesis confirmed; because they disagree, the cell
resolved as the pre-stated middle ground M3, not a PASS.

**Why it matters here:** it means "does correctness geometry crystallize
with scale" does not have a single scale-intrinsic answer independent of how
the reading layer is chosen. A future amendment that wants to use a
sharpening account of correctness identifiability (for example, to justify
re-opening CD or SO's rotation/subspace questions at larger scale with a
better instrument) needs to specify a scale-adaptive layer-selection
procedure as part of the claim, not assume a ported fixed depth will show
the same effect. The mechanism this cell excluded by construction,
[[l2-logistic-bootstrap-svd-cannot-resolve-multidim-discriminative-subspace]],
is why the ladder's primary estimator stays at k=1 rather than attempting a
higher-rank identifiability read that SO already showed is instrumentally
unreachable.

**Speculative link, not asserted by either source.** Both
`correctness-geometry-scale-ladder` and the family-atlas line's
[[epistemic-readouts-are-late-compression-summaries]] hypothesis describe an
epistemic signal's identifiability or readability depending on where, rather
than whether, it is measured (layer choice here; depth relative to an
early dimensionality peak there). The two studies use different instruments
on different signals (a correctness dial across model scale versus a
known-unknown/caution/raw-refusal read panel across layer depth within one
model), and no resolved gate in either line connects them; any relationship
between "the right layer depends on scale" and "the right layer depends on
which side of a compression peak you read" is this note's own speculative
juxtaposition, not a finding either experiment reports.

Source of truth: `experiments/correctness-geometry-scale-ladder/AMENDMENT.md`,
"G1 resolution on the real run" (end of the Outcome section), resolved
2026-07-20.
