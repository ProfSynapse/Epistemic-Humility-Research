---
aliases:
- layer-wise cosine similarity
- all-layers similarity matrix
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:hidden-state-cosine-similarity
  type: metric
  status: canonical
area: metrics
related:
- '[[2407.09298--transformer-layers-as-painters]]'
- '[[residual-stream]]'
relationships:
- type: measured_by
  target: '[[2407.09298--transformer-layers-as-painters]]'
  target_id: paper:2407.09298
  confidence: high
- type: related_to
  target: '[[residual-stream]]'
  target_id: term:residual-stream
---

Hidden-state cosine similarity is the cosine of the angle between the
residual-stream hidden-state vectors produced at two different layers (or at
the same layer across two runs), computed pairwise across all layers to form
an all-layers similarity matrix. High cosine similarity between a pair of
layers indicates their output representations occupy directionally similar
regions of activation space.

**Why it matters here:** The metric is the direct evidentiary basis for the
paper's central finding: a block of high-cosine-similarity middle layers in
the all-layers similarity matrix coincides exactly with the layers that
tolerate skipping and input-source swapping, supporting the claim that middle
layers share a common representation space.

**Lineage:** reported in arXiv:2407.09298 (Figure 2, Figure 3) for Llama2-7B
and BERT-Large.
