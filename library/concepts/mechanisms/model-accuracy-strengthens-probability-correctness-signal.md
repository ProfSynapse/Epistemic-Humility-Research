---
aliases:
- Model Accuracy Strengthens Probability-Correctness Signal
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:model-accuracy-strengthens-probability-correctness-signal
  type: mechanism
  status: canonical
cause: Higher model accuracy on a task dataset
effect: Stronger within-dataset correlation between log-probability and answer correctness
polarity: increases
related:
- '[[2606.27359--when-likely-answers-right-sequence-probability-correctness]]'
- '[[sequence-probability]]'
- '[[self-consistency]]'
relationships:
- type: supported_by
  target: '[[2606.27359--when-likely-answers-right-sequence-probability-correctness]]'
  target_id: paper:2606.27359
  confidence: high
- type: related_to
  target: '[[sequence-probability]]'
  target_id: term:sequence-probability
- type: related_to
  target: '[[self-consistency]]'
  target_id: method:self-consistency
---

When a model achieves higher accuracy on a given task, the log-probability it assigns to sequences correlates more strongly with whether those sequences are correct, a pattern observed consistently across math, science, and commonsense benchmarks (arXiv:2606.27359). The mechanism is that correct answers cluster at higher probability mass when the model's distribution is closer to the true answer distribution, making the probability signal a more reliable correctness proxy. This relationship is dataset-contingent: accuracy explains most of the variance in probability-correctness correlation strength across datasets and models.
