---
aliases:
- Key-Value Memorization Gates Truth Encoding
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:kv-memorization-gates-truth-encoding
  type: mechanism
  status: canonical
cause: "Phase 1 of training: rapid [[key-value-associative-memory|key-value memorisation]] of subject-attribute associations within approximately 1000 batches, reaching above 99% accuracy on true sequences"
effect: "Phase 2 emergence: abrupt appearance of a linear [[truth-direction|truth encoding]] at approximately 7500 batches that enables the model to reduce loss on false sequences by leveraging the memorised true associations"
polarity: enables
related:
- '[[2510.15804--emergence-linear-truth-encodings-language-models]]'
- '[[key-value-associative-memory]]'
- '[[truth-direction]]'
- '[[two-phase-memorization-encoding]]'
relationships:
- type: supported_by
  target: '[[2510.15804--emergence-linear-truth-encodings-language-models]]'
  target_id: paper:2510.15804
  confidence: high
- type: related_to
  target: '[[key-value-associative-memory]]'
  target_id: method:key-value-associative-memory
- type: related_to
  target: '[[truth-direction]]'
  target_id: term:truth-direction
- type: related_to
  target: '[[two-phase-memorization-encoding]]'
  target_id: term:two-phase-memorization-encoding
---

Emergence of linear truth encoding follows a two-phase training dynamic: in the first phase the model rapidly memorises subject-attribute associations as key-value pairs in feed-forward layers, achieving near-perfect accuracy on true-sentence prediction. In the second phase, having saturated accuracy on true sequences, the model gains loss reduction on false sequences by encoding a truth variable that allows it to adjust probability assignments relative to the memorised true values (arXiv:2510.15804). The first phase is thus a prerequisite for the second: without the memorised factual associations there is no reference against which truth-value deviations can be encoded.
