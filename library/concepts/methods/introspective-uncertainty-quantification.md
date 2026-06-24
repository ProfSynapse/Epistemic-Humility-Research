---
aliases:
- IUQ
- introspective UQ
- two-stage introspective UQ
tags:
- kg/method
- concept
- method
kg:
  id: method:introspective-uncertainty-quantification
  type: method
  status: canonical
area: methods
related:
- '[[2506.18183--reasoning-models-dont-know]]'
- '[[verbalized-confidence]]'
- '[[consistency-based-confidence]]'
- '[[overconfidence]]'
- '[[expected-calibration-error]]'
- '[[calibration]]'
- '[[reasoning-fine-tuning]]'
relationships:
- type: proposed_by
  target: '[[2506.18183--reasoning-models-dont-know]]'
  target_id: paper:2506.18183
  confidence: high
- type: related_to
  target: '[[verbalized-confidence]]'
  target_id: method:verbalized-confidence
  confidence: medium
- type: related_to
  target: '[[consistency-based-confidence]]'
  target_id: method:consistency-based-confidence
  confidence: medium
- type: related_to
  target: '[[overconfidence]]'
  target_id: term:overconfidence
  confidence: medium
- type: related_to
  target: '[[expected-calibration-error]]'
  target_id: metric:expected-calibration-error
  confidence: medium
- type: related_to
  target: '[[calibration]]'
  target_id: term:calibration
  confidence: medium
- type: related_to
  target: '[[reasoning-fine-tuning]]'
  target_id: method:reasoning-fine-tuning
  confidence: medium
---

A two-stage self-verbalized uncertainty quantification procedure in which a first model instance answers a question and reports its confidence, then a second fresh model instance reads the first model's chain-of-thought trace and provides an updated confidence estimate without changing the answer. Three conservativeness levels are defined: IUQ-Low (neutral re-assessment), IUQ-Medium (prompted to find flaws in reasoning), and IUQ-High (prompted to find flaws, prior confidence withheld).

**Why it matters here:** Demonstrates that zero-shot post-hoc reflection on chain-of-thought traces can improve calibration for some reasoning models (DeepSeek, o3-Mini) while worsening it for others (Claude), providing a diagnostic for whether a model's self-confidence is tractably adjustable through reasoning rather than training.

**Lineage:** Introduced in arXiv:2506.18183 (Mei et al., 2025). Related to verbalized-confidence methods and the multi-stage reasoning paradigm of chain-of-thought prompting.
