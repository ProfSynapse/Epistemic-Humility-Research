---
aliases:
- dose regime determines who supplies selectivity
- mid-band self-sorting write vs overdrive gate-supplied selectivity
- reconciliation of the two gate-vs-write dissociations
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:write-selectivity-is-operating-point-dependent
  type: mechanism
  status: canonical
cause: "The dosed write's setpoint sits either between the confab and known [[commitment-margin]] distributions (mid-band regime: dose above typical confab margins, below typical known margins) or above the known-margin distribution (overdrive regime: dose above typical known margins)."
effect: "At mid-band, the write self-sorts on content and the doubt gate contributes only a modest, sub-floor selectivity increment plus cost concentration (qwen35-4b-midband-doubt-snap's permuted-gate control; gate-contribution-factorial's registered Gap_Sel 0.148 qwen / 0.129 mistral, both real but below the 0.20 floor). In overdrive, the write is non-selective between confab and known-correct content once applied, and the gate becomes the sole source of selectivity (ungated-vs-gated-dose-matched's H4 result: 60.1% of known-correct rows damaged ungated versus 3.1% gated, a 57.0pp gap, at a cost of only 4.3pp of confab conversion)."
polarity: mediates
related:
- '[[ungated-vs-gated-dose-matched]]'
- '[[qwen35-4b-midband-doubt-snap]]'
- '[[gate-contribution-factorial]]'
- '[[qwen3-4b-l34-dose200-write-non-selective-gate-supplies-selectivity]]'
- '[[caution-write-selectivity-is-content-dependent-not-gate-created]]'
- '[[doubt-gate-adds-sub-floor-selectivity-write-drives-abstention-lift]]'
- '[[commitment-margin]]'
- '[[known-unknown-direction]]'
relationships:
- type: supported_by
  target: '[[ungated-vs-gated-dose-matched]]'
  target_id: experiment:ungated-vs-gated-dose-matched
  confidence: high
  evidence:
  - experiments/ungated-vs-gated-dose-matched/AMENDMENT.md#outcome (Qwen3-4B/L34/dose-200, overdrive anchor)
  - docs/research/margin-theory-framework.md (section 1, anchor result 1; section 2, Claim 2 overdrive regime)
- type: supported_by
  target: '[[qwen35-4b-midband-doubt-snap]]'
  target_id: experiment:qwen35-4b-midband-doubt-snap
  confidence: high
  evidence:
  - experiments/qwen35-4b-midband-doubt-snap/AMENDMENT.md#outcome (Qwen3.5-4B/hs20/dose_abs 12.608, mid-band anchor)
  - docs/research/margin-theory-framework.md (section 1, anchor result 2; section 2, Claim 2 mid-band regime)
- type: supported_by
  target: '[[gate-contribution-factorial]]'
  target_id: experiment:gate-contribution-factorial
  confidence: high
  evidence:
  - experiments/gate-contribution-factorial/AMENDMENT.md#outcome (both families, mid-band, registered sub-floor gate contribution)
  - docs/research/margin-theory-framework.md (section 1, anchor result 3; section 2, Claim 2 mid-band regime)
- type: related_to
  target: '[[qwen3-4b-l34-dose200-write-non-selective-gate-supplies-selectivity]]'
  target_id: mechanism:qwen3-4b-l34-dose200-write-non-selective-gate-supplies-selectivity
  confidence: high
  evidence:
  - docs/research/margin-theory-framework.md (section 1; this mechanism is the framework's overdrive-regime instance)
- type: related_to
  target: '[[caution-write-selectivity-is-content-dependent-not-gate-created]]'
  target_id: mechanism:caution-write-selectivity-is-content-dependent-not-gate-created
  confidence: high
  evidence:
  - docs/research/margin-theory-framework.md (section 1; this mechanism is the framework's mid-band-regime instance)
- type: related_to
  target: '[[doubt-gate-adds-sub-floor-selectivity-write-drives-abstention-lift]]'
  target_id: mechanism:doubt-gate-adds-sub-floor-selectivity-write-drives-abstention-lift
  confidence: high
  evidence:
  - docs/research/margin-theory-framework.md (section 1, anchor result 3)
- type: related_to
  target: '[[commitment-margin]]'
  target_id: term:commitment-margin
  confidence: high
- type: related_to
  target: '[[known-unknown-direction]]'
  target_id: term:known-unknown-direction
  confidence: medium
---

This mechanism reconciles two prior gate-vs-write dissociations that looked
contradictory because each isolated the gate's contribution at only one
operating point.
[[qwen3-4b-l34-dose200-write-non-selective-gate-supplies-selectivity]] found
that at Qwen3-4B/L34/dose 200, the write is non-selective and the gate
supplies essentially all of the instrument's selectivity.
[[caution-write-selectivity-is-content-dependent-not-gate-created]] found
that at Qwen3.5-4B/hs20/dose_abs 12.608, the write is already content-
selective in-sample and the gate's role is mainly to limit collateral
known-correct exposure. The registered
[[doubt-gate-adds-sub-floor-selectivity-write-drives-abstention-lift]] result
then showed, at the pre-registered mid-band operating points of both
families, that the gate's selectivity increment over a fire-count-matched
permuted gate is real but sits entirely below its floor.

The proposed reconciliation is that these are one geometry measured at two
different doses relative to each row's commitment margin, not three separate
facts about the gate. When the dose sits in the mid-band gap between the
confab-margin and known-margin distributions, the write already discriminates
on content and the gate adds only a modest, sub-floor increment plus cost
concentration. When the dose is pushed into the overdrive regime, above the
known-margin distribution, everything crosses or degrades regardless of
content, and the gate becomes the only thing left supplying selectivity. This
account is proposed, not yet independently confirmed: the quantitative test
is whether per-row margin distributions (the M1 margin-mapping experiment)
retrodict all three anchor results from their operating points alone,
including the overdrive result via the known-margin tail. No locked verdict
moves from this framing; it is an interpretive synthesis over already-
registered results, drafted 2026-07-16 in
`docs/research/margin-theory-framework.md` (section 2, Claim 2).
