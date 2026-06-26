---
aliases:
- Within-Sample Correlation Symmetry Limits Probability-Weighted Voting
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:within-sample-correlation-symmetry-limits-probability-voting
  type: mechanism
  status: canonical
cause: Within-sample log-probability/correctness correlations distributed symmetrically around zero across diverse benchmarks
effect: Reliability of probability-weighted voting in self-consistency relative to uniform majority voting
polarity: decreases
related:
- '[[2606.27359--when-likely-answers-right-sequence-probability-correctness]]'
- '[[sequence-probability]]'
- '[[self-consistency]]'
- '[[power-self-consistency]]'
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
- type: related_to
  target: '[[power-self-consistency]]'
  target_id: method:power-self-consistency
---

Across a broad set of benchmarks, the correlation between [[sequence-probability]] and correctness within individual questions is as often negative as positive, producing a near-symmetric distribution around zero (arXiv:2606.27359). Because probability weighting amplifies votes for whichever answer has higher probability, it introduces noise that cancels across the population rather than providing a consistent signal for [[self-consistency]] voting. Methods like [[power-self-consistency]] that exploit within-sample probability ordering therefore gain no systematic advantage over uniform majority voting when this symmetry holds.
