---
title: prompt-crossing-completion
aliases:
- Completing the prompt-condition crossing
- Gap 3 / Gap 1 prompt-crossing completion
tags:
- kg/experiment
- experiment
- abstention
kg:
  id: experiment:prompt-crossing-completion
  type: experiment
  status: canonical
related:
- '[[pstruct-internalization-seed-robustness]]'
- '[[prompt-vs-training-panel]]'
- '[[grpo-three-seed-confirmatory]]'
- '[[preference-stage-after-sft-partially-erodes-internalized-abstention]]'
- '[[only-sft-installs-abstention-in-weights]]'
- '[[selfaware]]'
- '[[context-invariance]]'
relationships:
- type: builds_on
  target: '[[pstruct-internalization-seed-robustness]]'
  target_id: experiment:pstruct-internalization-seed-robustness
  confidence: high
  evidence:
  - "experiments/prompt-crossing-completion/AMENDMENT.md Gates PC-G1 (each seq arm compared to its own seed's cold-SFT P-struct parent value 69.57/76.94/79.36, sourced from the panel and this seed-robustness cell; the 30% floor is the panel's frozen R3 value reused unchanged)"
- type: builds_on
  target: '[[prompt-vs-training-panel]]'
  target_id: experiment:prompt-vs-training-panel
  confidence: high
  evidence:
  - "experiments/prompt-crossing-completion/AMENDMENT.md Design (P-struct prompt byte-identical to the pinned panel configs; seed-1 cold-SFT parent value 69.57 originates here)"
- type: builds_on
  target: '[[grpo-three-seed-confirmatory]]'
  target_id: experiment:grpo-three-seed-confirmatory
  confidence: high
  evidence:
  - "experiments/prompt-crossing-completion/AMENDMENT.md#outcome Gap 1b (warmed plain-answer arms compared against clean-SFT merged 87.02 and SFT->GRPO v2 seed1 93.41, the governed response-confidence readings from the grpo-three-seed-confirmatory amendment's seed-1 table)"
- type: evaluates_on
  target: '[[selfaware]]'
  target_id: dataset:selfaware
  confidence: high
  evidence:
  - "experiments/prompt-crossing-completion/AMENDMENT.md Design (full SelfAware, n=3,369 per arm, eleven arms)"
- type: supports
  target: '[[preference-stage-after-sft-partially-erodes-internalized-abstention]]'
  target_id: mechanism:preference-stage-after-sft-partially-erodes-internalized-abstention
  confidence: high
  evidence:
  - "experiments/prompt-crossing-completion/AMENDMENT.md#outcome (PC-G1 applied verbatim to all six seq arms; falsifier NOT fired)"
- type: related_to
  target: '[[only-sft-installs-abstention-in-weights]]'
  target_id: mechanism:only-sft-installs-abstention-in-weights
  confidence: high
  evidence:
  - "extends the cold-start finding (DPO/KTO from scratch install nothing that survives instruction removal) to warmed sequential arms, which behave differently"
- type: related_to
  target: '[[context-invariance]]'
  target_id: term:context-invariance
  confidence: medium
---

Eval-only tier-2 exploratory cell, resolved 2026-08-16, closing two of three prompt-crossing gaps paper 2's Limitations section named (PI-authorized 2026-08-15; the third, instructed readings for cold DPO/KTO seeds 2/3, was assessed low-information and skipped). Eleven arms across three configs, instrument identical to the panel and seed-robustness cells (`run_eval.py`, vLLM, greedy, full SelfAware n=3,369 per arm).

**Gap 3** (six arms, `seq_sft_dpo`/`seq_sft_kto` seeds 1-3 under P-struct): tests whether a preference stage applied to an already-internalized SFT checkpoint preserves, erodes, or deepens the internalized abstention. PC-G0 passed on all 11 arms (full coverage, `config_sha` stamped, parse path recorded; lead-verified by independent recompute on three pivotal arms). PC-G1 (falsifier not fired): all six arms clear the 30% floor; see [[preference-stage-after-sft-partially-erodes-internalized-abstention]].

**Gap 1** (five arms: `cold_sft` seeds 1-3 under response-confidence, `clean_sft_merged` and `sft_grpo_v2_seed1` under plain-answer): makes paper 2 Section 4.5's instructed-vs-instruction-free comparison single-contract. Gap 1a cold-SFT response-confidence readings (85.66 / 90.21 / 90.60) land inside the predicted 85-95 band; the secondary at-or-above-plain-answer ordering holds at seeds 1-2 and breaks at seed 3 (90.60 < 92.34), reported as-is with no registered claim riding on it. Gap 1b warmed arms under plain-answer land within the predicted ~10pp of their governed response-confidence readings (clean-SFT merged 87.60 vs 87.02, +0.58pp; SFT->GRPO v2 seed1 96.22 vs 93.41, +2.81pp).

**Why it matters here:** the only cell in the program measuring what a preference stage does to internalized (not merely instructed) abstention, and it makes paper 2's contract comparisons single-contract in both directions.

**Lineage:** builds on [[prompt-vs-training-panel]] (seed-1 P-struct parent) and [[pstruct-internalization-seed-robustness]] (seed 2-3 parents, frozen R3 thresholds); Gap 1b comparators sourced from [[grpo-three-seed-confirmatory]]. Source of truth: `experiments/prompt-crossing-completion/AMENDMENT.md`, Outcome section, resolved 2026-08-16.
