---
aliases:
- LRE
- Lre
- linearity of factual relation representations
- Linear Relation Embedding (LRE)
tags:
- kg/method
- concept
- method
kg:
  id: method:linear-relation-embedding
  type: method
  status: canonical
area: mechanistic-interpretability
related:
- '[[activation-patching]]'
- '[[lre-dataset]]'
- '[[lre-faithfulness-mamba-transformer-parity]]'
relationships:
- type: related_to
  target: '[[activation-patching]]'
  target_id: method:activation-patching
- type: related_to
  target: '[[lre-dataset]]'
  target_id: dataset:lre-dataset
- type: related_to
  target: '[[lre-faithfulness-mamba-transformer-parity]]'
  target_id: mechanism:lre-faithfulness-mamba-transformer-parity
---

Linear Relation Embedding (LRE) approximates how a language model decodes a factual relation by fitting a first-order Taylor series (linear) approximation to the model's hidden-state computation at the enriched subject representation. Given a relation prompt such as "The Eiffel Tower is located in", LRE extracts a weight matrix and bias from the Jacobian of a mid-layer MLP to predict the object token directly. Faithfulness is measured as how often the linear approximation recovers the same answer the full model produces.

**Why it matters here:** LRE operationalizes the linearity of factual association representations, providing a probe of whether the model's knowledge of a relation is geometrically simple enough to support targeted editing and auditing, which connects to calibration and knowledge-boundary research.

**Lineage:** related to [[activation-patching]] as both are causal probing methods; evaluated on the [[lre-dataset]] benchmark; the finding [[lre-faithfulness-mamba-transformer-parity]] shows SSM and transformer models share comparable LRE faithfulness.
