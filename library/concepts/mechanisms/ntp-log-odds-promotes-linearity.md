---
aliases:
- NTP log-odds matching promotes linear concept representations
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:ntp-log-odds-promotes-linearity
  type: mechanism
  status: canonical
cause: "The [[next-token-prediction]] objective satisfying the log-odds matching condition (predicted concept log-odds equal prior log-odds, independent of conditioning context)"
effect: "Concept steering vectors (unembedding differences for binary concept flips) are mutually parallel in the [[linear-representation-hypothesis|representation space]] for a fixed concept, establishing a linear structure"
polarity: enables
related:
- '[[2403.03867--origins-linear-representations-large-language-models]]'
- '[[next-token-prediction]]'
- '[[linear-representation-hypothesis]]'
- '[[steering-vector]]'
relationships:
- type: supported_by
  target: '[[2403.03867--origins-linear-representations-large-language-models]]'
  target_id: paper:2403.03867
  confidence: high
- type: related_to
  target: '[[next-token-prediction]]'
  target_id: method:next-token-prediction
- type: related_to
  target: '[[linear-representation-hypothesis]]'
  target_id: term:linear-representation-hypothesis
- type: related_to
  target: '[[steering-vector]]'
  target_id: term:steering-vector
---

When the next-token prediction loss is minimised under a log-odds matching condition, the optimal solution requires that the difference between any two context embeddings that differ only in a binary concept value is a fixed vector independent of context. This algebraic constraint directly implies that the unembedding differences used as concept steering vectors are mutually parallel, providing a theoretical grounding for the empirically observed linearity of concept representations (arXiv:2403.03867). The condition is satisfied approximately in practice because LLMs are trained to capacity on large corpora, making log-odds matching a plausible inductive bias.
