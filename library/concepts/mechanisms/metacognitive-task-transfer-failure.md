---
aliases:
- cross-task metacognitive isolation
- confidence task transfer failure
- bidirectional metacognitive non-transfer
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:metacognitive-task-transfer-failure
  type: mechanism
  status: canonical
cause: "Supervised fine-tuning restricted to a single metacognitive output format (either numeric single-question confidence or pairwise comparison ranking)"
effect: "No improvement in the other metacognitive task format: single-question calibration training leaves pairwise AUCc and AUCa unchanged, and pairwise comparison training leaves single-question AUC and ECE unchanged"
polarity: prevents
related:
- '[[2510.05126--metacognition-uncertainty-communication]]'
- '[[verbalized-confidence]]'
- '[[pairwise-confidence-comparison]]'
- '[[consistency-based-confidence]]'
- '[[uncertainty-training-improves-calibration]]'
- '[[pretrained-latent-representations-enable-calibration-generalization]]'
relationships:
- type: supported_by
  target: '[[2510.05126--metacognition-uncertainty-communication]]'
  target_id: paper:2510.05126
  confidence: high
- type: related_to
  target: '[[verbalized-confidence]]'
  target_id: method:verbalized-confidence
  confidence: high
- type: related_to
  target: '[[pairwise-confidence-comparison]]'
  target_id: method:pairwise-confidence-comparison
  confidence: high
- type: related_to
  target: '[[consistency-based-confidence]]'
  target_id: method:consistency-based-confidence
  confidence: high
- type: related_to
  target: '[[uncertainty-training-improves-calibration]]'
  target_id: mechanism:uncertainty-training-improves-calibration
  confidence: high
- type: related_to
  target: '[[pretrained-latent-representations-enable-calibration-generalization]]'
  target_id: mechanism:pretrained-latent-representations-enable-calibration-generalization
  confidence: high
---

When an LLM is fine-tuned exclusively on one metacognitive format, the representations it acquires are operationally isolated from the other format. The failure is bidirectional and applies to both calibration and discrimination metrics: learning to assign numeric scores does not teach relative ranking, and learning to rank does not teach numeric calibration. This suggests that absolute confidence estimation and relative comparison are implemented as distinct behavioral routines rather than as surface projections of a common latent uncertainty signal. Multitask fine-tuning on both formats simultaneously partially overcomes this isolation, with GPT-4.1-mini showing gains in both directions under C+S training, though Llama-3.1-70B shows asymmetric behavior (single-question benefits but pairwise does not improve under multitask training).
