---
aliases:
- permuted-gate control isolates selectivity to the write direction
- doubt gate limits dosing, does not create confab/known selectivity
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:caution-write-selectivity-is-content-dependent-not-gate-created
  type: mechanism
  status: canonical
cause: "In qwen35-4b-midband-doubt-snap's permuted-gate control at hs20 dose 8 x sigma_c on Qwen/Qwen3.5-4B, randomly selecting which held-out-population rows receive the caution erase-write snap (same total fire count as the real doubt gate, but uniformly permuted across fired FIT confabs and known-correct rows) instead of gating the write on the doubt readout."
effect: "The permuted arm's directly dosed confabs refuse at 0.669, close to the gated arm's 0.684, while directly dosed known-correct rows refuse at only 0.056 -- so the confab-versus-known refusal gap survives even when the doubt gate is bypassed entirely. The write direction's content dependence in the substrate, not the doubt gate, is what makes confabs refuse and knowns not. The gate's operational contribution is in the population it exposes to the write, not in the response it produces once written: at hs20 dose 8 it fires on only 13 of 240 known-correct rows (versus all 240 if applied unconditionally), and 77% (10/13) of the knowns it does fire on are falsely refused, so gating limits collateral known-correct damage rather than creating the refusal selectivity."
polarity: complicates
related:
- '[[qwen35-4b-midband-doubt-snap]]'
- '[[qwen35-4b-midband-write-decouples-refusal-from-format-collapse]]'
- '[[known-unknown-direction]]'
- '[[qwen3-4b-l34-dose200-write-non-selective-gate-supplies-selectivity]]'
relationships:
- type: supported_by
  target: '[[qwen35-4b-midband-doubt-snap]]'
  target_id: experiment:qwen35-4b-midband-doubt-snap
  confidence: high
  evidence:
  - experiments/qwen35-4b-midband-doubt-snap/AMENDMENT.md#outcome (permuted-gate control, binding scope statement 3)
- type: related_to
  target: '[[qwen35-4b-midband-write-decouples-refusal-from-format-collapse]]'
  target_id: mechanism:qwen35-4b-midband-write-decouples-refusal-from-format-collapse
  confidence: high
  evidence:
  - experiments/qwen35-4b-midband-doubt-snap/AMENDMENT.md#outcome
- type: related_to
  target: '[[known-unknown-direction]]'
  target_id: term:known-unknown-direction
  confidence: medium
- type: related_to
  target: '[[qwen3-4b-l34-dose200-write-non-selective-gate-supplies-selectivity]]'
  target_id: mechanism:qwen3-4b-l34-dose200-write-non-selective-gate-supplies-selectivity
  confidence: high
  evidence:
  - experiments/ungated-vs-gated-dose-matched/AMENDMENT.md#outcome (binding scope statement 2)
---

The headline hs20 dose-8 decoupling result
([[qwen35-4b-midband-write-decouples-refusal-from-format-collapse]]) could in
principle come from two different places: the doubt gate could be doing the
selecting (only sending confabs to the write), or the write direction itself
could already discriminate confab-like content from known-correct content once
applied. `qwen35-4b-midband-doubt-snap`'s permuted-gate control (part of its
G3-style placebo battery, adjudicated in the red-team review) distinguishes
these by directly dosing a random selection of rows with the same total fire
count and no doubt information.

The permuted arm reproduces almost all of the gated arm's confab refusal rate
(0.669 vs 0.684) while directly dosed knowns refuse at only 0.056, so the
selectivity is a property of what the caution direction does when applied,
not of which rows the gate chose to apply it to. This complicates a naive
reading of the doubt gate as the mechanism's discriminating component: on
this substrate the gate's job is damage limitation (dosing far fewer knowns
than an unconditional write would) rather than manufacturing the confab/known
gap.

This is an operating-point-scoped finding, not a universal property of the
caution write. The registered dose-every-row contrast
`ungated-vs-gated-dose-matched` (H4) ran the same style of gated-vs-ungated
comparison at a different substrate, site, and dose (Qwen3-4B raw-base, the
late write site L34, dose 200) and found the opposite pattern: there,
ungated dosing damages 60.1% of known-correct rows versus 3.1% gated, so the
write is non-selective at that operating point and the gate is what supplies
the selectivity
([[qwen3-4b-l34-dose200-write-non-selective-gate-supplies-selectivity]]). The
two results are not in tension; together they show the write's
content-selectivity depends on where and how hard it is applied, so neither
finding generalizes past its own substrate, site, and dose.
