---
aliases:
- mid-band caution write decouples refusal from JSON corruption (Qwen3.5-4B)
- hs20 dose-8 decoupling window
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:qwen35-4b-midband-write-decouples-refusal-from-format-collapse
  type: mechanism
  status: canonical
cause: "On Qwen/Qwen3.5-4B (bf16, hybrid linear-attention architecture), moving the doubt-gated caution erase-write snap from the registered late write site (hs30, model-local depth fraction round(0.94*(num_hidden_layers-1))) to a mid-band J-space workspace layer identified by an eff_dim_frac profile peak (hs20, hs23, or hs26), and dosing at a per-layer sigma_c multiple on the same fired FIT confabs."
effect: "At hs20 dose 8 x sigma_c, refusal induction and output well-formedness decouple: fired FIT confabs reach refused 0.684 (594/869) with well_formed 0.980, clearing both a 0.60 refusal floor and a 0.80 well-formed floor simultaneously, with known-correct false-refusal 0.042 (10/240), all in-sample FIT. The in-grid late-site comparator (hs30, re-run here) never clears both floors at any dose (peak refused about 0.31 at doses 12-16 with well-formedness already degrading), reproducing its own entangled collapse. Potency at matched relative dose is monotone toward earlier layers (hs20 > hs23 > hs26 > hs30); hs23 (the eff-dim profile peak) and hs26 never reach the refusal floor. This is existence evidence for a decoupling window at one registered mid-band candidate, not a claim that hs20 is the operating optimum: layers earlier than hs20 were profiled but never fit or dosed, and the result is in-sample FIT only, with the held-out pool untouched by design."
polarity: enables
related:
- '[[qwen35-4b-midband-doubt-snap]]'
- '[[qwen35-late-site-entangles-refusal-and-format-collapse]]'
- '[[j-space-mediated-actuation-fragility]]'
- '[[steering-dose-windows-are-absolute-not-sigma-transferable]]'
relationships:
- type: supported_by
  target: '[[qwen35-4b-midband-doubt-snap]]'
  target_id: experiment:qwen35-4b-midband-doubt-snap
  confidence: high
  evidence:
  - experiments/qwen35-4b-midband-doubt-snap/AMENDMENT.md#outcome
  - experiments/qwen35-4b-midband-doubt-snap/analysis-committed/dose_ladder_full_summary.json
- type: related_to
  target: '[[qwen35-late-site-entangles-refusal-and-format-collapse]]'
  target_id: mechanism:qwen35-late-site-entangles-refusal-and-format-collapse
  confidence: high
  evidence:
  - experiments/qwen35-4b-midband-doubt-snap/AMENDMENT.md#outcome
- type: related_to
  target: '[[j-space-mediated-actuation-fragility]]'
  target_id: mechanism:j-space-mediated-actuation-fragility
  confidence: medium
  evidence:
  - experiments/qwen35-4b-midband-doubt-snap/AMENDMENT.md (Motivation and posture)
- type: related_to
  target: '[[steering-dose-windows-are-absolute-not-sigma-transferable]]'
  target_id: mechanism:steering-dose-windows-are-absolute-not-sigma-transferable
  confidence: medium
---

`qwen35-late-site-entangles-refusal-and-format-collapse` established that the
registered late write site on Qwen3.5-4B has no dose where refusal content and
JSON well-formedness are both high: the two curves cross well below the
registered thresholds. `qwen35-4b-midband-doubt-snap` asked whether that is a
property of the write site or of the mechanism, by moving the same doubt-gated
caution snap to a J-space workspace-band layer identified from an
effective-dimension-fraction profile and testing the resulting per-layer dose
ladder against the same floors.

The result answers the question for this substrate: the late-site
entanglement was a write-site problem, not a caution-direction or
doubt-gate problem. hs20 finds a coherent dose window (dose 6 misses only the
refusal floor, dose 12 misses only the well-formed floor, dose 16 and above
collapses to the same near-total degeneracy the late site shows everywhere)
that the late site never reaches at any point in the same locked grid. This
replicates, on a second and architecturally distinct (hybrid linear-attention)
substrate, the same-model Qwen3-4B lesson that a mid-band write site can
outperform a late write site once dose is calibrated per layer.
