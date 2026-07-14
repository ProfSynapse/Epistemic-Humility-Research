---
aliases:
- Bias-direction features predict judge degradation across domains
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:bias-direction-features-predict-cross-domain-judge-degradation
  type: mechanism
  status: canonical
cause: "A linear predictor uses per-layer projections of judge activations onto fitted bias directions."
effect: "The predictor anticipates cue-induced score degradation on benchmark domains excluded from direction fitting."
polarity: enables
related:
- '[[2607.11871--inside-unfair-judge-mechanistic-interpretability-account-llm]]'
- '[[judge-bias-outcome-predictor]]'
- '[[effective-bias-vector]]'
- '[[auroc]]'
relationships:
- type: supported_by
  target: '[[2607.11871--inside-unfair-judge-mechanistic-interpretability-account-llm]]'
  target_id: paper:2607.11871
  confidence: high
- type: related_to
  target: '[[judge-bias-outcome-predictor]]'
  target_id: method:judge-bias-outcome-predictor
  confidence: high
- type: related_to
  target: '[[effective-bias-vector]]'
  target_id: method:effective-bias-vector
  confidence: high
- type: related_to
  target: '[[auroc]]'
  target_id: metric:auroc
  confidence: high
---

The linear projection model reaches AUROC 0.82 on SocialMaze, BBQ, and GPQA, compared with 0.63 for a zero-shot text-LLM baseline. A richer LightGBM model performs better in-domain but falls to 0.75 cross-domain, indicating that the compact bias-direction features are the more transferable signal in this evaluation.
