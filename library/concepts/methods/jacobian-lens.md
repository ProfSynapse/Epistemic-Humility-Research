---
aliases:
- J-lens
- Jacobian Lens
- J-lens readout
tags:
- kg/method
- concept
- method
kg:
  id: method:jacobian-lens
  type: method
  status: canonical
area: methods
related:
- '[[tc-2026-workspace--verbalizable-representations-global-workspace]]'
- '[[global-workspace]]'
- '[[logit-lens]]'
- '[[tuned-lens]]'
- '[[residual-stream]]'
- '[[representational-drift]]'
relationships:
- type: proposed_by
  target: '[[tc-2026-workspace--verbalizable-representations-global-workspace]]'
  target_id: paper:tc-2026-workspace
  confidence: high
- type: related_to
  target: '[[global-workspace]]'
  target_id: term:global-workspace
  confidence: high
- type: related_to
  target: '[[logit-lens]]'
  target_id: method:logit-lens
  confidence: high
- type: related_to
  target: '[[tuned-lens]]'
  target_id: method:tuned-lens
  confidence: high
- type: related_to
  target: '[[residual-stream]]'
  target_id: term:residual-stream
  confidence: medium
- type: related_to
  target: '[[representational-drift]]'
  target_id: term:representational-drift
  confidence: medium
---

The Jacobian lens (J-lens) reads out the concepts a language model is "poised
to verbalize" from an intermediate hidden state. At layer l it computes the
Jacobian J_l of the final-layer residual stream with respect to the layer-l
residual stream, averaged over source position, downstream position, and a
prompt corpus, then applies the unembedding matrix to the Jacobian-transformed
state: lens(h_l) = softmax(W_U * norm(J_l * h_l)). Unlike the [[logit-lens]]
(which fixes J_l to the identity) or the [[tuned-lens]] (which fits a
correlational linear map to the output distribution), the J-lens estimates an
actual causal effect, which the authors argue corrects for
[[representational-drift]] and recovers interpretable content at depths where
the logit lens fails. The method only identifies concepts that correspond to
single tokens and the authors describe it as an imperfect, approximate probe
of a model's underlying representational structure, not a complete readout.

**Why it matters here:** J-lens is offered as a way to distinguish what a
model represents internally from what it will actually report or act on, a
distinction directly relevant to interpretability-based calibration and
hallucination-detection work that tries to read a model's internal state as a
proxy for what it "knows" or "believes."

**Lineage:** proposed in the Transformer Circuits piece "Verbalizable
Representations Form a Global Workspace in Language Models" (2026); positioned
as a causal correction to the [[logit-lens]] and an alternative to the
[[tuned-lens]]'s correlational fit.
