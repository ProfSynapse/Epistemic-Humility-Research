---
aliases:
- confidence estimator divergence in LRM traces
- multi-estimator disagreement on faithful calibration
- single estimator fragility for reasoning trace confidence
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:estimator-divergence-invalidates-single-probe-faithfulness
  type: mechanism
  status: canonical
cause: "Using a single internal confidence estimator (e.g. token-probability RCC or hidden-state DeepConf or sampling consistency) to assess whether a large reasoning model is faithfully calibrated"
effect: "Conclusions about faithful calibration depend heavily on which estimator is chosen; the three estimators produce Spearman correlations with verbal decisiveness at the trace level spanning 0.081 to 0.631 on identical traces"
polarity: mediates
related:
- '[[2606.03969--faithful-calibration-framework]]'
- '[[cmfg-star]]'
- '[[faithful-calibration]]'
- '[[prefix-conditioned-sampling]]'
- '[[consistency-based-confidence]]'
- '[[verbalized-confidence]]'
- '[[p-true]]'
- '[[activation-patching-results-depend-on-method-choices]]'
- '[[generation-discrimination-gap]]'
relationships:
- type: supported_by
  target: '[[2606.03969--faithful-calibration-framework]]'
  target_id: paper:2606.03969
  confidence: high
- type: related_to
  target: '[[cmfg-star]]'
  target_id: metric:cmfg-star
  confidence: high
- type: related_to
  target: '[[faithful-calibration]]'
  target_id: term:faithful-calibration
  confidence: high
- type: related_to
  target: '[[prefix-conditioned-sampling]]'
  target_id: method:prefix-conditioned-sampling
  confidence: high
- type: related_to
  target: '[[consistency-based-confidence]]'
  target_id: method:consistency-based-confidence
  confidence: high
- type: related_to
  target: '[[verbalized-confidence]]'
  target_id: method:verbalized-confidence
  confidence: high
- type: related_to
  target: '[[p-true]]'
  target_id: method:p-true
  confidence: high
- type: related_to
  target: '[[activation-patching-results-depend-on-method-choices]]'
  target_id: mechanism:activation-patching-results-depend-on-method-choices
  confidence: high
- type: related_to
  target: '[[generation-discrimination-gap]]'
  target_id: term:generation-discrimination-gap
  confidence: high
---

At trace level, RCC (token-probability) correlates with linguistic decisiveness at Spearman 0.081, DeepConf (hidden-state) at 0.631, and Sampling Consistency at 0.104. A researcher using RCC would conclude near-zero alignment; a researcher using DeepConf would conclude substantial alignment. This is not a minor variance: the three estimators are measuring different latent quantities that happen to be only loosely coupled in long chain-of-thought outputs. The divergence parallels the activation-patching result in the existing graph: method choices mediate the apparent effect. For Phase 3 mech-interp, this implies that single-probe verdicts on internal uncertainty cannot be treated as representative of the model's global uncertainty representation.
