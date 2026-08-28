---
aliases:
- Weight steering mitigates behavioral drift from task-specific fine-tuning
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:weight-steering-mitigates-finetuning-induced-behavioral-drift
  type: mechanism
  status: canonical
cause: "A contrastive behavioral weight direction is added after task-specific fine-tuning."
effect: "Fine-tuning-induced sycophancy or under-refusal decreases while more of the acquired task capability is retained than under the tested activation-steering variants."
polarity: decreases
related:
- '[[2511.05408--steering-language-models-weight-arithmetic]]'
- '[[contrastive-weight-steering]]'
- '[[gcd-sycophancy]]'
- '[[gsm8k]]'
relationships:
- type: supported_by
  target: '[[2511.05408--steering-language-models-weight-arithmetic]]'
  target_id: paper:2511.05408
  confidence: high
- type: related_to
  target: '[[contrastive-weight-steering]]'
  target_id: method:contrastive-weight-steering
  confidence: high
- type: related_to
  target: '[[gcd-sycophancy]]'
  target_id: dataset:gcd-sycophancy
  confidence: high
- type: related_to
  target: '[[gsm8k]]'
  target_id: dataset:gsm8k
  confidence: high
---

In Figure 3, weight steering reduces learned GCD sycophancy and changes answer correctness while preserving GCD performance better than activation steering. In Figure 6, direct-refusal weight steering and joint fine-tuning best restore safety after GSM8K fine-tuning, while activation steering and noncontrastive refusal vectors lose more math performance.
