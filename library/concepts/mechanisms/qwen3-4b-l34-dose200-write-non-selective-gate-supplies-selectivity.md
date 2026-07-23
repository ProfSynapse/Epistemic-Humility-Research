---
aliases:
- the doubt gate, not the write, supplies selectivity (Qwen3-4B/L34/dose-200)
- ungated dose-matched dosing damages 60% of known-correct rows vs 3% gated
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:qwen3-4b-l34-dose200-write-non-selective-gate-supplies-selectivity
  type: mechanism
  status: canonical
cause: "In ungated-vs-gated-dose-matched (H4), dosing every held-out row of the resolved doubt-gated caution snap unconditionally along its erase-write direction c_hat at the registered Qwen3-4B/L34 setpoint (fixed realized projection dose_target 200.0, scope anchor_onward), gate disabled, versus the same instrument with the doubt gate deciding fire per row at the frozen threshold tau_frozen, on the SAME 443 held-out rows (185 confab, 258 known-correct) at the SAME dose in one harness pass."
effect: "Ungated dosing damages 60.1% (155/258) of held-out known-correct rows (144 clean false-refusals, 10 answered-wrong, 1 degenerate) versus 3.1% (8/258) gated, a 57.0pp gap with paired McNemar p = 4.2e-43 over the 258 known-correct rows, while ungated confab conversion (77.8%) exceeds gated conversion (73.5%) by only 4.3pp. At this operating point the write itself is non-selective between known-correct and confab content once applied; the doubt gate, not the write, supplies the instrument's selectivity, at a cost of only 4.3pp of confab conversion."
polarity: enables
related:
- '[[ungated-vs-gated-dose-matched]]'
- '[[caution-write-selectivity-is-content-dependent-not-gate-created]]'
- '[[known-unknown-direction]]'
- '[[activation-steering]]'
relationships:
- type: supported_by
  target: '[[ungated-vs-gated-dose-matched]]'
  target_id: experiment:ungated-vs-gated-dose-matched
  confidence: high
  evidence:
  - experiments/ungated-vs-gated-dose-matched/AMENDMENT.md#outcome
- type: related_to
  target: '[[caution-write-selectivity-is-content-dependent-not-gate-created]]'
  target_id: mechanism:caution-write-selectivity-is-content-dependent-not-gate-created
  confidence: high
  evidence:
  - experiments/ungated-vs-gated-dose-matched/AMENDMENT.md#outcome (binding scope statement 2)
- type: related_to
  target: '[[known-unknown-direction]]'
  target_id: term:known-unknown-direction
  confidence: medium
- type: related_to
  target: '[[activation-steering]]'
  target_id: method:activation-steering
  confidence: medium
---

H4 converts the resolved doubt-gated caution snap's most-quoted mechanism
sentence, previously resting on an unregistered dose-200 diagnostic and a
permuted-gate placebo, into a registered dose-every-row contrast: the same
443 held-out rows, dosed at the same setpoint, gated versus ungated, in one
harness pass. The result is unambiguous at this operating point: removing the
gate turns a 3.1% known-correct cost into a 60.1% cost while ceding only
4.3pp of confab conversion, so the gate is what keeps the instrument from
damaging most of what it should leave alone.

This looks, on its face, like it contradicts
[[caution-write-selectivity-is-content-dependent-not-gate-created]], which
found on Qwen3.5-4B's mid-band write site that a permuted-gate control
reproduces almost all of the gated arm's confab refusal while barely touching
known-correct rows, i.e. that the write itself already discriminates
confab-like content. The two results are not in tension: they measure
different substrate, site, and dose (Qwen3-4B raw-base at the late site L34,
dose 200, versus Qwen3.5-4B at a mid-band site, dose 8 x sigma_c). Together
they establish that the caution write's content-selectivity is
operating-point-dependent, not a fixed property of the direction: at L34
dose-200 the write is non-selective and the gate supplies selectivity; at the
mid-band operating point the write itself is already selective and the gate
mainly limits collateral exposure. Neither result should be read as a
universal claim about the caution write; each is scoped to its own
substrate, site, and dose.
