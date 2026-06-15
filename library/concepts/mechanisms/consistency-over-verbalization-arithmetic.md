---
aliases:
- Consistency-based methods dramatically outperform verbalization on arithmetic tasks
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:consistency-over-verbalization-arithmetic
  type: mechanism
  status: canonical
cause: Using [[self-consistency]] response consistency rather than direct [[verbalized-confidence]] for arithmetic reasoning tasks like [[gsm8k]]
effect: '[[auroc]] improves from 54.8% (near-random) to 92.7%, distinguishing correct from incorrect answers far more reliably'
polarity: increases
related:
- '[[2306.13063--can-llms-express-uncertainty]]'
- '[[self-consistency]]'
- '[[verbalized-confidence]]'
- '[[gsm8k]]'
- '[[auroc]]'
relationships:
- type: supported_by
  target: '[[2306.13063--can-llms-express-uncertainty]]'
  target_id: paper:2306.13063
  confidence: high
- type: related_to
  target: '[[self-consistency]]'
  target_id: method:self-consistency
- type: related_to
  target: '[[verbalized-confidence]]'
  target_id: method:verbalized-confidence
- type: related_to
  target: '[[gsm8k]]'
  target_id: dataset:gsm8k
- type: related_to
  target: '[[auroc]]'
  target_id: metric:auroc
---

For arithmetic tasks, verbalized confidence is particularly unreliable because models can produce confident verbal assertions about incorrect calculations. Response consistency across multiple samples exploits the fact that correct arithmetic answers tend to converge while incorrect ones diverge, providing a much stronger signal than any single model's self-assessment. The can-LLMs-express-uncertainty paper (arXiv:2306.13063) quantifies this as a 38-point AUROC gap between consistency-based and verbalization-based uncertainty on GSM8K.
