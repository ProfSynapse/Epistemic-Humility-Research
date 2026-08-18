---
aliases:
- safety-specific neuron
- safety neurons
tags:
- kg/term
- concept
- term
kg:
  id: term:safety-neuron
  type: term
  status: canonical
area: terms
related:
- '[[2608.14392--tripwire-triggering-aligned-refusal-statistically-certified-safety]]'
- '[[safety-refusal]]'
- '[[knowledge-neurons]]'
- '[[refusal-direction]]'
relationships:
- type: studied_by
  target: '[[2608.14392--tripwire-triggering-aligned-refusal-statistically-certified-safety]]'
  target_id: paper:2608.14392
  confidence: high
- type: related_to
  target: '[[safety-refusal]]'
  target_id: term:safety-refusal
  confidence: high
- type: different_from
  target: '[[knowledge-neurons]]'
  target_id: term:knowledge-neurons
  confidence: medium
- type: related_to
  target: '[[refusal-direction]]'
  target_id: term:refusal-direction
  confidence: medium
  note: "Neuron-level analogue of the direction-level refusal-mediating construct."
---

A safety neuron is a neuron (in the gated MLP up- or gate-projection of a decoder-only Transformer) that plays a dual causal role in an aligned model's jailbreak resistance: a detection role, activating selectively on harmful input, and a refusal role, whose sustained activation triggers the downstream computation that produces an explicit refusal. Prior work shows that pruning a small fraction (<0.6%) of a layer's neurons suffices to break safety alignment, motivating the search for a compact, causally-specific safety-neuron set rather than treating harmful semantics as diffusely encoded.

**Why it matters here:** Safety neurons are the concrete substrate TripWire reads (via a sparse feature over the selected set) and writes (via the trigger-style clamp) to gate refusal; the same read-then-gate-write shape generalizes to reading any narrow known-unknown-adjacent signal and using it to gate a refusal or abstention write.

**Lineage:** distinguished from generic knowledge neurons (which encode factual associations rather than harm detection); the neuron-level counterpart of the [[refusal-direction]] literature, which localizes refusal to a single residual-stream direction rather than a discrete neuron set.
