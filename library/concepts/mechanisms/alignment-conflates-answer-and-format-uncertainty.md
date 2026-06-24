---
aliases:
- alignment corrupts answer uncertainty
- SFT/DPO conflates MCQ uncertainty types
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:alignment-conflates-answer-and-format-uncertainty
  type: mechanism
  status: canonical
cause: "Supervised fine-tuning and preference optimization on human-preference dialog data optimize over both choice tokens and format tokens simultaneously without distinguishing the two uncertainty types"
effect: "The model's answer uncertainty (the calibrated per-choice ranking) is shifted toward overconfidence, destroying the well-calibrated pretrained distribution in a way that in-context learning cannot reverse"
polarity: increases
related:
- '[[2310.11732--calibration-aligned-multiple-choice]]'
- '[[format-uncertainty]]'
- '[[answer-uncertainty]]'
- '[[overconfidence]]'
- '[[supervised-finetuning]]'
- '[[direct-preference-optimization]]'
- '[[calibration]]'
- '[[expected-calibration-error]]'
- '[[rlhf-degrades-conditional-calibration]]'
relationships:
- type: supported_by
  target: '[[2310.11732--calibration-aligned-multiple-choice]]'
  target_id: paper:2310.11732
  confidence: high
- type: related_to
  target: '[[format-uncertainty]]'
  target_id: term:format-uncertainty
  confidence: high
- type: related_to
  target: '[[answer-uncertainty]]'
  target_id: term:answer-uncertainty
  confidence: high
- type: related_to
  target: '[[overconfidence]]'
  target_id: term:overconfidence
  confidence: high
- type: related_to
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
  confidence: high
- type: related_to
  target: '[[direct-preference-optimization]]'
  target_id: method:direct-preference-optimization
  confidence: high
- type: related_to
  target: '[[calibration]]'
  target_id: term:calibration
  confidence: high
- type: related_to
  target: '[[expected-calibration-error]]'
  target_id: metric:expected-calibration-error
  confidence: high
- type: related_to
  target: '[[rlhf-degrades-conditional-calibration]]'
  target_id: mechanism:rlhf-degrades-conditional-calibration
  confidence: high
---

When alignment data contains MCQ-style or MCQ-adjacent responses, the loss or preference objective updates the token probabilities for both the format identifier (which letter prefix to use) and the choice letter (which answer to select). Because these updates are entangled, the model's ranking over candidates is inflated regardless of the task and even for tasks never seen during alignment. He et al. 2023 confirm this via six synthetic schemes: only schemes that touch answer-token distributions (SFT-Choice, SFT-Mixed, DPO-Choice, DPO-Mixed) produce overconfidence on MMLU; format-only schemes (SFT-Format, DPO-Format) preserve calibration. The consequence is that aligned LMs show higher ECE than their pretrained counterparts at every model size and cannot be fixed at inference time by providing in-context examples, because ICL can adjust format preference but cannot undo the corrupted answer uncertainty.
