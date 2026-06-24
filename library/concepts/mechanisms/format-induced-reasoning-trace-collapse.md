---
aliases:
- format-dependent VR collapse
- empty-think vs no-think effect
- missing-reasoning representation effect
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:format-induced-reasoning-trace-collapse
  type: mechanism
  status: canonical
cause: "The format used to represent missing reasoning traces in fine-tuning data (empty-think: empty <think> block included; no-think: reasoning tags omitted entirely)"
effect: "Differential rates of valid reasoning rate (VR) collapse during fine-tuning, with model-default formats not reliably protective and non-default formats sometimes preserving substantially more valid reasoning"
polarity: mediates
related:
- '[[2605.21127--silent-reasoning-trace-suppression]]'
- '[[reasoning-trace-collapse]]'
- '[[valid-reasoning-rate]]'
- '[[supervised-finetuning]]'
- '[[instruction-tuning]]'
relationships:
- type: supported_by
  target: '[[2605.21127--silent-reasoning-trace-suppression]]'
  target_id: paper:2605.21127
  confidence: high
- type: related_to
  target: '[[reasoning-trace-collapse]]'
  target_id: term:reasoning-trace-collapse
  confidence: high
- type: related_to
  target: '[[valid-reasoning-rate]]'
  target_id: metric:valid-reasoning-rate
  confidence: high
- type: related_to
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
  confidence: high
- type: related_to
  target: '[[instruction-tuning]]'
  target_id: method:instruction-tuning
  confidence: high
---

When fine-tuning explicit reasoning models on data without reasoning traces, the choice of how to encode missing reasoning shapes whether VR collapses. Empty-think provides a structural signal that a reasoning block should exist but is empty; no-think removes the structural scaffold entirely. Llama-R1-8B retains 71% Chemistry VR under empty-think but collapses to 0% under no-think. Qwen3-8B is more stable under no-think than empty-think on some benchmarks. OLMo-3-7B preserves more GSM8K VR under empty-think (80%) vs. no-think (45%). Nemotron-7B is format-insensitive. Model-default formatting should be treated as an experimental variable, not an assumed safe choice.
