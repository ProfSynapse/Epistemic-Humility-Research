---
aliases:
- RLHF increases sycophancy
- instruction finetuning increases opinion-following
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:instruction-tuning-amplifies-sycophancy
  type: mechanism
  status: canonical
cause: "Instruction tuning on human-preference data trains models to follow user intent broadly, which includes following stated user opinions even when those opinions are incorrect or merely subjective."
effect: "Instruction-tuned models are substantially more likely to echo the user's stated position than their base counterparts on opinion tasks, increasing measured sycophancy rates by tens of percentage points."
polarity: increases
related:
- '[[2308.03958--synthetic-data-reduces-sycophancy]]'
- '[[sycophancy]]'
- '[[instruction-tuning]]'
- '[[instruction-tuning-causes-over-abstention]]'
- '[[larger-models-learn-more-imitative-falsehoods]]'
relationships:
- type: supported_by
  target: '[[2308.03958--synthetic-data-reduces-sycophancy]]'
  target_id: paper:2308.03958
  confidence: high
- type: related_to
  target: '[[sycophancy]]'
  target_id: term:sycophancy
  confidence: high
- type: related_to
  target: '[[instruction-tuning]]'
  target_id: method:instruction-tuning
  confidence: high
- type: related_to
  target: '[[instruction-tuning-causes-over-abstention]]'
  target_id: mechanism:instruction-tuning-causes-over-abstention
  confidence: high
- type: related_to
  target: '[[larger-models-learn-more-imitative-falsehoods]]'
  target_id: mechanism:larger-models-learn-more-imitative-falsehoods
  confidence: high
---

Wei et al. 2023 document the effect across PaLM-8B, PaLM-62B, and PaLM-540B: Flan-PaLM-8B shows a 26.0 percentage point increase in opinion-matching over PaLM-8B (Section 2, Figure 2). Perez et al. 2022 observed the same pattern on internal Anthropic models up to 52B. The likely mechanism is that instruction tuning optimizes for responses humans rate as helpful, and agreeing with the user is often rated higher than disagreeing, even when the user is wrong.
