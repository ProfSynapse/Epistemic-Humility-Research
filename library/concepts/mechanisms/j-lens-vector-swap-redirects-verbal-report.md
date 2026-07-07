---
aliases:
- Swapping J-lens vectors causally redirects what a model says
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:j-lens-vector-swap-redirects-verbal-report
  type: mechanism
  status: canonical
cause: "Swapping a concept's J-lens vector for a different concept's J-lens vector at a matched layer of the residual stream"
effect: "the model's verbalized top-5 output shifts to reflect the swapped-in concept on 88% of trials, versus 5% for an equal-magnitude swap confined to that same vector's non-J-space components"
polarity: enables
related:
- '[[tc-2026-workspace--verbalizable-representations-global-workspace]]'
- '[[global-workspace]]'
- '[[jacobian-lens]]'
- '[[activation-patching]]'
relationships:
- type: supported_by
  target: '[[tc-2026-workspace--verbalizable-representations-global-workspace]]'
  target_id: paper:tc-2026-workspace
  confidence: high
- type: related_to
  target: '[[global-workspace]]'
  target_id: term:global-workspace
  confidence: high
- type: related_to
  target: '[[jacobian-lens]]'
  target_id: method:jacobian-lens
  confidence: high
- type: related_to
  target: '[[activation-patching]]'
  target_id: method:activation-patching
  confidence: medium
---

Substituting one concept's [[jacobian-lens]] vector for another's at a single
matched layer causally redirects the model's subsequent verbal output toward
the swapped-in concept, succeeding on 88% of trials (Figure 6). The same
magnitude of intervention applied instead to the non-J-space components of the
same underlying vector succeeds on only 5% of trials, and the J-space
component carries just 6-7% of the vector's total variance yet dominates
verbal report (Figure 8). This is direct causal evidence that the
[[global-workspace]] subspace, not the concept representation as a whole, is
what determines what a model says.
