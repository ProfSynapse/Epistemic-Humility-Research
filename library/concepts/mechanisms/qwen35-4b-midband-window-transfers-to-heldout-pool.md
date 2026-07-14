---
aliases:
- hs20 mid-band operating point promoted to a held-out claim (Qwen3.5-4B)
- within-family held-out transfer of the doubt-gated caution snap
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:qwen35-4b-midband-window-transfers-to-heldout-pool
  type: mechanism
  status: canonical
cause: "The hs20 mid-band doubt-gated caution operating point (frozen direction set, gate threshold, standardization scalars, and dose 8 x sigma_c), selected and fit in-sample on Qwen3.5-4B FIT confabs by qwen35-4b-midband-doubt-snap and never refit, is applied unchanged by qwen35-4b-midband-heldout to the untouched Qwen3.5-4B held-out pool (1,332 confabs, 360 known-correct)."
effect: "Fired held-out confab refused rate reaches 872/1286 = 0.678 (Wilson 95% [0.652, 0.703], against the 0.60 floor) with well-formed rate 1256/1286 = 0.977 (against the 0.80 floor) simultaneously, so the refusal/format decoupling that defined the in-sample result survives out of sample. Known-correct false-refusal over the full 360 held-out knowns holds at 14/360 = 0.039, against the 0.10 ceiling. random_direction is a no-op (confab refused delta +0.008, known delta 0.000 vs baseline) and permuted_gate is strictly worse on known-correct false-refusal (0.056 vs 0.039), so both direction- and gate-specificity hold. The in-sample operating point therefore generalizes to rows within the same model it was never fit on, in contrast to its failure to actuate clean refusal when ported across model families in rr-cross-family-raw-refusal."
polarity: mediates
related:
- '[[qwen35-4b-midband-heldout]]'
- '[[qwen35-4b-midband-doubt-snap]]'
- '[[qwen35-4b-midband-write-decouples-refusal-from-format-collapse]]'
- '[[rr-cross-family-raw-refusal]]'
relationships:
- type: supported_by
  target: '[[qwen35-4b-midband-heldout]]'
  target_id: experiment:qwen35-4b-midband-heldout
  confidence: high
  evidence:
  - experiments/qwen35-4b-midband-heldout/AMENDMENT.md#outcome
- type: related_to
  target: '[[qwen35-4b-midband-doubt-snap]]'
  target_id: experiment:qwen35-4b-midband-doubt-snap
  confidence: high
- type: related_to
  target: '[[qwen35-4b-midband-write-decouples-refusal-from-format-collapse]]'
  target_id: mechanism:qwen35-4b-midband-write-decouples-refusal-from-format-collapse
  confidence: high
- type: different_from
  target: '[[rr-cross-family-raw-refusal]]'
  target_id: experiment:rr-cross-family-raw-refusal
  confidence: high
  evidence:
  - experiments/rr-cross-family-raw-refusal/AMENDMENT.md#outcome
---

`qwen35-4b-midband-doubt-snap` established the hs20 mid-band operating point
as an in-sample existence result only: `c_hat` was fit on FIT confab-vs-refused
labels and evaluated on those same FIT confabs, with the held-out pool
untouched by design. `qwen35-4b-midband-heldout` closes that gap by loading
the frozen window byte-for-byte (nothing refit) and scoring it for the first
time on the reserved held-out pool. The refusal, format, cost, and placebo
legs all clear the same floors the in-sample result cleared, so the window is
promoted from a within-FIT-sample finding to a held-out claim about
Qwen3.5-4B. This is a narrower generalization than a cross-family transfer:
the same write, sited at each family's own atlas-located workspace band and
tested on non-Qwen substrates in `rr-cross-family-raw-refusal`, failed to
clear the refusal floor on either Llama-3.2-3B-Instruct (format collapse
before the floor) or Mistral-7B-Instruct-v0.3 (a near-miss bounded by
detector coverage). Held-out rows within a family transfer; the family
boundary itself does not.
