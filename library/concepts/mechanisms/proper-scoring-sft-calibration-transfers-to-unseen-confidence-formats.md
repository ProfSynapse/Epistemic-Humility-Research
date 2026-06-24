---
aliases:
- calibration format generalization
- ConfTuner linguistic generalization
- proper-scoring format transfer
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:proper-scoring-sft-calibration-transfers-to-unseen-confidence-formats
  type: mechanism
  status: canonical
cause: "Fine-tuning on numerical verbalized confidence (0-100%) using a proper scoring rule (tokenized Brier score)"
effect: "The resulting calibration transfers to linguistic confidence formats (high/medium/low) unseen during training, indicating the model learns a generalized internal calibration representation rather than format-specific output patterns"
polarity: enables
related:
- '[[2508.18847--conftuner]]'
- '[[tokenized-brier-score-is-proper-scoring-rule-for-verbalized-calibration]]'
- '[[conftuner]]'
- '[[verbalized-confidence]]'
- '[[coarse-linguistic-confidence-degrades-selective-classification]]'
relationships:
- type: supported_by
  target: '[[2508.18847--conftuner]]'
  target_id: paper:2508.18847
  confidence: high
- type: related_to
  target: '[[tokenized-brier-score-is-proper-scoring-rule-for-verbalized-calibration]]'
  target_id: mechanism:tokenized-brier-score-is-proper-scoring-rule-for-verbalized-calibration
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
  target: '[[coarse-linguistic-confidence-degrades-selective-classification]]'
  target_id: mechanism:coarse-linguistic-confidence-degrades-selective-classification
  confidence: high
---

Table 3 (2508.18847) shows ConfTuner trained only on numeric confidence expressions achieves average AUROC 0.6511 on linguistic high/medium/low confidence evaluation for LLaMA, outperforming SaySelf (0.5989), base (0.5718), and LACIE (0.5126). The gap is largest on LACIE, which uses model-judgment proxy labels that may be more format-tied. This generalization suggests that proper-scoring SFT instills a calibration signal at a level of abstraction above surface format, though the mechanism linking token-level probability distribution training to linguistic category output is not directly analyzed in the paper.
