---
aliases:
- Early MLP sublayers drive subject enrichment
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:early-mlp-drives-subject-enrichment
  type: mechanism
  status: canonical
cause: Early MLP sublayers processing the last-subject token across lower layers
effect: The last-subject-position representation becomes attribute-rich, reaching approximately 50% attribute rate in intermediate-upper layers, substantially higher than at any other position
polarity: enables
related:
- '[[2304.14767--dissecting-recall-factual-associations]]'
- '[[subject-enrichment]]'
- '[[factual-association-recall-mechanism]]'
- '[[ffn-as-key-value-memory]]'
relationships:
- type: supported_by
  target: '[[2304.14767--dissecting-recall-factual-associations]]'
  target_id: paper:2304.14767
  confidence: high
- type: related_to
  target: '[[subject-enrichment]]'
  target_id: term:subject-enrichment
- type: related_to
  target: '[[factual-association-recall-mechanism]]'
  target_id: term:factual-association-recall-mechanism
- type: related_to
  target: '[[ffn-as-key-value-memory]]'
  target_id: term:ffn-as-key-value-memory
---

The [[subject-enrichment]] process is the first computational stage of factual recall: early MLP sublayers (layers 0-10 in GPT-2 XL) progressively enrich the last-subject-token representation by writing attribute information into the residual stream, causing the attribute-rate at that position to climb to approximately 50% in intermediate-upper layers (arXiv:2304.14767). This contrasts sharply with non-subject token positions, which exhibit far lower attribute rates at the same depth. The enrichment is driven by feedforward sublayers acting as a distributed key-value store, consistent with the [[ffn-as-key-value-memory]] hypothesis.
