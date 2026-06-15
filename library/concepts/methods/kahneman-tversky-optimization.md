---
aliases:
- KTO
- Kahneman-Tversky Optimization
- Kahneman-Tversky Optimization (KTO)
tags:
- kg/method
- concept
- method
kg:
  id: method:kahneman-tversky-optimization
  type: method
  status: canonical
area: methods
related:
- '[[2402.01306--kto-prospect-theoretic]]'
- '[[human-aware-loss-functions]]'
- '[[reinforcement-learning-from-human-feedback]]'
- '[[direct-preference-optimization]]'
relationships:
- type: proposed_by
  target: '[[2402.01306--kto-prospect-theoretic]]'
  target_id: paper:2402.01306
  confidence: high
- type: derived_from
  target: '[[human-aware-loss-functions]]'
  target_id: term:human-aware-loss-functions
- type: derived_from
  target: '[[reinforcement-learning-from-human-feedback]]'
  target_id: method:reinforcement-learning-from-human-feedback
- type: variation_of
  target: '[[direct-preference-optimization]]'
  target_id: method:direct-preference-optimization
---

Kahneman-Tversky Optimization (KTO) aligns language models using only a binary desirability signal per output, with no requirement for paired chosen/rejected responses. Its loss function is derived from [[prospect-theory]]'s model of human utility under uncertainty, applying a loss-aversion asymmetry so that the model is penalized more heavily for undesirable outputs than it is rewarded for desirable ones.

**Why it matters here:** KTO is the third preference-training arm in the Phase 1 experiment (SFT vs DPO vs KTO). Because it does not need [[preference-pair-data]], it can be applied directly to abstention-labeled examples, and comparing it against [[direct-preference-optimization]] reveals how much the paired-signal requirement and the loss-aversion inductive bias each contribute to abstention learning.

**Lineage:** derives from [[reinforcement-learning-from-human-feedback]]; variant of [[direct-preference-optimization]] that eliminates paired preferences; extends the [[human-aware-loss-functions]] framework introduced in the same paper.
