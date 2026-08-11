---
title: flavor-atlas-surface-control-confirmatory
aliases:
- Style-controlled confirmatory read of the flavor-atlas overt-unanswerability separation
- flavor-atlas surface control
tags:
- kg/experiment
- experiment
- epistemic-humility
kg:
  id: experiment:flavor-atlas-surface-control-confirmatory
  type: experiment
  status: canonical
related:
- '[[flavor-atlas-rawbase]]'
- '[[pretrained-base-carries-broad-overt-unanswerability-code]]'
- '[[overt-vs-covert-unanswerability-is-the-boundary-not-flavor]]'
- '[[known-unknown-questions]]'
- '[[selfaware]]'
- '[[style-and-construct-are-near-collinear-in-flavor-atlas-pools]]'
relationships:
- type: builds_on
  target: '[[flavor-atlas-rawbase]]'
  target_id: experiment:flavor-atlas-rawbase
  confidence: high
  evidence:
  - "AMENDMENT.md Motivation and posture (confirmatory follow-on registered
    to close flavor-atlas-rawbase's own registered style-confound caveat;
    reuses flavor-atlas-rawbase's KUQ/SelfAware activation captures and
    panels byte-identically, no new extraction)"
- type: tests
  target: '[[pretrained-base-carries-broad-overt-unanswerability-code]]'
  target_id: mechanism:pretrained-base-carries-broad-overt-unanswerability-code
  confidence: high
  evidence:
  - "AMENDMENT.md Outcome (that mechanism's registered caveat named a
    style-controlled confirmatory cell, not yet registered, as the
    required next step before promotion to a claim; this cell is that
    test)"
- type: related_to
  target: '[[overt-vs-covert-unanswerability-is-the-boundary-not-flavor]]'
  target_id: mechanism:overt-vs-covert-unanswerability-is-the-boundary-not-flavor
  confidence: medium
  evidence:
  - "AMENDMENT.md Design (same six KUQ flavor plus SelfAware/AmbigQA
    reference pools as the companion atlas finding)"
- type: evaluates_on
  target: '[[known-unknown-questions]]'
  target_id: dataset:known-unknown-questions
  confidence: high
  evidence:
  - "experiment.yaml inputs (reuses flavor-atlas-rawbase's KUQ panel
    byte-identically, no new extraction)"
- type: evaluates_on
  target: '[[selfaware]]'
  target_id: dataset:selfaware
  confidence: high
  evidence:
  - "experiment.yaml inputs (reuses flavor-atlas-rawbase's SelfAware panel
    byte-identically)"
- type: supports
  target: '[[style-and-construct-are-near-collinear-in-flavor-atlas-pools]]'
  target_id: mechanism:style-and-construct-are-near-collinear-in-flavor-atlas-pools
  confidence: high
  evidence:
  - "AMENDMENT.md Outcome (S2 surface-only descriptive readout 0.9096-0.9863
    across the six KUQ flavors; SG5/C3 FAIL; SG6/C2 FAIL 0/20 vs an 18/20
    band)"
---

Tier-3 exploratory confirmatory probe-fit cell (resolved 2026-08-11),
registered as the direct follow-on to close `flavor-atlas-rawbase`'s own
registered style confound. Analysis-only reread of that cell's existing
KUQ, SelfAware, and AmbigQA activation captures on the raw pretrained
`unsloth/Qwen3-4B` base (no new extraction, no GPU verb): fits a
cross-fitted ridge model per layer to residualize the activation panels
against a combined prompt-surface feature block (length, punctuation,
digit profile, interrogative form, lexical n-grams), then re-reads the
same registered known/unknown probe protocol on the residuals. Three
controls gate SG8 adjudication: C1 (treatment strength: the surface
model must explain real, above-permutation activation variance), C2
(permutation negative control: residualizing against 20 structurally
meaningless surface matrices should not collapse the readouts the way
the true surface matrix does), and C3 (planted-channel control: a
synthetic surface-correlated signal must be reachable and removable by
the same instrument).

**Result, INDETERMINATE as registered.** C1 passed decisively (combined
surface block explains real above-permutation activation variance at
every primary layer). C2 and C3 both failed: 0 of 20 permuted-surface
residualized runs kept all six KUQ flavors at or above 0.90 AUROC
(band requires 18/20), and the planted-channel control's own
residualization moved the unplanted flavors' readouts by up to 0.077
against a 0.05 band. Because C2/C3 failed, SG8 refused adjudication of
P1-P3/F1-F2 as registered; none of the prediction or falsifier bands
were evaluated. Per the signed collapse-asymmetry rule, this outcome
licenses only "not adjudicable with this instrument on these pools" -
it does not license "the flavor-atlas separation is a style artifact"
and it does not license "the raw base has no unanswerability code".
Descriptive-only readout (S2): a probe fit on question-surface features
alone predicts KUQ/SelfAware flavor membership at 0.91-0.99 AUROC,
showing style and the overt-unanswerability construct are near-collinear
in these pools by construction (see
[[style-and-construct-are-near-collinear-in-flavor-atlas-pools]]).

Atlas promotion to a claim stays blocked; `flavor-atlas-rawbase` is not
falsified. Registered next routes: a fresh surface-matched pool that
breaks the style/construct confound at construction, or causal
actuation on the trained lineage, which does not inherit this readout
confound.

**Lineage:** confirmatory follow-on to [[flavor-atlas-rawbase]],
registered to test [[pretrained-base-carries-broad-overt-unanswerability-code]]'s
style-confound caveat. Source of truth:
`experiments/flavor-atlas-surface-control-confirmatory/AMENDMENT.md`
(Outcome section), `experiment.yaml` (`verdict:`), and
`analysis-committed/surface_control.json`.
