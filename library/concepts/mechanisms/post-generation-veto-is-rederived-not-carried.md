---
aliases:
- Post-generation veto is re-derived, not carried
- the trust dial recomputes from the emitted answer instead of transporting the pre-gen doubt reading
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:post-generation-veto-is-rederived-not-carried
  type: mechanism
  status: canonical
cause: "Generation of an answer between the pre-generation anchor read and the post-generation veto read (cross-position probe transfer, axis geometry, and residualization on the cached Amendment S/T/U/W surfaces)."
effect: "The correctness/veto axis fails cross-position transfer (0.58-0.64 vs 0.81-0.86 in-position) while the answerability axis transports near-perfectly (0.96-0.99), the whole state is largely rewritten (same-row pre-to-post cosine about 0.58), and the post-read advantage (+0.022 raw base, +0.094 GRPO-v2) survives residualizing every carried readout: the veto is predominantly NEW information computed from the emitted answer, on an axis orthogonal to doubt (whitened cosine -0.02). Post-training increases the re-derived share."
polarity: mediates
related:
- '[[internal-confab-mechanics--cpu-fleet]]'
- '[[answerability-and-correctness-are-orthogonal-readout-axes]]'
- '[[per-answer-correctness-linearly-readable-post-generation]]'
- '[[task-training-sharpens-not-creates-hallucination-veto]]'
- '[[answerability-probe-transfers-across-qa-datasets]]'
- '[[known-unknown-direction]]'
relationships:
- type: supported_by
  target: '[[internal-confab-mechanics--cpu-fleet]]'
  target_id: paper:internal-confab-mechanics
  confidence: high
- type: related_to
  target: '[[answerability-and-correctness-are-orthogonal-readout-axes]]'
  target_id: mechanism:answerability-and-correctness-are-orthogonal-readout-axes
  confidence: high
- type: related_to
  target: '[[per-answer-correctness-linearly-readable-post-generation]]'
  target_id: mechanism:per-answer-correctness-linearly-readable-post-generation
  confidence: high
- type: related_to
  target: '[[task-training-sharpens-not-creates-hallucination-veto]]'
  target_id: mechanism:task-training-sharpens-not-creates-hallucination-veto
  confidence: high
- type: related_to
  target: '[[answerability-probe-transfers-across-qa-datasets]]'
  target_id: mechanism:answerability-probe-transfers-across-qa-datasets
  confidence: medium
- type: related_to
  target: '[[known-unknown-direction]]'
  target_id: term:known-unknown-direction
  confidence: high
---

Session-0037 veto-transport analysis
(experiments/commitment-point/analysis-committed/veto-transport/, TODO
item 31), CPU-only on the cached Amendment S/T/U/W extraction tensors. Answerability
behaves as a carried question property (it rides through generation almost
untouched) while correctness/trust behaves as a computed answer property. Same-row
correctness projection survives weakly (r about 0.34-0.37), so a carried minority
exists, but out-of-sample veto reproduction (dial to hallucination 0.784 raw base,
0.969 GRPO-v2, matching the published 0.980) plus the residualized post-read surplus
attribute most of the veto to recomputation. Design consequence: interventions on
the veto should target the answer-token window where it crystallizes, not the
pre-generation anchor; the W surface's transported 0.905 is an upper bound because
its answerability and veto labels coincide. Readout-not-causal evidence.
