---
aliases:
- distractor susceptibility by model scale
- larger models more harmed by distractors
- RLHF model distractor paradox
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:distractor-prompting-reveals-calibration-gap
  type: mechanism
  status: canonical
cause: "Presenting LLMs with plausible but incorrect distractors alongside the correct answer (multiple-choice format) in lieu of free-generation"
effect: "Accuracy and calibration improve for all models, but larger RLHF-tuned models suffer a higher rate of distractor-induced harm (up to 8.03% of questions harmed for GPT-4o) than smaller open models (4.43-5.62%), suggesting that self-generated confidence heuristics in larger models interfere with distractor-presence"
polarity: mediates
related:
- '[[2502.11028--mind-the-confidence-gap]]'
- '[[reward-model-confidence-bias-drives-rlhf-overconfidence]]'
- '[[rlhf-degrades-conditional-calibration]]'
- '[[distractor-augmented-prompting]]'
- '[[simpleqa]]'
- '[[expected-calibration-error]]'
- '[[overconfidence]]'
relationships:
- type: supported_by
  target: '[[2502.11028--mind-the-confidence-gap]]'
  target_id: paper:2502.11028
  confidence: high
- type: related_to
  target: '[[reward-model-confidence-bias-drives-rlhf-overconfidence]]'
  target_id: mechanism:reward-model-confidence-bias-drives-rlhf-overconfidence
  confidence: high
- type: related_to
  target: '[[rlhf-degrades-conditional-calibration]]'
  target_id: mechanism:rlhf-degrades-conditional-calibration
  confidence: high
- type: related_to
  target: '[[distractor-augmented-prompting]]'
  target_id: method:distractor-augmented-prompting
  confidence: high
- type: related_to
  target: '[[simpleqa]]'
  target_id: dataset:simpleqa
  confidence: high
- type: related_to
  target: '[[expected-calibration-error]]'
  target_id: metric:expected-calibration-error
  confidence: high
- type: related_to
  target: '[[overconfidence]]'
  target_id: term:overconfidence
  confidence: high
---

Chhikara (2025) finds that structured answer choices with distractors systematically reduce ECE and increase accuracy across six LLMs on SimpleQA, but the pattern of who benefits and who is harmed splits by model scale and training regime. Smaller models (LLaMA3-8B, LLaMA3.1-8B, Gemma2-9B) show large accuracy gains (from ~5% to ~44-46%) while remaining substantially miscalibrated (ECE 0.36-0.37 in the D-setting). Larger RLHF-tuned models (GPT-4o) achieve near-perfect calibration in the distractor setting (ECE 0.037) but have the highest share of distractor-harmed questions (8.03%), implying that their associative recall and self-generated confidence heuristics, strengthened by RLHF, are more easily misled by plausible incorrect options. The paper does not directly attribute this pattern to RLHF as a mechanism, and GPT-4o-mini (also RLHF-tuned) shows an intermediate harm rate (6.22%), so the scale-vs-training-regime confound is not fully resolved.
