---
aliases:
- sigma-distance does not transfer across models
- dose windows are absolute, not sigma-normalized
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:steering-dose-windows-are-absolute-not-sigma-transferable
  type: mechanism
  status: canonical
cause: "A caution-direction write dose is calibrated as an absolute registered grid on one model checkpoint (Qwen3-4B, where the grid sits at a normal working sigma-distance from the fitted c_hat direction), and the same absolute grid is then carried over to a different model with its own independently fitted write-direction standard deviation (sigma_c), rather than a per-model absolute-unit recalibration."
effect: "The coherent operating window does not track sigma-distance across models: Qwen3.5-4B fits sigma_c=2.80, about 4.7x smaller than the Qwen3-4B reference, so the registered grid's lowest dose (100) is already a roughly 38-sigma write and every one of 854 fired FIT confabs degenerates; Qwen3.5-9B collapses at 15.8 sigma, the distance that was a normal working dose on the reference model, with well-formed rows falling from 886 to 2 across doses 100/150/200 as refusal content rises 18 -> 363 -> 886. Coherent dose windows are absolute (in raw write units) and model-specific: recalibrating a per-model absolute-unit grid, not sigma-matching, is required before dose viability can be assessed on a new substrate."
polarity: prevents
related:
- '[[doubt-snap-cross-family-confirmatory]]'
- '[[qwen35-4b-midband-doubt-snap]]'
- '[[qwen35-late-site-entangles-refusal-and-format-collapse]]'
relationships:
- type: supported_by
  target: '[[doubt-snap-cross-family-confirmatory]]'
  target_id: experiment:doubt-snap-cross-family-confirmatory
  confidence: high
  evidence:
  - experiments/doubt-snap-cross-family-confirmatory/NOTEBOOK.md (2026-07-09 entry)
- type: built_on_by
  target: '[[qwen35-4b-midband-doubt-snap]]'
  target_id: experiment:qwen35-4b-midband-doubt-snap
  confidence: high
  evidence:
  - experiments/qwen35-4b-midband-doubt-snap/AMENDMENT.md (Stage B fit result table)
- type: related_to
  target: '[[qwen35-late-site-entangles-refusal-and-format-collapse]]'
  target_id: mechanism:qwen35-late-site-entangles-refusal-and-format-collapse
  confidence: medium
---

Readback confirmed the write itself always realized the commanded projection
exactly on both Qwen3.5 cells, which rules out an inert-write explanation for
the dose-viability failures in `doubt-snap-cross-family-confirmatory`: the
grid was simply too strong in absolute terms for a substrate whose fitted
write direction has much smaller variance than the reference model's. The
portable lesson is that a sigma-normalized dose is not a safe way to move a
calibrated instrument between checkpoints.

`qwen35-4b-midband-doubt-snap` builds directly on this lesson: its per-layer
dose grids are sized in absolute multiples of each candidate layer's own
freshly fitted sigma_c rather than inherited from the late-site grid, because
all three mid-band candidates fit smaller sigma_c than the late site and
would collapse even faster under the original absolute grid.
