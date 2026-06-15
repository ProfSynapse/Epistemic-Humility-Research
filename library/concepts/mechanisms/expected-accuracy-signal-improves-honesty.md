---
aliases:
- Expected Accuracy as Training Signal Improves Honesty
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:expected-accuracy-signal-improves-honesty
  type: mechanism
  status: canonical
cause: Using model-estimated expected accuracy over multiple samples to label known/unknown questions as the training signal for [[idk-sft]] behavior
effect: Higher [[honesty-score]] than binary known/unknown labeling alone, at the cost of mild [[over-conservativeness-score|over-conservativeness]]
polarity: increases
related:
- '[[2312.07000--alignment-for-honesty]]'
- '[[idk-sft]]'
- '[[honesty-score]]'
- '[[over-conservativeness-score]]'
relationships:
- type: supported_by
  target: '[[2312.07000--alignment-for-honesty]]'
  target_id: paper:2312.07000
  confidence: high
- type: related_to
  target: '[[idk-sft]]'
  target_id: method:idk-sft
- type: related_to
  target: '[[honesty-score]]'
  target_id: metric:honesty-score
- type: related_to
  target: '[[over-conservativeness-score]]'
  target_id: metric:over-conservativeness-score
---

Binary known/unknown labeling requires a fixed threshold and does not capture the model's graded uncertainty over borderline questions. By sampling multiple model responses and using the empirical accuracy as a soft expected-accuracy signal, the training data better reflects the model's actual epistemic state. The alignment-for-honesty paper (arXiv:2312.07000) shows this approach yields higher honesty scores on [[triviaqa]] and related benchmarks, though the improved sensitivity to unknown questions also slightly increases over-conservativeness.
