---
aliases:
- calibration vs humility
- communicative epistemic humility
- calibration-humility distinction
tags:
- kg/term
- concept
- term
kg:
  id: term:calibration-humility-gap
  type: term
  status: canonical
area: terms
related:
- '[[2511.07477--epistemic-pathology-polite-liar]]'
- '[[calibration]]'
- '[[overconfidence]]'
- '[[expected-calibration-error]]'
- '[[sycophancy]]'
- '[[rlhf-distorts-all-gricean-maxims]]'
- '[[confidence-evidence-ratio]]'
relationships:
- type: proposed_by
  target: '[[2511.07477--epistemic-pathology-polite-liar]]'
  target_id: paper:2511.07477
  confidence: high
- type: related_to
  target: '[[calibration]]'
  target_id: term:calibration
  confidence: medium
- type: related_to
  target: '[[overconfidence]]'
  target_id: term:overconfidence
  confidence: medium
- type: related_to
  target: '[[expected-calibration-error]]'
  target_id: metric:expected-calibration-error
  confidence: medium
- type: related_to
  target: '[[sycophancy]]'
  target_id: term:sycophancy
  confidence: medium
- type: related_to
  target: '[[rlhf-distorts-all-gricean-maxims]]'
  target_id: mechanism:rlhf-distorts-all-gricean-maxims
  confidence: medium
- type: related_to
  target: '[[confidence-evidence-ratio]]'
  target_id: metric:confidence-evidence-ratio
  confidence: medium
---

The distinction between statistical calibration (aggregate confidence matches aggregate accuracy across a distribution) and communicative epistemic humility (the model signals uncertainty to the individual user in its output). A model can satisfy the first while failing the second, because the aggregate probability distribution is invisible to users; what reaches them is uniform assertoric force.

**Why it matters here:** Motivates measuring humility beyond ECE: a training intervention that improves aggregate calibration need not improve the communicative signal that individual users receive, and may still produce the polite-liar failure mode.

**Lineage:** Coined by DeVilling (2511.07477) §5.3, building on the distinction between frequentist calibration in the sense of Guo et al. and speech-act adequacy from Gricean pragmatics.
