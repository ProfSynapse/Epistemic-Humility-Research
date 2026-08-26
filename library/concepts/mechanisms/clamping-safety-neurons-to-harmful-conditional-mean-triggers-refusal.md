---
aliases:
- Trigger-style clamp triggers aligned refusal
- Safety-neuron clamping triggers refusal
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:clamping-safety-neurons-to-harmful-conditional-mean-triggers-refusal
  type: mechanism
  status: canonical
cause: "Clamping a small, statistically identified set of [[safety-neuron|safety neurons]] to their harmful-conditional mean activation throughout generation, via [[tripwire]]'s trigger-style clamp"
effect: "The model reliably produces refusal output even under adversarial jailbreak prompts (GCG, AmpleGCG, AutoDAN, Jailbreak-R1), because the clamp injects a stable internal 'this input is harmful' signal that triggers the refusal behavior already learned during alignment, without needing to intercept every harmful-semantic pathway"
polarity: causes
related:
- '[[2608.14392--tripwire-triggering-aligned-refusal-statistically-certified-safety]]'
- '[[tripwire]]'
- '[[safety-neuron]]'
- '[[safety-refusal]]'
- '[[feature-activation-clamping-controls-behavior]]'
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
  target: '[[safety-neuron]]'
  target_id: term:safety-neuron
  confidence: high
- type: related_to
  target: '[[safety-refusal]]'
  target_id: term:safety-refusal
  confidence: high
- type: related_to
  target: '[[feature-activation-clamping-controls-behavior]]'
  target_id: mechanism:feature-activation-clamping-controls-behavior
  confidence: medium
  note: "Same clamp-to-fixed-value paradigm, applied here to neurons rather than SAE features and specifically to force a refusal output."
---

Across four safety-aligned LLMs (Llama-2-7B, Llama-3.1-8B, Qwen2.5-7B, Qwen2.5-32B), holding the identified safety-neuron set at its harmful-conditional mean activation reduces average attack success rate to at most 2.0%, compared with 8.3%-12.6% for RepE and 2.2%-4.9% for erasure-style or weight-editing baselines (TraceRouter, DELMAN, LED). Because the clamp overwrites activations directly, an adversarial prompt cannot suppress the injected signal, and because triggering refusal requires only a stable detection signal rather than blocking every route harmful semantics could take, a small (top-1000 to top-2500) neuron set suffices and the defense does not need to be attack-specific.
