---
aliases:
- Unsloth optimized decode path never fires a registered forward hook
- bespoke gen_stream steering confound is instrumentation, not a causal null
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:unsloth-for-inference-decode-bypasses-steering-hook
  type: mechanism
  status: canonical
cause: "In h6-genstream-hook-firing-check (H6), registering a steering hook plus an independent read-only firing counter on a target module of an Unsloth `FastLanguageModel.for_inference` load of raw-base unsloth/Qwen3-4B, then generating via its optimized cached decode loop over a fixed 16-step answer window, on all 25 pinned smoke prompts."
effect: "The in-hook and independent counters agree at exactly 1 firing per sequence (the prefill call only); zero of the following 15 decode-step forward passes route through the hooked module, on 25 of 25 prompts. Downstream behavior is unaffected at a supra-threshold 2-sigma commanded write (0/25 argmax divergence from the hook-absent run), consistent with the write never reaching the model during decode. This certifies that the prior commitment-point (AK) Stage 2 answer-window gen_stream MISS, diagnosed from a 100%-byte-identical-across-alphas signature, was an instrumentation artifact of this bespoke harness path, not a causal null: no answer-window steering evidence produced on this path is admissible."
polarity: prevents
related:
- '[[h6-genstream-hook-firing-check]]'
- '[[cross-trajectory-readback-fails-after-intervention-diverges]]'
- '[[activation-steering]]'
relationships:
- type: supported_by
  target: '[[h6-genstream-hook-firing-check]]'
  target_id: experiment:h6-genstream-hook-firing-check
  confidence: high
  evidence:
  - experiments/h6-genstream-hook-firing-check/AMENDMENT.md#outcome
- type: related_to
  target: '[[cross-trajectory-readback-fails-after-intervention-diverges]]'
  target_id: mechanism:cross-trajectory-readback-fails-after-intervention-diverges
  confidence: medium
  evidence:
  - experiments/h6-genstream-hook-firing-check/AMENDMENT.md#outcome
- type: related_to
  target: '[[activation-steering]]'
  target_id: method:activation-steering
  confidence: medium
---

H6 is an instrument check, not a behavioral experiment: it decides whether a
harness that claims to steer during `generate()` decode actually does. The
bespoke path under test is the one that produced the commitment-point (AK)
Stage 2 answer-window result, whose raw rows carried a signature that was
never a plausible causal null (328/328 byte-identical across seven alphas,
while a single-token prefill push at the same per-step magnitude already
changed 24% of rows).

An independent firing counter and a read-only recording hook, registered
after the steering hook, settle it directly: on this Unsloth
`for_inference` load, the hooked module's `forward()` is called exactly once
per sequence, at prefill, and never again during the cached decode loop that
generates the remaining tokens. No per-step write can land, and none does;
behavior is identical to the hook-absent run on every tested prompt. The
prior answer-window MISS is therefore certified as an instrumentation
artifact of this harness path, and the AK Stage 2 answer-window arm is
instrument-void until a rerun on a path proven to fire per decode step (see
[[cross-trajectory-readback-fails-after-intervention-diverges]] for why the
alternative plain-HF path, though it fires correctly, is not yet certified
either).
