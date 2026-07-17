---
title: Commitment Margin
aliases:
- commitment margin
- tipping dose
- susceptibility channel
tags:
- kg/term
- concept
- term
kg:
  id: term:commitment-margin
  type: term
  status: canonical
area: terms
related:
- '[[gate-contribution-factorial]]'
- '[[known-unknown-direction]]'
- '[[write-selectivity-is-operating-point-dependent]]'
- '[[doubt-gate-adds-sub-floor-selectivity-write-drives-abstention-lift]]'
relationships:
- type: related_to
  target: '[[gate-contribution-factorial]]'
  target_id: experiment:gate-contribution-factorial
  confidence: high
  evidence:
  - docs/research/margin-theory-framework.md (section 1, anchor result 3)
- type: related_to
  target: '[[known-unknown-direction]]'
  target_id: term:known-unknown-direction
  confidence: high
  evidence:
  - docs/research/margin-theory-framework.md (section 2, Claim 1)
- type: related_to
  target: '[[write-selectivity-is-operating-point-dependent]]'
  target_id: mechanism:write-selectivity-is-operating-point-dependent
  confidence: high
  evidence:
  - docs/research/margin-theory-framework.md (section 2, Claim 2)
- type: related_to
  target: '[[doubt-gate-adds-sub-floor-selectivity-write-drives-abstention-lift]]'
  target_id: mechanism:doubt-gate-adds-sub-floor-selectivity-write-drives-abstention-lift
  confidence: medium
  evidence:
  - docs/research/margin-theory-framework.md (section 1, anchor result 3)
---

For each (model, question) pair, the commitment margin is the minimum
perturbation dose along the known-unknown direction that flips the row's
behavior to abstention. Confabulation-prone rows have short margins;
well-supported known-correct rows have long ones. The margin is the
susceptibility channel: unlike a readout (a linear probe or gate score
extracted from a single forward pass), the margin is revealed only by
intervention, and it is proposed as the encoding of a row's epistemic state
that a dose-response experiment actually measures.

**Why it matters here:** the commitment margin gives a single quantity that
is proposed to retrodict all three anchor results of the margin-theory
framework from their operating points alone: whether a fixed dose lands in
the gap between the confab-margin distribution and the known-margin
distribution (mid-band, where the write self-sorts) or above the known-margin
distribution (overdrive, where the write is non-selective and the gate
becomes the sole source of selectivity). It is the keystone quantity for the
M1 margin-mapping experiment in the framework's cascade (per-row dose
staircase along the known-unknown direction, both families).

**Lineage:** introduced 2026-07-16 in `docs/research/margin-theory-framework.md`
as a working-framework concept, not yet a registered claim; it names an
observation already stated as a governed binding-scope sentence in
`ungated-vs-gated-dose-matched/AMENDMENT.md` ("the write's content-selectivity
is operating-point-dependent") and gives it a proposed mechanism. See
[[write-selectivity-is-operating-point-dependent]] for the dose-regime
account and [[boundary-anisotropy]] for the family-level companion property.
