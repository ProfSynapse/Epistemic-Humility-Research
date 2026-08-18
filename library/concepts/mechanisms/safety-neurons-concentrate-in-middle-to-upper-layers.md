---
aliases:
- Safety neurons cluster in middle-to-upper transformer layers
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:safety-neurons-concentrate-in-middle-to-upper-layers
  type: mechanism
  status: canonical
cause: "Statistically identifying [[safety-neuron|safety neurons]] (FDR-controlled Welch t-test plus utility-specificity filter) jointly across every layer of aligned LLMs (Llama-2-7B, Llama-3.1-8B, Qwen2.5-7B)"
effect: "Selected safety neurons concentrate in middle-to-upper layers (peaking around layers 12-16 for Llama-2/Llama-3.1, and layers 15-21 for Qwen2.5-7B) and are nearly absent in early layers"
polarity: enables
related:
- '[[2608.14392--tripwire-triggering-aligned-refusal-statistically-certified-safety]]'
- '[[safety-neuron]]'
- '[[knowledge-neurons-concentrated-upper-layers]]'
- '[[tripwire]]'
relationships:
- type: supported_by
  target: '[[2608.14392--tripwire-triggering-aligned-refusal-statistically-certified-safety]]'
  target_id: paper:2608.14392
  confidence: high
- type: related_to
  target: '[[safety-neuron]]'
  target_id: term:safety-neuron
  confidence: high
- type: related_to
  target: '[[knowledge-neurons-concentrated-upper-layers]]'
  target_id: mechanism:knowledge-neurons-concentrated-upper-layers
  confidence: medium
  note: "Same upper-layer concentration pattern reported for a different neuron population (factual knowledge neurons), consistent with early layers encoding low-level syntax and later layers encoding higher-level semantic/behavioral features."
- type: related_to
  target: '[[tripwire]]'
  target_id: method:tripwire
  confidence: high
---

TripWire's per-layer safety-neuron counts under the top-2500 budget (Figure 3) show a sharp onset around layers 8-14 followed by a peak in the middle layers and a gradual decline toward the final layers for Llama-2 and Llama-3.1, with the pattern shifted later (onset around layer 13, peak layers 15-21) for Qwen2.5-7B. The paper reads this as consistent with harm detection and refusal triggering being mediated by mid-to-high-level semantic and behavioral representations rather than surface-level token features.
