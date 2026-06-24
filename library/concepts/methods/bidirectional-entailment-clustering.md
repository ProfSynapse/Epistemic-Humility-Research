---
aliases:
- bidirectional NLI clustering
- semantic equivalence clustering
- bi-directional entailment algorithm
tags:
- kg/method
- concept
- method
kg:
  id: method:bidirectional-entailment-clustering
  type: method
  status: canonical
area: methods
related:
- '[[2302.09664--semantic-uncertainty-kuhn]]'
- '[[semantic-entropy]]'
- '[[semantic-equivalence]]'
- '[[decoding-randomness]]'
relationships:
- type: proposed_by
  target: '[[2302.09664--semantic-uncertainty-kuhn]]'
  target_id: paper:2302.09664
  confidence: high
- type: related_to
  target: '[[semantic-entropy]]'
  target_id: method:semantic-entropy
  confidence: medium
- type: related_to
  target: '[[semantic-equivalence]]'
  target_id: term:semantic-equivalence
  confidence: medium
- type: related_to
  target: '[[decoding-randomness]]'
  target_id: term:decoding-randomness
  confidence: medium
---

An algorithm that clusters free-form text generations into semantic equivalence classes by checking, for each pair of generated sequences, whether both directions of natural language entailment hold (using an NLI classifier such as DeBERTa-large fine-tuned on MNLI). Two sequences are placed in the same class if and only if each entails the other within the context of the question. Complexity is O(M^2) in the worst case but reduced by transitivity.

**Why it matters here:** Provides the semantic clustering step that makes semantic entropy tractable and accurate. Achieves 92.7% accuracy on TriviaQA and 95.3% on CoQA at lower temperatures; degrades to 61% at temperature 1.5, establishing a practical upper bound on sampling temperature.

**Lineage:** Introduced in Kuhn, Gal, and Farquhar (arXiv:2302.09664, ICLR 2023) as the core component of semantic entropy. Operationalizes the linguistic concept of semantic equivalence via textual entailment, building on prior NLI work (MNLI, DeBERTa).
