---
aliases:
- gate axis falsified: write drives most abstention, gate adds sub-floor selectivity
- permuted gate already reproduces most of the gated abstention lift
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:doubt-gate-adds-sub-floor-selectivity-write-drives-abstention-lift
  type: mechanism
  status: canonical
cause: "In a 2x2 factorial crossing {true doubt gate, fire-count-matched permuted gate} x {true c_hat caution direction, K=5 fresh random directions} plus baseline, scored on both confab and known-correct populations under the wide two-instrument stack, on Qwen3.5-4B hs20 (dose_abs 12.608, the census operating point) and Mistral-7B-Instruct-v0.3 hs16 (dose_abs 3.665, RR2/RR3 lineage), with sign-robust selectivity Sel_abs(arm) = |confab_lift| - |known_lift| and gate-selectivity gap Gap_Sel(direction) = Sel_abs(true_gate, direction) - Sel_abs(permuted_gate, direction)."
effect: "The doubt gate is not what supplies the instrument's selectivity at these operating points: the dosed c_hat write alone, applied through a fire-count-matched PERMUTED gate, already drives most of the abstention lift (permuted-gate confab abstention 0.550 qwen / 0.600 mistral vs undosed baselines 0.083 / 0.282). The true doubt gate adds a real but sub-floor selectivity increment over the permuted gate (Gap_Sel(c_hat) 0.148 qwen, bootstrap 95% CI [0.119, 0.177]; 0.129 mistral, CI [0.103, 0.156]; both CIs exclude zero but sit entirely below the pre-registered 0.20 floor), and its cost-protection margin falls short of its own floor (0.008 qwen, CI [-0.011, 0.028], includes zero; 0.034 mistral, CI [0.016, 0.055], real but under the 0.10 floor). This falsifies the 'selectivity comes from the gate, not the write' claim on both substrates: the gate's row selection contributes something measurable but not the dominant share of the instrument's benefit."
polarity: complicates
related:
- '[[gate-contribution-factorial]]'
- '[[caution-write-selectivity-is-content-dependent-not-gate-created]]'
- '[[qwen3-4b-l34-dose200-write-non-selective-gate-supplies-selectivity]]'
- '[[matched-magnitude-placebo-sign-survives-as-distributional-property]]'
- '[[known-unknown-direction]]'
- '[[activation-steering]]'
relationships:
- type: supported_by
  target: '[[gate-contribution-factorial]]'
  target_id: experiment:gate-contribution-factorial
  confidence: high
  evidence:
  - experiments/gate-contribution-factorial/AMENDMENT.md#outcome (Verdict; Per-family criterion results P2/P3)
- type: related_to
  target: '[[caution-write-selectivity-is-content-dependent-not-gate-created]]'
  target_id: mechanism:caution-write-selectivity-is-content-dependent-not-gate-created
  confidence: high
  evidence:
  - experiments/gate-contribution-factorial/AMENDMENT.md (Motivation and posture)
- type: related_to
  target: '[[qwen3-4b-l34-dose200-write-non-selective-gate-supplies-selectivity]]'
  target_id: mechanism:qwen3-4b-l34-dose200-write-non-selective-gate-supplies-selectivity
  confidence: high
- type: related_to
  target: '[[matched-magnitude-placebo-sign-survives-as-distributional-property]]'
  target_id: mechanism:matched-magnitude-placebo-sign-survives-as-distributional-property
  confidence: medium
  evidence:
  - experiments/gate-contribution-factorial/AMENDMENT.md (Design, direction-specificity denominator)
- type: related_to
  target: '[[known-unknown-direction]]'
  target_id: term:known-unknown-direction
  confidence: medium
- type: related_to
  target: '[[activation-steering]]'
  target_id: method:activation-steering
  confidence: medium
---

Registered successor to two prior gate-vs-write dissociations that ran at a
single operating point each: `caution-write-selectivity-is-content-dependent-not-gate-created`
(Qwen3.5-4B mid-band, permuted-gate reproduces most gated confab refusal) and
`qwen3-4b-l34-dose200-write-non-selective-gate-supplies-selectivity` (Qwen3-4B
raw-base late site, the opposite pattern, where the gate is the dominant
discriminator). Neither prior result carried a pre-registered magnitude floor
or a known-correct-population cost-protection statistic, and neither had run
on Mistral. This factorial adds both: a pre-registered 0.20 selectivity-gap
floor and a 0.10 cost-protection floor, tested on two families at once
(Qwen3.5-4B hs20 primary, Mistral-7B-Instruct-v0.3 hs16 secondary) under the
wide two-instrument stack rather than the narrow phrase detector.

The result lands closer to the mid-band precedent than the L34 precedent: on
both families the write, routed through a permuted gate with no doubt
information, already recovers most of the gated arm's abstention lift, and
the true gate's own contribution, while measurably positive (both
gate-selectivity-gap confidence intervals exclude zero), sits entirely below
the pre-registered floor on both P2 (selectivity gap) and P3 (cost
protection). The claim that "selectivity comes from the gate, not the write"
(the mid-band controller's own governing statement,
`doubt-gated-caution-tighten` AMENDMENT lines 71-73) does not survive a
pre-registered floor test at these operating points, on either substrate.

Direction-specificity, evaluated separately against the
`placebo-seed-distribution-census` K=15 null (S1, and cannot rescue or
falsify the gate axis), dissociates by family as the design predicted: qwen's
gated confab lift is sign-opposed to the census suppressive null (effect
ratio 7.27, floor 3.0), while mistral's is same-signed as the census
recruiting null and falls short of the floor (ratio 2.03), reproducing the
RR2/RR3 direction-axis failure under a stricter K=15 denominator. The gate
axis and the direction axis are independently adjudicated: this experiment
shows the gate axis fails on both families regardless of how the direction
axis lands. No locked verdict moves; this is exploratory instrument/mechanism
evidence, reported separately from the Phase 1 headline matrix, the census,
and RR2/RR3. Source of truth:
`experiments/gate-contribution-factorial/AMENDMENT.md`.
