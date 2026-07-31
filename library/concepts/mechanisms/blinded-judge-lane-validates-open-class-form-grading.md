---
aliases:
- judge-lane instrument clears calibration where the regex taxonomy failed
- blinded sharded opus-subagent judge validated for F1/F2/F3 grading
- promoted standing adjudication lane passes G1/G2 on the axis-G boundary
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:blinded-judge-lane-validates-open-class-form-grading
  type: mechanism
  status: canonical
cause: "The program's standing blinded sharded adjudication lane is promoted to primary instrument for the naming battery's open-class F1/F2/F3 form-gradedness boundary: a single context-free opus-tier subagent judge per shard, isolated from the model that produced the graded text, sees only the registered rubric and bare {opaque_id, text} pairs with mandatory per-row reading (scripted keyword classification forbidden); a second independent isolated opus-tier model agent serves as calibration adjudicator. It is run against freshly registered gates (G1 judge-vs-adjudicator disagreement on a 200-row calibration slice, G2 decoy agreement) after a first calibration attempt was ruled void pre-unblind for an empty-text decoy pool defect."
effect: "The instrument clears both registered floors on the repaired attempt-2 calibration slice (seed 20260801): G1 three-way judge-vs-adjudicator disagreement 7/200 = 0.035 against a 0.12 floor (dev-set judge-vs-judge point estimate 0.080 plus 0.04 headroom), direction breakdown F2-to-F1 6 / F1-to-F2 1; G2 clear-positive decoy agreement 25/25 = 1.00 against a 0.92 floor, as amended by a PI-approved governed deviation dropping the text-less clear-negative decoy source. A registered lead spot-check (n=30) is concordant with the rubric and a non-gating stability regrade shows 4/57 = 0.070 flips, all borderline F1/F2 hedges. Where the automated pattern-matched regex taxonomy for the same F1/F2/F3 boundary missed 79 of 86 disagreements one-sidedly against a 0.05 floor, the blinded model-judge lane clears its floor by more than 3x headroom, validating it as the axis-G instrument."
polarity: enables
related:
- '[[form-judge-axis-g-rescore]]'
- '[[abstention-wide-instrument-calibration]]'
- '[[form-taxonomy-pattern-battery-underdetects-epistemic-marking]]'
relationships:
- type: supported_by
  target: '[[form-judge-axis-g-rescore]]'
  target_id: experiment:form-judge-axis-g-rescore
  confidence: high
  evidence:
  - experiments/form-judge-axis-g-rescore/AMENDMENT.md#outcome (Instrument validation;
    calibration attempt 2, G1 PASS 0.035, G2 PASS 25/25, lead spot-check n=30 concordant)
- type: related_to
  target: '[[abstention-wide-instrument-calibration]]'
  target_id: experiment:abstention-wide-instrument-calibration
  confidence: medium
  evidence:
  - experiments/form-judge-axis-g-rescore/AMENDMENT.md (Motivation and posture;
    lineage abstention-wide-instrument-calibration, RR2, RR3, and the naming battery's
    own calibration slice)
- type: related_to
  target: '[[form-taxonomy-pattern-battery-underdetects-epistemic-marking]]'
  target_id: mechanism:form-taxonomy-pattern-battery-underdetects-epistemic-marking
  confidence: high
  evidence:
  - experiments/form-judge-axis-g-rescore/AMENDMENT.md (Motivation and posture;
    the judge lane replaces the pattern classifier this mechanism voided for the
    same F1/F2/F3 boundary, rather than repairing it)
---

The program's standing blinded model-judge grading protocol, already used
elsewhere for closed-class abstention detection, is promoted to primary
instrument for an open-class three-way boundary (committed / hedged /
non-answerable) that a purpose-built regex taxonomy had just failed to grade
reliably. Two isolated, context-free opus-tier model agents (a judge and a
separate calibration adjudicator, never a human grader) read every row's text
directly against a pinned rubric rather than matching patterns. The first
calibration attempt was voided pre-unblind by a registered lead spot-check
that caught an empty-text decoy pool defect; after a PI-approved governed
deviation and a fail-closed guard, the repaired instrument clears both
registered floors with wide headroom, in direct contrast to the regex
taxonomy's one-sided, order-of-magnitude miss on the same boundary.

**Why it matters here:** demonstrates that the program's open-class
form-gradedness question was measurable all along; the earlier instrument-void
outcome was a property of the pattern-matched classifier, not of the
underlying construct.
