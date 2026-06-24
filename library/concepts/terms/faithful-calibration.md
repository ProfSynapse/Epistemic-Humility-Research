---
aliases:
- FC
- faithful confidence expression
- alignment between intrinsic and expressed confidence
tags:
- kg/term
- concept
- term
kg:
  id: term:faithful-calibration
  type: term
  status: canonical
area: terms
related:
- '[[2606.03969--faithful-calibration-framework]]'
- '[[cmfg-star]]'
- '[[linguistic-decisiveness-scorer]]'
- '[[prefix-conditioned-sampling]]'
- '[[generation-discrimination-gap]]'
- '[[calibration]]'
- '[[verbalized-confidence]]'
- '[[overconfidence]]'
relationships:
- type: proposed_by
  target: '[[2606.03969--faithful-calibration-framework]]'
  target_id: paper:2606.03969
  confidence: high
- type: related_to
  target: '[[cmfg-star]]'
  target_id: metric:cmfg-star
  confidence: medium
- type: related_to
  target: '[[linguistic-decisiveness-scorer]]'
  target_id: method:linguistic-decisiveness-scorer
  confidence: medium
- type: related_to
  target: '[[prefix-conditioned-sampling]]'
  target_id: method:prefix-conditioned-sampling
  confidence: medium
- type: related_to
  target: '[[generation-discrimination-gap]]'
  target_id: term:generation-discrimination-gap
  confidence: medium
- type: related_to
  target: '[[calibration]]'
  target_id: term:calibration
  confidence: medium
- type: related_to
  target: '[[verbalized-confidence]]'
  target_id: method:verbalized-confidence
  confidence: medium
- type: related_to
  target: '[[overconfidence]]'
  target_id: term:overconfidence
  confidence: medium
---

The alignment between a model's intrinsic confidence (as estimated from token probabilities, hidden states, or sampling consistency) and its linguistically expressed confidence (how hedged or decisive the model's verbal output is). Distinct from standard calibration, which measures alignment between expressed confidence and empirical accuracy. A model can be accurately calibrated while being unfaithfully calibrated if its verbal hedging is decoupled from its internal uncertainty signal.

**Why it matters here:** Identifies a failure mode that output-level calibration metrics miss: a model may say 'I am not sure' when its internal probability signal is high, or assert confidently when internal uncertainty is high. This decoupling becomes especially salient in long-chain-of-thought models where users interpret verbose deliberation as a confidence signal.

**Lineage:** Operationalized and formalized in Gani et al. 2026 (arXiv:2606.03969). Related concept of generation-discrimination gap described earlier in the ITI literature (2306.03341).
