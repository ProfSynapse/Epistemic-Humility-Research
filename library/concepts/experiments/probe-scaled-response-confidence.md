---
title: probe-scaled-response-confidence
aliases:
- 'Protocol Amendment E: Probe-Scaled Response Confidence Targets'
- Amendment E
tags:
- kg/experiment
- experiment
- response-confidence
kg:
  id: experiment:probe-scaled-response-confidence
  type: experiment
  status: canonical
related:
- '[[contrastive-response-confidence-target-shaping]]'
- '[[grpo-three-seed-confirmatory]]'
relationships:
- type: related_to
  target: '[[contrastive-response-confidence-target-shaping]]'
  target_id: method:contrastive-response-confidence-target-shaping
  confidence: high
  evidence:
  - "experiments/probe-scaled-response-confidence/AMENDMENT.md section 3 (probe-derived target construction and the v1/v2/v3 target-shaping iterations)"
- type: built_on_by
  target: '[[grpo-three-seed-confirmatory]]'
  target_id: experiment:grpo-three-seed-confirmatory
  confidence: high
  evidence:
  - "experiments/grpo-three-seed-confirmatory/AMENDMENT.md Frozen inputs items 1-7 (output contract, probe-derived target, target mapping, v3 clean-SFT base row counts, consumed as a frozen input without retro-signing)"
---

Protocol Amendment E. Registers a probe-derived response-confidence target
scheme for the response-confidence track: a JSON output contract
`{"answer": ..., "response_confidence": 0.73}`, a Laplace-smoothed
probe-derived target `factual_p = (correct_samples + 1) / (n_samples + 2)`
over 32 stochastic samples, and a mapping `response_confidence = 0.1 + 0.8 *
response_appropriateness_p` into the non-endpoint range `[0.1, 0.9]`.
`response_confidence` is defined as response-appropriateness, not
answer-correctness, so a correct "I don't know" on a true unknown earns a high
target. Early (v1/v2) target-shaping iterations still collapsed to a dominant
scalar; the v3 clean-SFT projection (14,943 rows: 7,981 known answers, 6,414
unknown abstentions, 548 ambiguous-middle; 2,489 unique targets; range
`[0.3508, 0.90]`) is the base later downstream response-confidence work
consumes.

Status: DRAFT / NOT SIGNED. Verdict, from its own machine record: probe
scaling alone is insufficient (the scalar still collapsed under earlier
target-shaping iterations, a target-imbalance failure); the v3 clean-SFT
mainline was reserved for later contrast rather than treated as a fix. Later
work (Amendment F and
[[grpo-three-seed-confirmatory]]) consumes Amendment E's v3
clean-SFT projection and output-contract design as a **frozen input** without
retro-signing E itself; E remains exploratory and its own probe-scaling
question remains open. Source of truth:
`experiments/probe-scaled-response-confidence/AMENDMENT.md`.
