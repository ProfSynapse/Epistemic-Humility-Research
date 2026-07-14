---
title: snap-seed-sampled-decode-replication
aliases:
- 'H3: Multi-Seed and Sampled-Decode Replication of the Doubt-Gated Caution Snap'
- H3 (paper 5 review memo hardening item)
tags:
- kg/experiment
- experiment
- doubt-snap
kg:
  id: experiment:snap-seed-sampled-decode-replication
  type: experiment
  status: canonical
related:
- '[[doubt-gated-caution-tighten]]'
- '[[sampled-decode-preserves-doubt-gated-caution-headline]]'
- '[[batched-termination-rule-misgrades-eos-at-final-position]]'
- '[[qwen35-batch-composition-flips-greedy-decode-outcomes]]'
- '[[activation-steering]]'
relationships:
- type: related_to
  target: '[[doubt-gated-caution-tighten]]'
  target_id: experiment:doubt-gated-caution-tighten
  confidence: high
  evidence:
  - experiments/snap-seed-sampled-decode-replication/AMENDMENT.md (Motivation and posture)
- type: supports
  target: '[[sampled-decode-preserves-doubt-gated-caution-headline]]'
  target_id: mechanism:sampled-decode-preserves-doubt-gated-caution-headline
  confidence: high
  evidence:
  - experiments/snap-seed-sampled-decode-replication/AMENDMENT.md#outcome
- type: supports
  target: '[[batched-termination-rule-misgrades-eos-at-final-position]]'
  target_id: mechanism:batched-termination-rule-misgrades-eos-at-final-position
  confidence: high
  evidence:
  - experiments/snap-seed-sampled-decode-replication/AMENDMENT.md#outcome (Instrument correction history)
- type: related_to
  target: '[[qwen35-batch-composition-flips-greedy-decode-outcomes]]'
  target_id: mechanism:qwen35-batch-composition-flips-greedy-decode-outcomes
  confidence: medium
- type: related_to
  target: '[[activation-steering]]'
  target_id: method:activation-steering
  confidence: medium
---

Registered exploratory replication (paper 5 review memo hardening item H3)
of the resolved doubt-gated-caution-tighten headline under fresh harness
seeds and the program's registered sampled-decode configuration, reusing
the frozen instrument (directions, gate threshold, standardization,
held-out split) verbatim, no refit.

Status: resolved, REVISED to resolved same day after a verified
instrument correction. The original K=5 run resolved FALSIFIED (pooled
majority-vote conversion 140/925 = 15.1% against the 63.5% floor), later
found to be an artifact of a batched termination-rule defect that misgraded
eos-at-final-position refusals as not-terminated
([[batched-termination-rule-misgrades-eos-at-final-position]]). After the
fix, the full K=5 re-run reproduced the greedy anchor exactly (H3-G0 PASS,
136/185 = 73.5%, 8/258 = 3.1%) and passed every gate on the sampled arm:
H3-G1 pooled majority-vote confab conversion 643/925 = 69.5%
(Wilson [66.5%, 72.4%]), above the 63.5% floor in all 5 seeds; H3-G2 pooled
known-correct cost 60/1290 = 4.65% (Wilson upper bound 5.9% < 12%); H3-G3
placebo margins held in all 5 seeds.

**Verdict: the falsifier does NOT fire. The resolved 73.5%/3.1% headline
survives temperature-0.7 sampled decoding**
([[sampled-decode-preserves-doubt-gated-caution-headline]]), closed by
diagnostic-replay, parity-recompute, and independent-rerun triple agreement
on the corrected termination rule. Source of truth:
`experiments/snap-seed-sampled-decode-replication/AMENDMENT.md`.
