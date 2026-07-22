---
title: margin-separation-fine-ladder
aliases:
- 'Margin separation at fine ladder resolution (M1b)'
- M1b margin-separation-fine-ladder
- fine-ladder retest of M1's censoring-aware separation criterion
tags:
- kg/experiment
- experiment
- margin-theory
kg:
  id: experiment:margin-separation-fine-ladder
  type: experiment
  status: canonical
related:
- '[[margin-mapping]]'
- '[[margin-theory-of-epistemic-state]]'
- '[[qwen-midband-margin-separation-is-instrument-resolution-limited]]'
relationships:
- type: builds_on
  target: '[[margin-mapping]]'
  target_id: experiment:margin-mapping
  confidence: high
  evidence:
  - experiments/margin-separation-fine-ladder/AMENDMENT.md (Design; substrate,
    direction, dose law, decoding, detector stack, and criterion conventions
    carried byte-identical from M1's committed artifacts; derivation reproduced
    M1's committed median, CI, and censoring counts exactly)
- type: related_to
  target: '[[margin-theory-of-epistemic-state]]'
  target_id: term:margin-theory-of-epistemic-state
  confidence: high
  evidence:
  - experiments/margin-separation-fine-ladder/AMENDMENT.md (Motivation and
    posture; retest of Claim 1's registered separation criterion at fine
    ladder resolution)
- type: supports
  target: '[[qwen-midband-margin-separation-is-instrument-resolution-limited]]'
  target_id: mechanism:qwen-midband-margin-separation-is-instrument-resolution-limited
  confidence: high
  evidence:
  - experiments/margin-separation-fine-ladder/AMENDMENT.md#outcome (Outcome;
    halted at RG0 drift check, resolved null-result by PI decision)
---

Registered fine-ladder retest of M1 (margin-mapping)'s censoring-aware
separation criterion (Claim 1) at the qwen mid-band operating point. M1's
coarse 10-rung ladder quantized the achievable bounds to {2.0, 3.0}, with
nothing between, so the criterion could not have returned any value in the
interval containing the 2.5 floor; M1's confab median landed in the critical
bracket (0.5x, 0.75x] holding 53 of 400 confab rows. M1b adds four new fine
rungs (0.55x-0.7x) inside that bracket, conditioned on only the 53 rows whose
M1 tipping fell there (212 new generations, 2.8% of M1's budget), with the
0.6x rung constructed so the observable bound equals exactly the registered
2.5 floor if the merged confab median falls at or below it. This is
experiment M1b of the margin-theory cascade, qwen35_4b only (mistral void by
instrument loss per M1).

Resolved 2026-07-17 as a null-result. HALTED at the pre-registered RG0 drift
check: fresh 0.75x-rung generations diverged in completion text from M1's
committed runlog on 3 of 8 probe rows (dose readback clean), per the signed
rule that any RG0 mismatch halts and lifts to the PI rather than retrying
silently. No separation criterion was computed, and both predictors'
scoreboard calls are UNSCORED. Diagnostics on the 53 refined rows regenerated
fresh at 0.5x and 0.75x found detector bits 98.1% identical (52/53) and
bracket classification preserved on 51/53, with byte match only 74% (0.5x) /
87% (0.75x): the drift is stochastic bf16 batch-composition non-determinism,
not a deterministic environment shift (row 131 flips its tipping bit across
batch sizes with no other variable changing). The PI resolved rather than
reworked: the boundary rows' per-row bracket noise (~4%, comparable to M1's
accepted 3.5% non-monotone rate) is the same order as the sub-rung separation
M1b set out to resolve, so the point-estimate criterion at the 0.6x boundary
is not well-posed. Verdict: qwen mid-band commitment-margin separation is
instrument-resolution-limited at the boundary, detailed in
[[qwen-midband-margin-separation-is-instrument-resolution-limited]]; M1's
Claim 1 falsification stands, and the miss is neither a clean quantization
artifact nor a clean real separation. Instrument lesson: a byte-identical
reuse guard is the wrong bar under bf16 batched greedy decoding, since
completion text depends on batch composition even in a stable environment;
the RG0 guard should have checked detector-bit / bracket-preservation, not
byte identity. No locked verdict moves: this is exploratory
instrument/mechanism-tier evidence, reported separately from the Phase 1
headline matrix. Source of truth:
`experiments/margin-separation-fine-ladder/AMENDMENT.md`.
