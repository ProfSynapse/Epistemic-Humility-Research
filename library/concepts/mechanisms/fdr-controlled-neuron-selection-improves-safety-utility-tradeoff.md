---
aliases:
- FDR-controlled neuron funnel beats probe-based neuron attribution
- Statistical neuron screening dominates probe-based safety-neuron selection
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:fdr-controlled-neuron-selection-improves-safety-utility-tradeoff
  type: mechanism
  status: canonical
cause: "Selecting safety neurons via per-neuron Welch t-tests under Benjamini-Hochberg false-discovery-rate control plus a utility-specificity filter (rho <= 0.5), instead of via per-layer logistic-regression probe-weight z-score attribution"
effect: "Reaches comparable or lower attack success rate using 3-5x fewer neurons, with far less utility degradation and over-refusal: probe-based selection needs 3,589-17,234 neurons and degrades MT-Bench by up to 52.3% with over-refusal rates as high as 62.5%, versus 1,000-2,500 neurons and at most a 5.3% MT-Bench drop for the FDR-controlled funnel"
polarity: decreases
related:
- '[[2608.14392--tripwire-triggering-aligned-refusal-statistically-certified-safety]]'
- '[[tripwire]]'
- '[[linear-probe]]'
- '[[high-probe-accuracy-does-not-imply-causal-use]]'
- '[[safety-neuron]]'
relationships:
- type: supported_by
  target: '[[2608.14392--tripwire-triggering-aligned-refusal-statistically-certified-safety]]'
  target_id: paper:2608.14392
  confidence: high
- type: related_to
  target: '[[tripwire]]'
  target_id: method:tripwire
  confidence: high
- type: related_to
  target: '[[linear-probe]]'
  target_id: method:linear-probe
  confidence: high
- type: related_to
  target: '[[high-probe-accuracy-does-not-imply-causal-use]]'
  target_id: mechanism:high-probe-accuracy-does-not-imply-causal-use
  confidence: medium
  note: "Same underlying failure mode: probe weights are not identifiable in the p >> n regime, so high-weight neurons can be merely correlated with the label rather than causally specific to it."
- type: related_to
  target: '[[safety-neuron]]'
  target_id: term:safety-neuron
  confidence: high
---

TripWire's ablation study (Table 2) isolates the identification step by comparing its FDR-controlled funnel against probe-based selection (fitting a per-layer logistic-regression classifier and thresholding weight z-scores) under identical always-on clamping. Probe weights are not identifiable in the p >> n regime, so a high-weight neuron may be merely correlated with harmfulness rather than specific to it, and the screening does not separate safety-specific neurons from generally-important ones; the extra neurons the probe selects carry utility knowledge, and clamping them costs substantial utility for negligible additional safety gain. Explicit false-discovery-rate control plus a utility-specificity filter removes this confound directly.
