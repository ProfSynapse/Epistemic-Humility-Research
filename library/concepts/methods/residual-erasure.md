---
aliases:
- residual erasure
- layer contribution erasure
tags:
- kg/method
- concept
- method
kg:
  id: method:residual-erasure
  type: method
  status: canonical
area: mechanistic-interpretability
related:
- '[[2505.13898--do-language-models-use-their-depth-efficiently]]'
- '[[residual-stream]]'
- '[[causal-intervention]]'
relationships:
- type: proposed_by
  target: '[[2505.13898--do-language-models-use-their-depth-efficiently]]'
  target_id: paper:2505.13898
  confidence: high
- type: related_to
  target: '[[residual-stream]]'
  target_id: term:residual-stream
  confidence: high
- type: variation_of
  target: '[[causal-intervention]]'
  target_id: method:causal-intervention
  confidence: high
---

Residual erasure is a causal intervention that ablates a layer's or
sublayer's write to the residual stream and measures the resulting change,
tracked both as a relative-norm contribution and as the cosine similarity
between the erased write and the residual state (a sign flip from negative
"erasing" similarity to positive "strengthening" similarity marks a change in
what the component is doing to the running representation).

**Why it matters here:** [[2505.13898--do-language-models-use-their-depth-efficiently]]
uses residual erasure to chart each layer's and sublayer's causal contribution
to the [[residual-stream]] across depth, revealing the sharp midpoint drop in
contribution and the coincident sign flip that motivate the paper's two-phase
account of depth use.

**Lineage:** a targeted variant of [[causal-intervention]] specialized to
per-component residual-stream writes rather than whole-layer skipping.
