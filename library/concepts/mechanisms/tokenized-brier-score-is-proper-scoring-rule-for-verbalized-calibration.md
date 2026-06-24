---
aliases:
- proper scoring rule for verbalized calibration
- Theorem 1 ConfTuner
- tokenized Brier proper incentive
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:tokenized-brier-score-is-proper-scoring-rule-for-verbalized-calibration
  type: mechanism
  status: canonical
cause: "Fine-tuning an LLM on the tokenized Brier score loss, which penalizes the expected squared error between the model's confidence-token probability distribution and the binary correctness indicator"
effect: "The loss-minimizing model places all probability mass on the confidence token whose value is closest to the true conditional correctness probability, yielding verbalized confidence that is calibrated in the same sense classical Brier-trained classifiers are calibrated"
polarity: enables
related:
- '[[2508.18847--conftuner]]'
- '[[bounded-proper-scoring-rule-incentivizes-accuracy-and-calibration]]'
- '[[tokenized-brier-score]]'
- '[[conftuner]]'
- '[[verbalized-confidence]]'
- '[[brier-score]]'
- '[[uncertainty-training-improves-calibration]]'
relationships:
- type: supported_by
  target: '[[2508.18847--conftuner]]'
  target_id: paper:2508.18847
  confidence: high
- type: related_to
  target: '[[bounded-proper-scoring-rule-incentivizes-accuracy-and-calibration]]'
  target_id: mechanism:bounded-proper-scoring-rule-incentivizes-accuracy-and-calibration
  confidence: high
- type: related_to
  target: '[[tokenized-brier-score]]'
  target_id: method:tokenized-brier-score
  confidence: high
- type: related_to
  target: '[[conftuner]]'
  target_id: method:conftuner
  confidence: high
- type: related_to
  target: '[[verbalized-confidence]]'
  target_id: method:verbalized-confidence
  confidence: high
- type: related_to
  target: '[[brier-score]]'
  target_id: metric:brier-score
  confidence: high
- type: related_to
  target: '[[uncertainty-training-improves-calibration]]'
  target_id: mechanism:uncertainty-training-improves-calibration
  confidence: high
---

Theorem 1 (Li et al. 2508.18847) proves that the tokenized Brier score satisfies Definition 1 (proper scoring rule for verbalized confidence): for any input with true correctness probability eta, the conditional risk R(q) is minimized when q is a Dirac distribution on the token k = argmin_i |eta - i/N|. This extends the classical Brier score proper-scoring guarantee from scalar probability outputs to the discrete-token setting used by LLMs when generating verbalized confidence. The practical consequence is that no labeled confidence scores or proxy heuristics are needed: the binary correctness of the generated answer provides sufficient supervision to align verbalized confidence with true uncertainty.
