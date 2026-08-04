---
aliases:
- Layers as Painters
- Layers-as-painters analogy
tags:
- kg/term
- concept
- term
kg:
  id: term:transformer-layers-as-painters
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[2407.09298--transformer-layers-as-painters]]'
relationships:
- type: proposed_by
  target: '[[2407.09298--transformer-layers-as-painters]]'
  target_id: paper:2407.09298
  confidence: high
- type: studied_by
  target: '[[2407.09298--transformer-layers-as-painters]]'
  target_id: paper:2407.09298
  confidence: high
---

The transformer-layers-as-painters analogy frames each layer of a pretrained
transformer as a painter in an assembly line: every painter (layer) receives a
canvas (the residual-stream hidden state) from the painter before it, applies
its own learned style (transformation), and passes the canvas on unchanged in
size or format. The analogy motivates a battery of interventions -- skipping a
painter, having painters swap canvases, reordering the assembly line, or
running several painters on copies of the same canvas in parallel -- as a way
to probe which layers are load-bearing and which are interchangeable.

**Why it matters here:** The analogy is the organizing frame for the paper's
central empirical finding, that middle layers behave as a block of mutually
substitutable painters sharing a common canvas format (representation space),
while the first and last few painters are specialists whose removal is
catastrophic.

**Lineage:** introduced and studied by arXiv:2407.09298; motivates
[[layer-skipping|layer skipping]], [[middle-layer-repeat|middle-layer
repeat]], [[layer-order-permutation|layer-order permutation]], and
[[parallel-layer-execution|parallel layer execution]] as the paper's
diagnostic interventions.
