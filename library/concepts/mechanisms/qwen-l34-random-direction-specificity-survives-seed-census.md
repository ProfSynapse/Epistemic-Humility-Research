---
aliases:
- qwen late-site specificity upgraded from single-draw to distributional form
- hs34 gated write beats a fifteen-seed random-direction null
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:qwen-l34-random-direction-specificity-survives-seed-census
  type: mechanism
  status: canonical
cause: "On raw-base Qwen3-4B at the late write site hs34 (dose 200.0), the frozen gated confab-tightening lift (+62.7pp, 137/185 vs undosed 21/185) is contrasted against fifteen fresh matched-dose random unit directions (seeds 920001-920015), scored under the same wide two-instrument stack `wide-instrument-control-rescore` used for its single-draw (seed 20260707) result."
effect: "The strongest of the fifteen random arms shifts the rate by only 13.0 percentage points (seed 920006), giving an effect ratio of 0.6270 / 0.1297 = 4.83, above the registered 3.0 floor. The hs34 late-site direction-specificity claim, previously resting on one historical draw (effect ratio 14.5), survives a max-over-15 distributional denominator at a lower but still passing ratio: the gated write's effect is direction-specific against a null distribution of random directions, not just against one lucky (or unlucky) draw."
polarity: mediates
related:
- '[[qwen3-4b-l34-placebo-seed-census]]'
- '[[wide-instrument-control-rescore]]'
- '[[gated-controller-and-layer-site-controls-survive-wide-instrument]]'
relationships:
- type: supported_by
  target: '[[qwen3-4b-l34-placebo-seed-census]]'
  target_id: experiment:qwen3-4b-l34-placebo-seed-census
  confidence: high
  evidence:
  - experiments/qwen3-4b-l34-placebo-seed-census/AMENDMENT.md#outcome (QG-G1)
- type: related_to
  target: '[[wide-instrument-control-rescore]]'
  target_id: experiment:wide-instrument-control-rescore
  confidence: high
  evidence:
  - experiments/qwen3-4b-l34-placebo-seed-census/AMENDMENT.md (Motivation and
    posture; extends WG-G1's single-draw effect ratio 14.5 to a max-over-15
    distributional ratio 4.83 at the identical site, dose, rows, and
    instrument)
- type: related_to
  target: '[[gated-controller-and-layer-site-controls-survive-wide-instrument]]'
  target_id: mechanism:gated-controller-and-layer-site-controls-survive-wide-instrument
  confidence: medium
---

The lower distributional ratio (4.83 vs the single-draw 14.5) is expected,
not a weakening of the underlying finding: a max-over-15 denominator is
mechanically larger than any single draw's denominator, so a drop in the
reported ratio while still clearing the 3.0 floor is exactly what a genuine
specific effect surviving a harder null looks like. The late-site
specificity conclusion behind Paper 5 Sections 4.8 and 7 no longer rests on
one committed random-direction draw.
