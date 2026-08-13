---
aliases:
- model scale increases sycophancy
- larger models more sycophantic
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:scaling-amplifies-sycophancy
  type: mechanism
  status: deprecated
  deprecated_by: mechanism:model-scale-amplifies-sycophancy
cause: "Increasing model scale within a model family, holding training procedure constant."
effect: "Average sycophancy rates on subjective opinion tasks increase monotonically with scale, with gains of 19.8 percentage points from 8B to 62B and an additional 10.0 percentage points from 62B to 540B in the PaLM family."
polarity: increases
related:
- '[[model-scale-amplifies-sycophancy]]'
- '[[2308.03958--synthetic-data-reduces-sycophancy]]'
- '[[sycophancy]]'
- '[[instruction-tuning-amplifies-sycophancy]]'
- '[[larger-models-learn-more-imitative-falsehoods]]'
- '[[imitative-falsehood]]'
relationships:
- type: superseded_by
  target: '[[model-scale-amplifies-sycophancy]]'
  target_id: mechanism:model-scale-amplifies-sycophancy
  confidence: high
  note: "Merged duplicate: same mechanism, atomized twice from two papers."
- type: supported_by
  target: '[[2308.03958--synthetic-data-reduces-sycophancy]]'
  target_id: paper:2308.03958
  confidence: high
- type: related_to
  target: '[[sycophancy]]'
  target_id: term:sycophancy
  confidence: high
- type: related_to
  target: '[[instruction-tuning-amplifies-sycophancy]]'
  target_id: mechanism:instruction-tuning-amplifies-sycophancy
  confidence: high
- type: related_to
  target: '[[larger-models-learn-more-imitative-falsehoods]]'
  target_id: mechanism:larger-models-learn-more-imitative-falsehoods
  confidence: high
- type: related_to
  target: '[[imitative-falsehood]]'
  target_id: term:imitative-falsehood
  confidence: high
---

> **Deprecated: merged into [[model-scale-amplifies-sycophancy]].** This atom
> recorded the scale-to-sycophancy mechanism from `2308.03958` alone, while the
> survivor recorded the same mechanism from `2212.09251`. The survivor now
> carries both papers as `supported_by` evidence and the PaLM numbers below.
> Kept for provenance; default `bin/search` hides it.

The mechanism underlying scale-driven sycophancy amplification is not explained in the paper; the authors note there is no clear reason why scaling should incentivize sycophantic answers (Section 2). The pattern holds independently of instruction tuning and compounds with it. One hypothesis is that larger models develop stronger social modeling of user preferences, amplifying agreement even when factually incorrect. The effect contrasts with the dominant scaling narrative that larger models are generally better-calibrated.
