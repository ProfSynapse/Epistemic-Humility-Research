---
aliases:
- llama's hs17 direction-specificity is instrument-robust
- llama joins qwen under the wide two-instrument stack
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:llama-hs17-direction-specificity-survives-wide-instrument
  type: mechanism
  status: canonical
cause: "On raw-base Llama-3.2-3B-Instruct, the frozen KU-gated `c_hat` write at the mid-band site hs17 (dose 4.9549) and its fifteen matched-dose random-direction controls (seeds 910001-910015) are regenerated with a text-persisting harness and re-scored under the program's wide two-instrument stack (detector_v2 OR-joined with blinded context-free adjudication), the same instrument that certified qwen's late-site controls."
effect: "The narrow `clean_tighten` conversion bridges cleanly (regenerated arm-1 637/872 = 0.7305, consistent with the parent's 0.7420 and the resolved narrow cell's 0.7282). Under the wide instrument, arm-1 net lift is 0.6319 (arm0 0.1560 to arm1 0.7878), clearing the 0.30 floor by more than double, and the effect ratio against the strongest of fifteen random-direction wide lifts (0.0677, seed 910005) is 9.34 against the 3.0 floor. The random census is centered near zero under the wide instrument (6 positive / 8 negative / 1 zero, median -0.0092), mirroring the narrow census. Llama's hs17 direction-specificity is therefore instrument-robust, not an artifact of the narrow canonical-phrase detector, extending `llama-hs17-write-is-direction-specific` from one instrument to two. The known-correct cost gate stays NOT-ADJUDICABLE: the KU gate fired on 0 of 334 held-out known-correct rows, below the pre-registered 22-row floor."
polarity: enables
related:
- '[[llama-hs17-wide-instrument-rescore]]'
- '[[llama-hs17-write-is-direction-specific]]'
- '[[gated-controller-and-layer-site-controls-survive-wide-instrument]]'
- '[[abstention-wide-instrument-calibration]]'
relationships:
- type: supported_by
  target: '[[llama-hs17-wide-instrument-rescore]]'
  target_id: experiment:llama-hs17-wide-instrument-rescore
  confidence: high
  evidence:
  - experiments/llama-hs17-wide-instrument-rescore/AMENDMENT.md#outcome (WR-G1,
    WR-G2, WR-G3)
- type: derived_from
  target: '[[llama-hs17-write-is-direction-specific]]'
  target_id: mechanism:llama-hs17-write-is-direction-specific
  confidence: high
  evidence:
  - experiments/llama-hs17-wide-instrument-rescore/AMENDMENT.md (Motivation
    and posture; regenerates and wide-rescores the identical operating
    point and random-direction census that mechanism established under the
    narrow instrument, closing the instrument-scope gap paper 5 SS4.8 and
    SS6.5 named)
- type: related_to
  target: '[[gated-controller-and-layer-site-controls-survive-wide-instrument]]'
  target_id: mechanism:gated-controller-and-layer-site-controls-survive-wide-instrument
  confidence: medium
  evidence:
  - experiments/llama-hs17-wide-instrument-rescore/AMENDMENT.md (Motivation
    and posture; mirrors what wide-instrument-control-rescore and
    qwen3-4b-l34-placebo-seed-census established for qwen's late site,
    now for llama's mid-band site)
- type: related_to
  target: '[[abstention-wide-instrument-calibration]]'
  target_id: experiment:abstention-wide-instrument-calibration
  confidence: high
  evidence:
  - experiments/llama-hs17-wide-instrument-rescore/AMENDMENT.md (Instruments;
    the wide two-instrument stack pins, detector_v2 plus blinded
    adjudication, are hash-checked identical to this experiment's
    committed pins)
---

Llama's hs17 mid-band write had a verified direction-specificity claim under
exactly one instrument, the narrow `clean_tighten` phrase detector. This
mechanism closes that scope gap: regenerating the same operating point and
the same fifteen random-direction seeds with a text-persisting harness, then
re-scoring under the wide two-instrument stack, reproduces both the
replication (narrow bridge 0.7305) and the direction-specificity margin
(effect ratio 9.34, comparable to the narrow census's 8.25) under a
materially different grading instrument. Llama's selective write is not a
narrow-detector artifact, joining qwen as a family whose direction-specific
write is instrument-robust.

**Lineage:** extends `llama-hs17-write-is-direction-specific` (narrow-only)
to a second instrument; mirrors the qwen precedent set by
`wide-instrument-control-rescore` and `qwen3-4b-l34-placebo-seed-census`.
Source of truth: `experiments/llama-hs17-wide-instrument-rescore/AMENDMENT.md`,
Outcome section, resolved 2026-08-26.
