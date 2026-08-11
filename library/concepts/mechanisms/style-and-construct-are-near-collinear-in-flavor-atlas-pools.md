---
title: style-and-construct-are-near-collinear-in-flavor-atlas-pools
aliases:
- surface style and overt-unanswerability construct are near-collinear
- flavor-atlas surface-control descriptive S2/C2 readout
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:style-and-construct-are-near-collinear-in-flavor-atlas-pools
  type: mechanism
  status: canonical
cause: "Fitting a probe on question-surface features alone (length, punctuation, digit profile, interrogative form, lexical n-grams) to predict KUQ/SelfAware flavor membership (S2), and separately residualizing the flavor-atlas-rawbase activation panels against 20 structurally meaningless permutations of the same combined surface-feature matrix (C2), on the same raw pretrained unsloth/Qwen3-4B base and pools as flavor-atlas-rawbase."
effect: "The surface-only probe (S2) alone reaches 0.9096-0.9863 AUROC predicting KUQ flavor membership (SelfAware 0.9523, AmbigQA 0.6597, pooled all-unknowns 0.9404), so question-surface style is itself a strong carrier of the flavor label in these pools. Residualizing against the 20 permuted (structurally meaningless) surface matrices collapses all six flavors' readouts about as much as residualizing against the true surface matrix does: 0 of 20 permuted runs kept every flavor at or above 0.90 AUROC, against a required 18/20 band (C2 FAIL). Together these show style and the overt-unanswerability construct are near-collinear in the KUQ/SelfAware pools by construction, so a cross-fitted residualization instrument on these pools cannot distinguish a style artifact from style being collinear with genuine overt-unanswerability structure; the observed post-residualization collapse reflects generic variance removal, not removal specific to true surface structure."
polarity: mediates
related:
- '[[flavor-atlas-surface-control-confirmatory]]'
- '[[flavor-atlas-rawbase]]'
- '[[pretrained-base-carries-broad-overt-unanswerability-code]]'
- '[[text-surface-form-predicts-boundary-elevation]]'
relationships:
- type: supported_by
  target: '[[flavor-atlas-surface-control-confirmatory]]'
  target_id: experiment:flavor-atlas-surface-control-confirmatory
  confidence: high
  evidence:
  - "AMENDMENT.md Outcome (S2 descriptive readout 0.9096-0.9863; SG5/C3
    FAIL, planted-channel deviation 0.077 vs 0.05 band; SG6/C2 FAIL, 0/20
    permuted runs vs an 18/20 band)"
- type: related_to
  target: '[[pretrained-base-carries-broad-overt-unanswerability-code]]'
  target_id: mechanism:pretrained-base-carries-broad-overt-unanswerability-code
  confidence: high
  evidence:
  - "AMENDMENT.md Outcome (this mechanism is the descriptive remainder of
    the INDETERMINATE confirmatory read of that mechanism's registered
    style-confound caveat; it does not confirm and does not resolve that
    caveat)"
- type: related_to
  target: '[[text-surface-form-predicts-boundary-elevation]]'
  target_id: mechanism:text-surface-form-predicts-boundary-elevation
  confidence: medium
  evidence:
  - "Cross-experiment structural parallel only: a different pool,
    checkpoint, and construct (confab-cloud knowledge boundary vs.
    flavor-atlas overt-unanswerability), but the same qualitative pattern
    of surface text form partially or fully carrying a linearly-read
    boundary or label"
---

`flavor-atlas-surface-control-confirmatory`'s descriptive, non-adjudicated
readout. A ridge probe fit on question-surface features alone (length,
punctuation, digit profile, interrogative form, lexical n-grams) predicts
KUQ/SelfAware flavor membership at 0.91-0.99 AUROC, and residualizing the
raw-base activations against 20 structurally meaningless permutations of
the same surface matrix collapses all six flavors' readouts about as much
as residualizing against the true surface matrix does. Together these show
style and the overt-unanswerability construct are near-collinear in the
KUQ/SelfAware pools by construction, so a cross-fitted residualization
instrument on these pools cannot separate a style artifact from style
being collinear with genuine overt-unanswerability structure.

**Why it matters here:** this is the descriptive remainder of an
INDETERMINATE confirmatory test of
[[pretrained-base-carries-broad-overt-unanswerability-code]]'s registered
style-confound caveat. Per the collapse-asymmetry rule, the failed
negative control (C2) and failed planted-channel control (C3) mean the
instrument's own collapse is uninterpretable: it licenses "not adjudicable
with this instrument on these pools", never "the atlas separation is
style" and never "the raw base has no unanswerability code". Promotion of
the flavor-atlas overt-unanswerability separation to a claim stays blocked
either way.

**Registered caveat (travels with this claim):** the planted-channel
control (C3) verifies only that the surface model can reach and remove a
linear plant within its own span; it does not test removal of a nonlinear
style encoding. The registered next routes are a fresh surface-matched
pool that breaks the style/construct confound at construction, or causal
actuation on the trained lineage, which does not inherit this readout
confound.

**Lineage:** descriptive readout from
[[flavor-atlas-surface-control-confirmatory]], the confirmatory follow-on
to [[flavor-atlas-rawbase]] registered to test
[[pretrained-base-carries-broad-overt-unanswerability-code]]'s
style-confound caveat. Source of truth:
`experiments/flavor-atlas-surface-control-confirmatory/AMENDMENT.md`,
Outcome section.
