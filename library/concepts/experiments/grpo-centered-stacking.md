---
title: grpo-centered-stacking
aliases:
- 'Protocol Amendment F: GRPO-Centered Three-Stage Stacking'
- Amendment F
tags:
- kg/experiment
- experiment
- response-confidence
kg:
  id: experiment:grpo-centered-stacking
  type: experiment
  status: canonical
related:
- '[[probe-scaled-response-confidence]]'
- '[[grpo-abstention-shift-replicates-across-seeds]]'
- '[[grpo-stage-ordering-effect-on-over-refusal-is-pairing-dependent]]'
relationships:
- type: builds_on
  target: '[[probe-scaled-response-confidence]]'
  target_id: experiment:probe-scaled-response-confidence
  confidence: high
  evidence:
  - "experiments/grpo-centered-stacking/AMENDMENT.md (three-stage stacking built on the Amendment E clean response-confidence lineage as a frozen input)"
- type: built_on_by
  target: '[[grpo-abstention-shift-replicates-across-seeds]]'
  target_id: mechanism:grpo-abstention-shift-replicates-across-seeds
  confidence: high
  evidence:
  - "experiments/grpo-three-seed-confirmatory/AMENDMENT.md Motivation and posture (seed-1 GRPO abstention shift is the effect the three-seed block replicates)"
- type: built_on_by
  target: '[[grpo-stage-ordering-effect-on-over-refusal-is-pairing-dependent]]'
  target_id: mechanism:grpo-stage-ordering-effect-on-over-refusal-is-pairing-dependent
  confidence: high
  evidence:
  - "experiments/grpo-three-seed-confirmatory/AMENDMENT.md:85-91 (Effect 3, the seed-1 stage-ordering observation this mechanism retests at three seeds)"
---

Protocol Amendment F, SIGNED 2026-06-24. Registers seed-1 three-stage
response-confidence stacking over the Amendment E clean SFT lineage: a
stage-2 GRPO arm (`clean_sft_grpo_v2`, the frozen GRPO source variant) plus
four stage-3 terminal stacks built from the merged stage-2 sources,
`clean_sft_dpo_grpo`, `clean_sft_kto_grpo`, `clean_sft_grpo_dpo`, and
`clean_sft_grpo_kto`. Found that GRPO is the only downstream path in this
lineage that materially shifts unknown-question abstention in the desired
direction (`clean_sft_grpo_v2` moves answer-on-unknown 12.98 to 6.59 pp
against its own same-seed base), at a cost of raised known-row over-refusal
(57.51 to 66.62 pp); and that a preference stage applied after GRPO
(`clean_sft_grpo_dpo`) partially recovers over-refusal (66.62 to 63.63 pp)
while unknown-answering holds essentially flat, the strongest seed-1 stack.
Descriptive stage-ordering observation ("Effect 3"): both GRPO-first-vs-last
matched pairs at seed 1 pointed the same direction (DPO pair -1.67 pp,
KTO pair -5.78 pp on over-refusal), registered as secondary and descriptive
because the DPO-pair margin was judged too small for a two-seed replication
to adjudicate.

F §8 excluded seeds 2/3, 8B, cloud lanes, bridge cells, and merged-model
publication "until seed-1 local results are interpretable." That exclusion
was lifted for seeds 2 and 3 of the local 4B lineage only by
[[grpo-three-seed-confirmatory]], which also found that F's Effect 3 prose
does not survive at three seeds for the DPO pair (see
[[grpo-stage-ordering-effect-on-over-refusal-is-pairing-dependent]]); F's
own seed-1 results and conclusions stand unchanged. Source of truth:
`experiments/grpo-centered-stacking/AMENDMENT.md`.
