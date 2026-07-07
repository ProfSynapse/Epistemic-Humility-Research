---
aliases:
- J-space
- global workspace in language models
- global workspace theory (LLMs)
- verbalizable representations
tags:
- kg/term
- concept
- term
kg:
  id: term:global-workspace
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[tc-2026-workspace--verbalizable-representations-global-workspace]]'
- '[[jacobian-lens]]'
- '[[concepts-as-subspaces]]'
- '[[linear-representation-hypothesis]]'
- '[[steering-vector]]'
relationships:
- type: proposed_by
  target: '[[tc-2026-workspace--verbalizable-representations-global-workspace]]'
  target_id: paper:tc-2026-workspace
  confidence: high
- type: related_to
  target: '[[jacobian-lens]]'
  target_id: method:jacobian-lens
  confidence: high
- type: related_to
  target: '[[concepts-as-subspaces]]'
  target_id: term:concepts-as-subspaces
  confidence: medium
- type: related_to
  target: '[[linear-representation-hypothesis]]'
  target_id: term:linear-representation-hypothesis
  confidence: medium
- type: related_to
  target: '[[steering-vector]]'
  target_id: term:steering-vector
  confidence: medium
---

The global workspace (operationalized as the "J-space") is a small, privileged
subspace of a language model's intermediate residual-stream activity that is
available for verbal report, deliberate modulation, and flexible downstream
reasoning, sitting atop a much larger volume of activity that is not. It is
identified via the [[jacobian-lens]] as the set of points expressible as a
sparse nonnegative combination of J-lens vectors (sparsity k, typically 25),
by analogy with the "access consciousness" distinction in cognitive science
between representations poised for use in reasoning and speech versus
representations that remain unreported. The paper that introduces this term is
explicit that it does not claim the architectural machinery of global
workspace theory is literally reproduced in a transformer, and that the J-lens
is an approximate, incomplete probe of whatever this subspace actually is.

**Why it matters here:** this term names the gap between what a model
represents and what it verbalizes or reports, which is the same gap that
epistemic-humility work on calibration, self-report, and hallucination
detection has to reason about when it uses a model's internal states (probes,
logit lens, activation reads) as a stand-in for what the model "knows."

**Lineage:** introduced in the Transformer Circuits piece "Verbalizable
Representations Form a Global Workspace in Language Models" (2026); contrasts
with prior work treating concept directions ([[concepts-as-subspaces]],
[[steering-vector]]) as uniformly accessible, by arguing only a subset of such
directions sit inside the reportable/actionable workspace.
