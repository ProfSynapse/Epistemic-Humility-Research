---
aliases:
- Probability Maximization Does Not Transfer to Accuracy
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:probability-maximization-does-not-transfer-to-accuracy
  type: mechanism
  status: canonical
cause: Selecting or tuning a decoding method to produce higher-probability sequences
effect: Reliable accuracy improvement on downstream question-answering benchmarks
polarity: prevents
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

Empirical analysis across multiple benchmarks shows that methods designed to favour higher-probability outputs do not reliably improve accuracy, and can even hurt it on tasks where low-probability tokens are disproportionately correct (arXiv:2606.27359). The underlying issue is that sequence probability conflates fluency, brevity, and format conventions with factual correctness, so maximizing it optimizes a proxy that is not aligned with task performance. This breaks the naive assumption that [[sequence-probability]] can serve as a universal criterion for selecting better answers.
