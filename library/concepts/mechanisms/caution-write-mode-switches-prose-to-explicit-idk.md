---
aliases:
- axis G resolves BINARY under the validated judge instrument
- dose converts all prose forms into explicit IDK with no graded intermediate
- baseline hedged share 0.431, an order of magnitude above the voided regex reading
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:caution-write-mode-switches-prose-to-explicit-idk
  type: mechanism
  status: canonical
cause: "Dosing along the frozen mid-band hs20 c_hat write direction across the naming battery's 7 Arm A sub-arms (baseline, three intermediate doses, 1.0x, two placebo doses) is graded on the open-class F1/F2/F3 form-gradedness boundary by the validated blinded judge-lane instrument (mechanism:blinded-judge-lane-validates-open-class-form-grading), replacing the voided regex form taxonomy for the same boundary, over all 1781 non-spent screened-in rows."
effect: "The judge finds the baseline model already hedges 0.431 of its non-degenerate prose answers (F2+F3 share), roughly an order of magnitude above what the voided regex taxonomy detected, and the placebo sub-arms sit at the same level (0.427, 0.406), so the elevated baseline hedging is a property of the model's undosed prose, not an artifact of dosing. The F2+F3 share falls MONOTONICALLY with dose across the intermediate doses (0.322 at 0.25x, 0.233 at 0.5x, 0.156 at 0.75x, 0.104 at 1.0x) while explicit IDK (the deterministic F4 screen) rises monotonically over the same ladder (16 to 267 of 400 rows). Against the naming battery's original axis-G thresholds (0.15 intermediate-dose share AND +0.10 over baseline), the 0.15 floor clears at all three intermediate doses but the +0.10-over-baseline leg fails at every dose because dosing moves the hedged share DOWN, not up. Axis G resolves BINARY: the caution write does not produce a graded epistemic-marking response to dose; it converts prose output of any kind, committed or already hedged, wholesale into explicit IDK, a mode switch with no graded intermediate."
polarity: enables
related:
- '[[form-judge-axis-g-rescore]]'
- '[[form-taxonomy-pattern-battery-underdetects-epistemic-marking]]'
- '[[midband-write-corrupts-known-answers-more-than-it-produces-abstention]]'
- '[[write-direction-naming-battery]]'
- '[[caution-write-idk-jump-replicates-under-fresh-sampled-decode-seeds]]'
- '[[idk-switch]]'
relationships:
- type: related_to
  target: '[[caution-write-idk-jump-replicates-under-fresh-sampled-decode-seeds]]'
  target_id: mechanism:caution-write-idk-jump-replicates-under-fresh-sampled-decode-seeds
  confidence: high
  evidence:
  - experiments/idk-switch-naming-confirmatory/AMENDMENT.md#outcome (N2 PASS;
    confirmatory fresh-seed sampled-decode replication of this mode-switch
    finding, adding an endpoint-magnitude CI and a placebo-specificity leg)
- type: related_to
  target: '[[idk-switch]]'
  target_id: term:idk-switch
  confidence: high
  evidence:
  - experiments/idk-switch-naming-confirmatory/AMENDMENT.md#outcome (this
    mechanism's mode switch is what earns the name IDK switch once it
    replicates on fresh seeds)
- type: supported_by
  target: '[[form-judge-axis-g-rescore]]'
  target_id: experiment:form-judge-axis-g-rescore
  confidence: high
  evidence:
  - experiments/form-judge-axis-g-rescore/AMENDMENT.md#outcome (Axis-G rescore;
    baseline 0.431, intermediate doses 0.322/0.233/0.156, 1.0x 0.104, placebos
    0.427/0.406, F4 16 to 267)
- type: related_to
  target: '[[form-taxonomy-pattern-battery-underdetects-epistemic-marking]]'
  target_id: mechanism:form-taxonomy-pattern-battery-underdetects-epistemic-marking
  confidence: high
  evidence:
  - experiments/form-judge-axis-g-rescore/AMENDMENT.md (Motivation and posture;
    this is the instrument-validated resolution of the axis-G question that mechanism
    left instrument-void, over the same frozen generations, under the same unchanged
    thresholds)
- type: related_to
  target: '[[midband-write-corrupts-known-answers-more-than-it-produces-abstention]]'
  target_id: mechanism:midband-write-corrupts-known-answers-more-than-it-produces-abstention
  confidence: medium
  evidence:
  - experiments/form-judge-axis-g-rescore/AMENDMENT.md (Prediction; the dose-driven
    movement is F1-to-F4 mode switching consistent with the naming battery's O-1
    wrongness dissociation)
- type: related_to
  target: '[[write-direction-naming-battery]]'
  target_id: experiment:write-direction-naming-battery
  confidence: medium
  evidence:
  - experiments/form-judge-axis-g-rescore/AMENDMENT.md (Motivation and posture;
    re-adjudicates axis G over the naming battery's frozen Arm A generations under
    its unchanged registered thresholds)
---

*Legacy naming note (2026-08-16): this note's title/slug predates the program's vocabulary rename; see `papers/common/terminology.md` for current running-prose terms (known-unknown direction, KU readout gate, refusal axis, KU-readout coupling, IDK switch). The slug stays verbatim under usage rule 1.*

Once the open-class form boundary is graded by a validated instrument instead
of the under-detecting regex taxonomy, the mid-band caution write's
intermediate-dose behavior turns out not to be gradedly hedging output at all.
The undosed baseline already hedges nearly half its prose answers (an order of
magnitude more than the voided detector saw), and dosing does not push that
share further up: it pushes it down, because a growing fraction of rows stop
being prose altogether and become explicit "I don't know" instead. The named
write is a binary prose-to-IDK switch, not a dial that produces more or less
epistemically marked language as it turns.

**Why it matters here:** resolves the naming battery's open axis-G question
(instrument-void, not the wrong prior) with the opposite mechanism than a
graded-hedging reading would suggest, and ties the axis-G rescore to the same
O-1 answer-corrupting dose-response direction already established on the known-answer
side of the naming battery.
