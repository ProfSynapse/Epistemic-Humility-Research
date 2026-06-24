---
aliases:
- confidence-routed model cascade
- calibration-downstream model cascade
- ConfTuner model cascade
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:calibrated-verbalized-confidence-enables-model-cascade-gains
  type: mechanism
  status: canonical
cause: "Routing only the samples for which a smaller LLM expresses low calibrated verbalized confidence to a more capable LLM (GPT-4o) for revision under a fixed revision budget"
effect: "Downstream task accuracy increases by up to 9.3% on HotpotQA and 5.5% on TruthfulQA relative to the unrouted baseline, because well-calibrated confidence correctly identifies which samples most benefit from revision"
polarity: enables
related:
- '[[2508.18847--conftuner]]'
- '[[conftuner]]'
- '[[verbalized-confidence]]'
- '[[expected-calibration-error]]'
- '[[auroc]]'
- '[[surrogate-confidence-estimation]]'
relationships:
- type: supported_by
  target: '[[2508.18847--conftuner]]'
  target_id: paper:2508.18847
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
  target: '[[expected-calibration-error]]'
  target_id: metric:expected-calibration-error
  confidence: high
- type: related_to
  target: '[[auroc]]'
  target_id: metric:auroc
  confidence: high
- type: related_to
  target: '[[surrogate-confidence-estimation]]'
  target_id: method:surrogate-confidence-estimation
  confidence: high
---

Section 4.3 and Figure 5 (2508.18847) show that model cascade accuracy gains are contingent on the quality of the confidence signal used for routing. ConfTuner's calibrated verbalized confidence outperforms base LLaMA confidence in cascade routing because it identifies the low-confidence samples that are genuinely incorrect rather than merely uncertain-sounding. The result extends verbalized calibration evaluation beyond ECE and AUROC metrics to a decision-theoretic downstream use case, and quantifies how calibration quality translates to accuracy under a fixed revision budget.
