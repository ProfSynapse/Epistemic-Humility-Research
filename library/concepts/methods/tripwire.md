---
aliases:
- TripWire
tags:
- kg/method
- concept
- method
kg:
  id: method:tripwire
  type: method
  status: canonical
area: safety-alignment
related:
- '[[2608.14392--tripwire-triggering-aligned-refusal-statistically-certified-safety]]'
- '[[representation-engineering]]'
- '[[neuron-ablation]]'
- '[[linear-probe]]'
- '[[safety-neuron]]'
- '[[refusal-direction]]'
relationships:
- type: proposed_by
  target: '[[2608.14392--tripwire-triggering-aligned-refusal-statistically-certified-safety]]'
  target_id: paper:2608.14392
  confidence: high
- type: related_to
  target: '[[representation-engineering]]'
  target_id: method:representation-engineering
  confidence: medium
  note: "Compared as an inference-time baseline (RepE); TripWire reports lower ASR and utility cost."
- type: related_to
  target: '[[neuron-ablation]]'
  target_id: method:neuron-ablation
  confidence: medium
  note: "Contrasts with erasure-style neuron suppression, which zeroes/reverses toxic neurons rather than clamping safety neurons to a fixed trigger value."
- type: related_to
  target: '[[linear-probe]]'
  target_id: method:linear-probe
  confidence: high
  note: "Contrasts with probe-weight z-score neuron attribution, which TripWire's FDR-controlled funnel is shown to dominate."
- type: related_to
  target: '[[safety-neuron]]'
  target_id: term:safety-neuron
  confidence: high
- type: related_to
  target: '[[refusal-direction]]'
  target_id: term:refusal-direction
  confidence: medium
  note: "Operates at neuron granularity rather than a single global direction."
---

TripWire is a training-free, neuron-level jailbreak defense with two stages. First, a statistically rigorous identification funnel screens every neuron in the model with (i) direction filtering (mean harmful activation exceeds mean benign activation), (ii) a per-neuron Welch t-test corrected across all neurons with Benjamini-Hochberg false-discovery-rate control, and (iii) a utility-specificity filter that excludes neurons whose utility-task activation also lies close to the harmful end of the benign-to-harmful axis. Surviving candidates are ranked by AUROC and the top-N are selected as safety neurons. Second, a trigger-style clamp holds the selected neurons at their harmful-conditional mean activation throughout generation, injecting an internal "this input is harmful" signal that triggers the refusal behavior already learned during alignment rather than attempting to block every harmful-semantic pathway. The clamp is realized in two provably equivalent deployment modes: a detector-gated inference-time intervention (a lightweight logistic-regression classifier over the sparse safety-neuron feature vector decides whether to apply the clamp) and a permanent, detector-free offline bias-patch weight edit (zero the neuron's weight row, set its bias to the harmful-conditional mean).

**Why it matters here:** TripWire is a concrete instance of "read a state, then gate a write": a cheap, statistically controlled read of a harmful/known-unknown-adjacent state from a small neuron set (the detector-gated inference mode), followed by a targeted write (the clamp) that overwrites only the neurons carrying that signal. The identification funnel's explicit false-discovery-rate and utility-specificity controls, and the proven equivalence between the inference-time gate and a permanent weight edit, are directly relevant to designing a low-utility-cost gate for a known-unknown read that triggers a refusal write.

**Lineage:** contrasts with erasure-style toxic-neuron suppression (e.g. TraceRouter) and with probe-based safety-neuron attribution (e.g. NeuroStrike-style per-layer logistic-regression probes), which the paper shows requires 3-5x more neurons and costs far more utility because probe weights are not identifiable in the p >> n regime and cannot separate safety-specific from generally-important neurons.
