---
title: no-abstention-prompt-gated-replication
aliases:
- 'No-abstention-prompt gated replication (cross-family)'
- instruction-free gated-write replication
- no-abstention-prompt cell
tags:
- kg/experiment
- experiment
- actuation
kg:
  id: experiment:no-abstention-prompt-gated-replication
  type: experiment
  status: canonical
related:
- '[[doubt-snap-cross-family-confirmatory]]'
- '[[j-space-calibrated-layer-contrast-qwen3-4b]]'
- '[[qwen35-4b-midband-heldout]]'
- '[[llama-hs17-direction-specificity]]'
- '[[gemma4-e4b-kv-seam-quarantine]]'
- '[[abstention-wide-instrument-calibration]]'
- '[[prompt-vs-training-panel]]'
- '[[abstention-instruction-amplifies-the-gated-write]]'
- '[[detector-v2-overfires-on-random-arm-text]]'
relationships:
- type: builds_on
  target: '[[doubt-snap-cross-family-confirmatory]]'
  target_id: experiment:doubt-snap-cross-family-confirmatory
  confidence: high
  evidence:
  - experiments/no-abstention-prompt-gated-replication/render.py (imports the
    parent render and deletes only the abstention sentence, enforced by
    import-time byte-for-byte assertions)
- type: builds_on
  target: '[[j-space-calibrated-layer-contrast-qwen3-4b]]'
  target_id: experiment:j-space-calibrated-layer-contrast-qwen3-4b
  confidence: high
  evidence:
  - experiments/no-abstention-prompt-gated-replication/AMENDMENT.md (Design,
    Substrate table; qwen3-4b frozen operating point hs23/setpoint 25 and the
    with-prompt reference lift 165/185 that sets the G1 floor)
- type: builds_on
  target: '[[qwen35-4b-midband-heldout]]'
  target_id: experiment:qwen35-4b-midband-heldout
  confidence: high
  evidence:
  - experiments/no-abstention-prompt-gated-replication/AMENDMENT.md (Design,
    Substrate table; qwen3.5-4b hs20 frozen operating point, dose 12.6082)
- type: builds_on
  target: '[[llama-hs17-direction-specificity]]'
  target_id: experiment:llama-hs17-direction-specificity
  confidence: high
  evidence:
  - experiments/no-abstention-prompt-gated-replication/AMENDMENT.md (Design,
    Substrate table; llama hs17 operating point and the with-prompt lift
    0.7190 that sets the G1b floor)
- type: builds_on
  target: '[[gemma4-e4b-kv-seam-quarantine]]'
  target_id: experiment:gemma4-e4b-kv-seam-quarantine
  confidence: high
  evidence:
  - experiments/no-abstention-prompt-gated-replication/AMENDMENT.md (Design,
    Substrate table; gemma below-seam hs15 operating point, dose 173.6577)
- type: builds_on
  target: '[[abstention-wide-instrument-calibration]]'
  target_id: experiment:abstention-wide-instrument-calibration
  confidence: high
  evidence:
  - experiments/no-abstention-prompt-gated-replication/cell.yaml
    (grading.pinned_instrument; detector_v2, pool builder, and adjudication
    scripts sha-pinned from that cell and reused as libraries)
- type: related_to
  target: '[[prompt-vs-training-panel]]'
  target_id: experiment:prompt-vs-training-panel
  confidence: high
  evidence:
  - experiments/prompt-vs-training-panel/AMENDMENT.md#outcome (the same
    abstention sentence alone elicits 90.89% refusal recall from the
    untrained base vs 0.00% without it, the finding that motivated this
    cell's confound test)
---

# No-abstention-prompt gated replication (cross-family)

Exploratory tier-2 cell, signed 2026-08-28, resolved 2026-08-30. Tests
whether the doubt-gated abstention write reproduces its gated-over-no_op
benefit when the system prompt contains no abstention instruction (JSON
contract only), across all five registered families at their frozen mid-band
operating points, with the detector threshold refit on the FIT split under
the new prompt and grading by the pinned two-stage wide instrument.

Outcome (AMENDMENT.md#outcome is authoritative): the pre-registered
falsifier (qwen3-4b gated-over-no_op two-stage lift CI including zero) did
NOT fire. Two-stage lifts, every 95% CI excluding zero: qwen3-4b +11.4pp
(12.7% of its with-prompt magnitude; G1 FAIL on the half-with-prompt floor,
the pre-stated middle band), llama +9.3pp (G1b FAIL on its floor), mistral
+18.8pp, qwen3.5-4b +45.6pp, gemma +47.0pp (G3 descriptive). Known-correct
cost near zero everywhere; G2 NOT-ADJUDICABLE (dosed-N 5 < 52); G4 PASS in
both eligible families (llama's random direction moves slightly toward
answering). Framing revision: instruction-amplified, not
instruction-independent.

Instrument history: v1 judge lanes for llama and qwen3.5-4b closed
VOID_CELL_TERMINAL on clear-positive decoy agreement; a pre-stated v2 lane
with with-prompt gated-arm overt-refusal decoys passed calibration in both
(9/9 shards). The v1 voids stand in the record.
