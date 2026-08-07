---
title: grpo-three-seed-confirmatory
aliases:
- GRPO Three-Seed Confirmatory Block
- GRPO three-seed confirmatory / response-confidence track
tags:
- kg/experiment
- experiment
- response-confidence
kg:
  id: experiment:grpo-three-seed-confirmatory
  type: experiment
  status: canonical
related:
- '[[probe-scaled-response-confidence]]'
- '[[grpo-centered-stacking]]'
- '[[best-stack-replication-scale-gate]]'
- '[[selfaware]]'
- '[[grpo-abstention-shift-replicates-across-seeds]]'
- '[[post-grpo-preference-stage-recovers-over-refusal-without-reopening-unknown]]'
- '[[grpo-stage-ordering-effect-on-over-refusal-is-pairing-dependent]]'
- '[[selfaware-known-question-contamination-inflates-known-row-metrics]]'
- '[[filtered-denominator-accuracy-metric-reverses-sign-under-selective-refusal]]'
relationships:
- type: builds_on
  target: '[[probe-scaled-response-confidence]]'
  target_id: experiment:probe-scaled-response-confidence
  confidence: high
  evidence:
  - "experiments/grpo-three-seed-confirmatory/AMENDMENT.md Frozen inputs items 1-7 (output contract, probe-derived target, target mapping, v3 clean-SFT base, consumed as a frozen input without retro-signing Amendment E)"
- type: builds_on
  target: '[[grpo-centered-stacking]]'
  target_id: experiment:grpo-centered-stacking
  confidence: high
  evidence:
  - "experiments/grpo-three-seed-confirmatory/AMENDMENT.md Frozen inputs items 8-13 and Relationship to prior registrations, Amendment F (stage-3 stack definitions, frozen GRPO source variant, merge-first lineage validation; F's seed-2/3/8B/cloud exclusion lifted for the local 4B lineage only)"
- type: builds_on
  target: '[[best-stack-replication-scale-gate]]'
  target_id: experiment:best-stack-replication-scale-gate
  confidence: high
  evidence:
  - "experiments/grpo-three-seed-confirmatory/AMENDMENT.md Relationship to prior registrations, Amendment G (this block is a strict superset of G's seed-replication half, ruled superseded-before-signing at sign, 2026-07-31; G's 8B/publication half is untouched)"
- type: evaluates_on
  target: '[[selfaware]]'
  target_id: dataset:selfaware
  confidence: high
  evidence:
  - "experiments/grpo-three-seed-confirmatory/AMENDMENT.md Eval plan (full 3369-row SelfAware under the response-confidence contract for all eight cells per seed)"
- type: supports
  target: '[[grpo-abstention-shift-replicates-across-seeds]]'
  target_id: mechanism:grpo-abstention-shift-replicates-across-seeds
  confidence: high
  evidence:
  - "experiments/grpo-three-seed-confirmatory/NOTEBOOK.md G1 ADJUDICATED PASS entry"
- type: supports
  target: '[[post-grpo-preference-stage-recovers-over-refusal-without-reopening-unknown]]'
  target_id: mechanism:post-grpo-preference-stage-recovers-over-refusal-without-reopening-unknown
  confidence: high
  evidence:
  - "experiments/grpo-three-seed-confirmatory/NOTEBOOK.md G2 ADJUDICATED PASS entry"
- type: supports
  target: '[[grpo-stage-ordering-effect-on-over-refusal-is-pairing-dependent]]'
  target_id: mechanism:grpo-stage-ordering-effect-on-over-refusal-is-pairing-dependent
  confidence: high
  evidence:
  - "experiments/grpo-three-seed-confirmatory/NOTEBOOK.md RED-TEAM PASS Finding 2 (G5 delivered)"
- type: supports
  target: '[[selfaware-known-question-contamination-inflates-known-row-metrics]]'
  target_id: mechanism:selfaware-known-question-contamination-inflates-known-row-metrics
  confidence: high
  evidence:
  - "experiments/grpo-three-seed-confirmatory/NOTEBOOK.md RED-TEAM PASS Finding 1 (MAJOR, ACCEPTED)"
- type: supports
  target: '[[filtered-denominator-accuracy-metric-reverses-sign-under-selective-refusal]]'
  target_id: mechanism:filtered-denominator-accuracy-metric-reverses-sign-under-selective-refusal
  confidence: high
  evidence:
  - "experiments/grpo-three-seed-confirmatory/NOTEBOOK.md INSTRUMENT FINDING entry (correct_on_known_pct filtered-denominator audit)"
---

Tier-2 exploratory amendment, SIGNED 2026-07-31, resolved 2026-08-07. Rebuilds
the entire eight-arm clean response-confidence lineage (SFT to
{DPO, KTO, GRPO v2} to {DPO-then-GRPO, KTO-then-GRPO, GRPO-then-DPO,
GRPO-then-KTO}) at two fresh seeds (2 and 3) from the Qwen3-4B-bnb-4bit
foundation on the local RTX 3090 lane, so every GRPO-touching arm in paper 2's
response-confidence track carries a three-seed interval matching its DPO and
KTO siblings. Its numbers are exploratory response-confidence-track evidence,
never pooled with the PROTOCOL v0.3 plain-answer headline matrix.

**G1 PASS, both seeds (the falsifier gate).** The seed-1 GRPO abstention
shift replicates; see
[[grpo-abstention-shift-replicates-across-seeds]].

**G2 PASS, both seeds.** The post-GRPO preference-stage recovery replicates,
small and direction-only by design; see
[[post-grpo-preference-stage-recovers-over-refusal-without-reopening-unknown]].

**G3 delivered (descriptive, non-gating).** Mean and 95 percent seed-level
bootstrap intervals (n=3 support points, seeds 1/2/3) reported for all five
GRPO-touching arms on truthful, refusal recall, answer-on-unknown,
over-refusal, correct-on-known, and refusal rate. With only three support
points the interval is bounded by the seed min/max; it is a descriptive
spread summary, not an inferential confidence interval.

**G4 not triggered (descriptive guard).** Stated `response_confidence`
stayed collapsed and behavior-insensitive as pre-stated: distinct-value counts
ranged 4 to 85 across seed-2/3 arms, nowhere near the 200-value trigger
leg, even though the Brier leg alone was met on the two clean-SFT base arms.

**G5 delivered (secondary, descriptive, non-gating).** Stage-ordering effect
on over-refusal is pairing-dependent: robust for the KTO pairing, sign-reversing
for the DPO pairing; see
[[grpo-stage-ordering-effect-on-over-refusal-is-pairing-dependent]].

**Standing limitation.** 117 SelfAware known-question prompts appear verbatim
in every training dataset this block consumes; G1 is structurally immune and
G2 is stratum-robust, but absolute known-row metric levels are inflated and
must carry the caveat; see
[[selfaware-known-question-contamination-inflates-known-row-metrics]].

**Standing instrument caveat.** `correct_on_known_pct` is the sole
filtered-denominator metric among those reported here and reverses sign
under the full-population denominator when refusal rates differ across arms;
see
[[filtered-denominator-accuracy-metric-reverses-sign-under-selective-refusal]].

Source of truth: `experiments/grpo-three-seed-confirmatory/AMENDMENT.md`,
`gates.yaml`, `experiment.yaml`, and `NOTEBOOK.md`.
