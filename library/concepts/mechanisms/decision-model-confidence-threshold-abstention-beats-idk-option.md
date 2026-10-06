---
title: decision-model-confidence-threshold-abstention-beats-idk-option
aliases:
- Calibrated-confidence threshold abstention beats an explicit IDK option
- Abstain on low confidence rather than list an I don't know option
- dmio H3 THRESHOLD_BETTER
- Confidence threshold catches more true unknowns than the IDK option at matched over-abstention
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:decision-model-confidence-threshold-abstention-beats-idk-option
  type: mechanism
  status: canonical
  recorded_at: 2026-10-06
cause: "In the decision-model-idk-option experiment, the same untrained pointer decision model (Qwen3.5-2B-Base torso, LoRA r16 + pointer head) abstains on PopQA 4-way questions in one of two ways: by picking an added \"I don't know\" option, or, on the no-IDK run, by abstaining whenever its CAL-temperature-calibrated top-option confidence falls below a threshold tau fit on CAL so that over-abstention on known questions matches the option's CAL over-IDK rate (r_cal 0.0022, k = 1, tau 0.3354)."
effect: "At matched over-abstention on TEST known questions (baseline 0.0097 vs over-IDK 0.0066, check difference 0.0031 [-0.0074, 0.0140], matched), the threshold abstains on 0.1849 of unknown-true questions against 0.0185 for the IDK option, delta -0.1665 [-0.1848, -0.1480] (paired question-level cluster bootstrap; H3 THRESHOLD_BETTER), falsifying the IDK-beats-threshold line. The descriptive TEST-matched comparison points the same way (tau 0.3180, delta -0.0842 [-0.0995, -0.0702]). On the descriptive threshold curve the baseline abstains on 0.9194 of unknown-true at 0.1012 over-abstention on known (tau 0.5164)."
polarity: enables
related:
- '[[decision-model-idk-option]]'
- '[[decision-model-idk-option-under-used-despite-tracking-unknowns]]'
- '[[selective-prediction]]'
- '[[temperature-scaling]]'
- '[[abstention-recall]]'
- '[[over-abstention]]'
- '[[correctness-probe-abstention-exceeds-uncertainty-baselines]]'
- '[[popqa]]'
relationships:
- type: supported_by
  target: '[[decision-model-idk-option]]'
  target_id: experiment:decision-model-idk-option
  confidence: high
  evidence:
  - experiments/decision-model-idk-option/experiment.yaml (verdict field)
  - experiments/decision-model-idk-option/analysis-committed/dmio-pointer_gate_summary.json
    (gate h3; secondary test_matched_comparison, threshold_curve)
  - experiments/decision-model-idk-option/AMENDMENT.md#outcome (Gate results, H3
    detail; Falsifier adjudication; Caveats, H3 operating point)
- type: related_to
  target: '[[decision-model-idk-option-under-used-despite-tracking-unknowns]]'
  target_id: mechanism:decision-model-idk-option-under-used-despite-tracking-unknowns
  confidence: high
- type: related_to
  target: '[[selective-prediction]]'
  target_id: term:selective-prediction
  confidence: high
  evidence:
  - experiments/decision-model-idk-option/AMENDMENT.md (Gates, H3; abstain when
    calibrated confidence is below a CAL-fit threshold)
- type: related_to
  target: '[[temperature-scaling]]'
  target_id: method:temperature-scaling
  confidence: high
- type: related_to
  target: '[[abstention-recall]]'
  target_id: metric:abstention-recall
  confidence: high
- type: related_to
  target: '[[over-abstention]]'
  target_id: term:over-abstention
  confidence: high
- type: related_to
  target: '[[correctness-probe-abstention-exceeds-uncertainty-baselines]]'
  target_id: mechanism:correctness-probe-abstention-exceeds-uncertainty-baselines
  confidence: low
  evidence:
  - experiments/decision-model-idk-option/AMENDMENT.md#outcome (a score-based
    abstention gate outperforms the alternative; different signal, model and
    task, so context only)
- type: related_to
  target: '[[popqa]]'
  target_id: dataset:popqa
  confidence: high
---

For an untrained decision model, abstaining when calibrated confidence is low
beats listing an "I don't know" option. At the same low over-abstention rate on
known questions, the confidence threshold catches about 18% of the questions
the base torso truly does not know; the option catches about 2%.

**Why it matters here:** a decision readout that cannot refuse can still be
given an abstention policy without changing its choice list. Its calibrated
confidence is the better default on this model. The follow-up the cell names
is to make the threshold the default abstention mechanism, with tau fit on CAL
at a pre-stated budget, tested against an IDK-trained arm (needs its own
amendment).

**Caveats:** the matched comparison sits at a very low operating point (about
1% over-abstention; tau fit from 1 of 268 CAL known questions and held fixed
in the bootstrap, so CAL uncertainty is not propagated). Pointer arm only; on
the letter-logit arm the operating points were not matched and H3 is
NOT-ADJUDICABLE. Exploratory tier-2, no training, one checkpoint per arm, one
2B model, PopQA 4-way multiple choice plus IDK. Source of truth:
`experiments/decision-model-idk-option/AMENDMENT.md` (Outcome), resolved
2026-10-06 (falsified).
