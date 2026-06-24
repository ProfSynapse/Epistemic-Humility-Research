---
aliases:
- open-ended calibration failure
- prompting uncertainty failure on open-ended tasks
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:open-ended-generation-breaks-prompting-calibration
  type: mechanism
  status: canonical
cause: "Applying black-box prompting-based or perplexity-based uncertainty estimation methods to open-ended LLM generation where answer choices are not provided"
effect: "Expected calibration error does not improve with model capability and AUROC gains are minimal even for the strongest models, with all prompting methods falling below the worst fine-tuned model on the same task"
polarity: prevents
related:
- '[[2406.08391--taught-to-know-what-they-dont-know]]'
- '[[open-ended-mmlu]]'
- '[[calibration-tuning]]'
- '[[verbalized-confidence]]'
- '[[p-true]]'
- '[[expected-calibration-error]]'
- '[[auroc]]'
- '[[mmlu]]'
- '[[verbalized-prob-generalizes-logit-overfits-distribution-shift]]'
relationships:
- type: supported_by
  target: '[[2406.08391--taught-to-know-what-they-dont-know]]'
  target_id: paper:2406.08391
  confidence: high
- type: related_to
  target: '[[open-ended-mmlu]]'
  target_id: dataset:open-ended-mmlu
  confidence: high
- type: related_to
  target: '[[calibration-tuning]]'
  target_id: method:calibration-tuning
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
  target: '[[expected-calibration-error]]'
  target_id: metric:expected-calibration-error
  confidence: high
- type: related_to
  target: '[[auroc]]'
  target_id: metric:auroc
  confidence: high
- type: related_to
  target: '[[mmlu]]'
  target_id: dataset:mmlu
  confidence: high
- type: related_to
  target: '[[verbalized-prob-generalizes-logit-overfits-distribution-shift]]'
  target_id: mechanism:verbalized-prob-generalizes-logit-overfits-distribution-shift
  confidence: high
---

In multiple-choice settings, max softmax probability and perplexity provide useful uncertainty signals that improve with model scale. In open-ended generation, perplexity conflates sequence length and phrasing variation with actual uncertainty about correctness, breaking the signal. Kapoor et al. (2024) demonstrate this across LLaMA-2, LLaMA-3, and Mistral model families on open-ended MMLU (Figure 2 Right, Section 4). The result implies that prompting-based calibration gains reported on multiple-choice benchmarks do not transfer to the more practically relevant open-ended setting.
