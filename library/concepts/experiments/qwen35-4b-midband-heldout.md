---
title: qwen35-4b-midband-heldout
aliases:
- Qwen3.5-4B mid-band doubt-snap held-out confirmation (hs20 frozen operating point)
- hs20 held-out promotion
tags:
- kg/experiment
- experiment
- doubt-snap
- j-space
kg:
  id: experiment:qwen35-4b-midband-heldout
  type: experiment
  status: canonical
related:
- '[[qwen35-4b-midband-doubt-snap]]'
- '[[qwen35-4b-midband-window-transfers-to-heldout-pool]]'
- '[[qwen35-4b-midband-write-decouples-refusal-from-format-collapse]]'
- '[[rr-cross-family-raw-refusal]]'
- '[[doubt-gated-caution-tighten]]'
relationships:
- type: builds_on
  target: '[[qwen35-4b-midband-doubt-snap]]'
  target_id: experiment:qwen35-4b-midband-doubt-snap
  confidence: high
  evidence:
  - experiments/qwen35-4b-midband-heldout/AMENDMENT.md (Frozen operating point table; nothing refit)
- type: supports
  target: '[[qwen35-4b-midband-window-transfers-to-heldout-pool]]'
  target_id: mechanism:qwen35-4b-midband-window-transfers-to-heldout-pool
  confidence: high
  evidence:
  - experiments/qwen35-4b-midband-heldout/AMENDMENT.md#outcome
- type: related_to
  target: '[[qwen35-4b-midband-write-decouples-refusal-from-format-collapse]]'
  target_id: mechanism:qwen35-4b-midband-write-decouples-refusal-from-format-collapse
  confidence: high
  evidence:
  - experiments/qwen35-4b-midband-heldout/AMENDMENT.md (Motivation and posture)
- type: different_from
  target: '[[rr-cross-family-raw-refusal]]'
  target_id: experiment:rr-cross-family-raw-refusal
  confidence: high
  evidence:
  - experiments/qwen35-4b-midband-heldout/AMENDMENT.md#outcome
  - experiments/rr-cross-family-raw-refusal/AMENDMENT.md#outcome
- type: related_to
  target: '[[doubt-gated-caution-tighten]]'
  target_id: experiment:doubt-gated-caution-tighten
  confidence: medium
---

Registered held-out stage for `qwen35-4b-midband-doubt-snap`: that experiment
established, in-sample on the FIT split of `Qwen/Qwen3.5-4B`, that a
doubt-gated caution snap written at mid-band layer hs20 decouples confab
refusal induction from output-format corruption, and stated explicitly that
"promotion to a claim requires a registered held-out stage." This experiment
is that stage. Nothing is refit: the hs20 direction set, gate threshold,
standardization scalars, and single dose (8 x sigma_c) are loaded byte-for-byte
from the resolved ladder and scored, for the first time, on the untouched
qwen35_4b held-out pool (1,332 confabs, 360 known-correct) reserved for this
purpose by `doubt-snap-cross-family-confirmatory`.

Resolved 2026-07-13, outcome shape A: the frozen window transfers. On the
1,332 held-out confabs, the gate fired on 1,286 rows, of which 872 refused
(0.678, Wilson 95% [0.652, 0.703], against the 0.60 floor) and 1,256 were
well-formed (0.977, against the 0.80 floor), so the in-sample decoupling
survives held-out scoring rather than degrading. Known-correct false-refusal
over the full 360 held-out knowns held at 14/360 = 0.039, against the 0.10
ceiling. Both placebo legs behaved: `random_direction` was a no-op relative to
baseline (confab refused delta +0.008, known delta 0.000) and `permuted_gate`
was strictly worse than the real gate on known-correct false-refusal (0.056
vs 0.039), preserving direction- and gate-specificity. This promotes the hs20
mid-band operating point from an in-sample existence result
([[qwen35-4b-midband-write-decouples-refusal-from-format-collapse]]) to a
held-out claim about Qwen3.5-4B specifically
([[qwen35-4b-midband-window-transfers-to-heldout-pool]]).

The promotion is within-model: the same doubt-gated caution write, ported
across families rather than held out within one, failed to actuate clean
refusal on either non-Qwen family tested
([[rr-cross-family-raw-refusal]]). Held-out transfer within Qwen3.5-4B and
cross-family transfer to Llama-3.2-3B/Mistral-7B are therefore a contrasting
pair: the operating point generalizes across rows it was never fit on, but
not across model families. Source of truth:
`experiments/qwen35-4b-midband-heldout/AMENDMENT.md`.
