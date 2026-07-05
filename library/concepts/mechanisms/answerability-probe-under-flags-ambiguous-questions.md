---
aliases:
- Answerability probe under-flags ambiguous questions
- ambiguous unknowns read as answerable
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:answerability-probe-under-flags-ambiguous-questions
  type: mechanism
  status: canonical
cause: "Reading ambiguous/underspecified unknown questions with a frozen linear answerability probe fit on the general known/unknown boundary (L20/24/28, raw instruct base)."
effect: "The probe under-flags them relative to every other unanswerability flavor (AUROC 0.92 vs 0.98-0.99; median unknown score 0.19, i.e. most ambiguous questions read as answerable), leaving a systematic blind spot in the answerability gate."
polarity: decreases
related:
- '[[internal-flavor-geometry--category-fleet]]'
- '[[input-ambiguity]]'
- '[[unanswerability-detection-shares-one-axis-across-flavors]]'
- '[[known-unknowns-taxonomy]]'
- '[[global-conformal-threshold-fails-conditional-coverage]]'
relationships:
- type: supported_by
  target: '[[internal-flavor-geometry--category-fleet]]'
  target_id: paper:internal-flavor-geometry
  confidence: high
- type: related_to
  target: '[[input-ambiguity]]'
  target_id: term:input-ambiguity
  confidence: high
- type: related_to
  target: '[[unanswerability-detection-shares-one-axis-across-flavors]]'
  target_id: mechanism:unanswerability-detection-shares-one-axis-across-flavors
  confidence: high
- type: related_to
  target: '[[known-unknowns-taxonomy]]'
  target_id: term:known-unknowns-taxonomy
  confidence: high
- type: related_to
  target: '[[global-conformal-threshold-fails-conditional-coverage]]'
  target_id: mechanism:global-conformal-threshold-fails-conditional-coverage
  confidence: low
---

Session-0036 category-geometry arm. A plausible reading is that ambiguity is
input-side uncertainty (the question is missing context) rather than knowledge-side
uncertainty (the answer is not determined), so a boundary fit mostly on
knowledge-side unknowns places ambiguous items on the answerable side. This is a
concrete failure stratum for the training-free answerability gate and one of the
Tier-3 follow-up targets alongside the counterfactual residual direction. It also
echoes the pliability finding that ambiguity behaves differently on the behavioral
side (low flip rate 8.8 percent despite high eligible count).
