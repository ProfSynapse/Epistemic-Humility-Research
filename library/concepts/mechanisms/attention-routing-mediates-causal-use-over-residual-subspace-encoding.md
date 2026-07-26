---
aliases:
- attention routing mediates causal use over residual subspace encoding
- top-of-stack attention routing is causally necessary
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:attention-routing-mediates-causal-use-over-residual-subspace-encoding
  type: mechanism
  status: canonical
cause: "Whether a hierarchical variable (top-of-stack identity) is read out via [[attention-knockout|attention routing]] to the relevant position, versus merely encoded in a low-rank residual-stream subspace that a [[linear-probe]] can decode"
effect: "Determines causal use: masking attention to the true top-of-stack position collapses long-distance task accuracy (-0.967 vs -0.014 for a random edge), while ablating the probe-aligned residual subspace at matched rank leaves accuracy near-unchanged"
polarity: mediates
related:
- '[[2604.22128--dissociating-decodability-causal-use-bracket-sequence-transformers]]'
- '[[attention-knockout]]'
- '[[linear-probe]]'
- '[[activation-patching]]'
- '[[high-probe-accuracy-does-not-imply-causal-use]]'
- '[[probing-accuracy-task-importance-disconnect]]'
relationships:
- type: supported_by
  target: '[[2604.22128--dissociating-decodability-causal-use-bracket-sequence-transformers]]'
  target_id: paper:2604.22128
  confidence: high
- type: related_to
  target: '[[attention-knockout]]'
  target_id: method:attention-knockout
  confidence: high
- type: related_to
  target: '[[linear-probe]]'
  target_id: method:linear-probe
  confidence: high
- type: related_to
  target: '[[activation-patching]]'
  target_id: method:activation-patching
  confidence: medium
- type: related_to
  target: '[[high-probe-accuracy-does-not-imply-causal-use]]'
  target_id: mechanism:high-probe-accuracy-does-not-imply-causal-use
  confidence: high
- type: related_to
  target: '[[probing-accuracy-task-importance-disconnect]]'
  target_id: term:probing-accuracy-task-importance-disconnect
  confidence: high
---

In transformers trained on the Dyck (balanced-bracket) language, arXiv:2604.22128
shows that top-of-stack identity, depth, and distance are all linearly decodable
from the residual stream out-of-distribution, but only the attention-routed
readout is causally load-bearing: masking a closing bracket's attention edge to
its true top-of-stack position (via [[attention-knockout]]) drops long-distance
accuracy by -0.967+/-0.009, versus -0.014+/-0.002 for masking a random edge,
while ablating the probe-aligned residual subspace at low rank ([[linear-probe]]
directions) has near-zero effect relative to ablating a random subspace of the
same rank. [[activation-patching]] further localizes the causally critical step
to the layer-1 attention block at the closing-bracket position, where recovery
jumps from ~0% to 100%. The same pattern replicates in a templated
subject-verb-agreement task, where masking the single subject-to-verb attention
edge collapses accuracy while the subject-number probe stays highly accurate.

**Why it matters here:** this sharpens
[[high-probe-accuracy-does-not-imply-causal-use]] and the
[[probing-accuracy-task-importance-disconnect]] into a specific, mechanistic
claim: in a setting with an explicit hierarchical ground truth, causal use is
mediated by which computational pathway (attention routing to a specific
position) reads the variable out, not merely by whether the variable is encoded
somewhere in the residual stream.
