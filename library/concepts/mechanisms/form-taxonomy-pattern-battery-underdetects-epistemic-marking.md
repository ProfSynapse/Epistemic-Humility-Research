---
aliases:
- Arm A form taxonomy fails blinded calibration
- pattern battery misses hedged and non-answerability marking
- instrument-void row fires on axis G
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:form-taxonomy-pattern-battery-underdetects-epistemic-marking
  type: mechanism
  status: canonical
cause: "write-direction-naming-battery's Arm A output-form taxonomy (form_taxonomy.py, a pattern-matched five-class F1-F5 classifier distinguishing committed assertions from hedged assertions, non-answerability assertions, explicit IDK, and degenerate output) is graded against a registered blinded adjudication slice, n=200 rows stratified across arms and doses, pool hash committed before grading and graded hash committed before unblind, against a pre-registered core disagreement ceiling of 0.05 on the F1/F2/F3 boundary."
effect: "Core disagreement lands at 86/200 = 0.43, about 8.6x the registered floor, and the mismatch is one-sided: 79 of the 86 disagreements are rows the automated pattern battery scores F1 (committed assertion, no epistemic marking) that the blinded isolated adjudicator (a context-free model agent serving as human-proxy judge) scores F2 (hedged assertion) or F3 (non-answerability assertion). Clear-positive decoy agreement passes cleanly, 19/19 = 1.00 over 19 decoys (a user-approved governed deviation from the registered 25-decoy minimum, since the placebo arms produced only 19 such rows), so the detector is not broken in general, it specifically under-detects epistemic marking. Per the cell's registered instrument-void rule this failed calibration voids axis G (form gradedness): Arms A and D are instrument-void, no Arm A form distribution is citable, and the naming battery's eight-row outcome-to-name table cannot be assembled from this cell regardless of what axes B and K resolve."
polarity: prevents
related:
- '[[write-direction-naming-battery]]'
- '[[known-unknowns-taxonomy]]'
relationships:
- type: supported_by
  target: '[[write-direction-naming-battery]]'
  target_id: experiment:write-direction-naming-battery
  confidence: high
  evidence:
  - experiments/write-direction-naming-battery/AMENDMENT.md#outcome (instrument-void row; core disagreement 86/200 = 0.43, decoy agreement 19/19 = 1.00)
- type: related_to
  target: '[[known-unknowns-taxonomy]]'
  target_id: term:known-unknowns-taxonomy
  confidence: low
---

A new five-class output-form taxonomy (F1 committed assertion through F5
degenerate, with F2 hedged assertion and F3 non-answerability assertion as the
two genuinely new classes) was built to answer whether the mid-band c_hat
write's intermediate-dose behavior is epistemically graded or merely degraded.
The taxonomy's own registered blinded-calibration gate is what fails, not the
underlying question: a seeded, stratified, pool-hash-committed 200-row slice
disagrees with the automated classifier on the F1/F2/F3 boundary at 0.43
against a 0.05 ceiling, and the disagreement direction is consistent rather
than noisy, the pattern battery reads hedged and non-answerability language as
plain committed assertions in 79 of 86 mismatches.

Because the calibration gate is registered as a stop condition (not an
outcome), this closes axis G of the naming battery's outcome table as
instrument-void rather than as a BINARY finding; no inference about whether
the write's intermediate-dose output is graded or merely degraded can be drawn
from the automated F1-F5 counts as built. A wider-recall taxonomy is a new
instrument for a future registration, not a fix applied post hoc to this cell.
