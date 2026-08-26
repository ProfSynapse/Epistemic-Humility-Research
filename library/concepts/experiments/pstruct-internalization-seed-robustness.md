---
title: pstruct-internalization-seed-robustness
aliases:
- 'Instruction-free abstention internalization: seed robustness of the P-struct readout'
- P-struct seed-robustness cell
- internalization confirmatory replication
tags:
- kg/experiment
- experiment
- abstention
kg:
  id: experiment:pstruct-internalization-seed-robustness
  type: experiment
  status: canonical
related:
- '[[prompt-vs-training-panel]]'
- '[[only-sft-installs-abstention-in-weights]]'
- '[[context-invariance]]'
relationships:
- type: builds_on
  target: '[[prompt-vs-training-panel]]'
  target_id: experiment:prompt-vs-training-panel
  confidence: high
  evidence:
  - experiments/pstruct-internalization-seed-robustness/AMENDMENT.md
    (Motivation and posture; registered as the confirmatory replication FOR
    THE INTERNALIZATION CLAIM specifically, reusing the panel's R3 30/10
    thresholds unchanged)
- type: supports
  target: '[[only-sft-installs-abstention-in-weights]]'
  target_id: mechanism:only-sft-installs-abstention-in-weights
  confidence: high
  evidence:
  - experiments/pstruct-internalization-seed-robustness/AMENDMENT.md#outcome
    (SR-G1 PASS; all three SFT seeds 69.57/76.94/79.36 >= 30% floor, all six
    DPO/KTO arms read 0.00%)
- type: related_to
  target: '[[context-invariance]]'
  target_id: term:context-invariance
  confidence: medium
  evidence:
  - experiments/pstruct-internalization-seed-robustness/AMENDMENT.md#outcome
    (one-sentence verdict; internalized behavior stays stable across three
    seeds once the instruction is removed at inference time)
---

Tier-2 confirmatory replication, eval-only, six arms: the structure-only
P-struct readout from `prompt-vs-training-panel` re-measured across headline
seeds 2 and 3 for all three cold-start objectives (SFT, DPO, KTO), on the
same instrument and byte-identical P-struct prompt. Registered specifically
to promote the panel's single-seed R3 internalization finding (cold SFT
seed 1 retains 69.6% refusal recall with the instruction removed, while the
untrained base reads 0.0%) to a three-seed claim, per the program guardrail
against pooling an exploratory win without a registered replication.

Resolved 2026-08-14. SR-G0 passed on all six arms (full n=3,369 coverage,
config_sha stamped, parse path recorded). SR-G1 passed: all three cold-SFT
seeds clear the 30% internalization floor (69.57% / 76.94% / 79.36%) with
base+P-struct fixed at 0.00% (< 10% ceiling), and all four DPO/KTO arms
(seeds 2 and 3) read 0.00%, matching seed 1. Neither falsifier fired.

**Why it matters here:** this is the confirmatory arm that makes
"only SFT installs abstention in the weights" a three-seed claim in both
directions (positive for SFT, negative for DPO/KTO), rather than a
single-seed observation riding on `prompt-vs-training-panel` alone.

**Lineage:** builds on [[prompt-vs-training-panel]]; reuses its frozen R3
30%/10% thresholds unchanged. Source of truth:
`experiments/pstruct-internalization-seed-robustness/AMENDMENT.md`, Outcome
section, resolved 2026-08-14.
