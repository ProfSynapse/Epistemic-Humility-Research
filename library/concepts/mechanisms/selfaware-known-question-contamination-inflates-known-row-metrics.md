---
aliases:
- SelfAware known-question training contamination
- response-confidence lineage SelfAware leakage
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:selfaware-known-question-contamination-inflates-known-row-metrics
  type: mechanism
  status: canonical
cause: "128 distinct SelfAware known (answerable) evaluation questions leak into the response-confidence training pipeline: 117 appear verbatim as user-side prompts in all four gradient-training datasets (SFT/DPO/KTO/GRPO train, set-identical across files) and a disjoint 11 appear only in the GRPO dev split (checkpoint-selection exposure, not gradient exposure); the pre-registered leakage guard checks question disjointness against the Cheng TriviaQA test set only and was never extended to SelfAware"
effect: "absolute levels of over_refusal_pct, correct_on_known_pct, and truthful_pct on known rows are inflated by the memorized ~5 percent of the known population (contaminated-stratum over-refusal roughly 30 percent versus roughly 71 percent on the clean stratum), while metrics computed only over the 1032 unknown-labeled rows are structurally unaffected and within-lineage deltas remain stratum-robust"
polarity: increases
related:
- '[[grpo-three-seed-confirmatory]]'
- '[[selfaware]]'
- '[[grpo-abstention-shift-replicates-across-seeds]]'
- '[[post-grpo-preference-stage-recovers-over-refusal-without-reopening-unknown]]'
relationships:
- type: supported_by
  target: '[[grpo-three-seed-confirmatory]]'
  target_id: experiment:grpo-three-seed-confirmatory
  confidence: high
  evidence:
  - "experiments/grpo-three-seed-confirmatory/NOTEBOOK.md RED-TEAM PASS FINDING 1 (MAJOR, ACCEPTED); 117 exact-match distinct questions against DPO train prompts, all label known, zero unknown"
  - "experiments/grpo-three-seed-confirmatory/NOTEBOOK.md clean-subset sensitivity addendum 2026-08-07: full-union accounting 128 distinct/128 rows (117 train + 11 grpo_dev-only), corrected DPO-slice row count 117 (not 118); all gate-shaped deltas, the G5 sign patterns, and every unknown-row metric are unchanged on the decontaminated n=3241 population (script: experiments/grpo-three-seed-confirmatory/analysis/clean_subset_sensitivity.py)"
- type: related_to
  target: '[[selfaware]]'
  target_id: dataset:selfaware
  confidence: high
  evidence:
  - "library/concepts/datasets/selfaware.md (1032 unanswerable / 2337 answerable SelfAware questions; the contaminated rows are drawn from the answerable/known partition only)"
- type: related_to
  target: '[[grpo-abstention-shift-replicates-across-seeds]]'
  target_id: mechanism:grpo-abstention-shift-replicates-across-seeds
  confidence: high
  evidence:
  - "experiments/grpo-three-seed-confirmatory/NOTEBOOK.md RED-TEAM PASS FINDING 1 (G1 is structurally immune: both G1 metrics compute over the unknown-labeled rows only, scorers.py:281-284, and zero unknown questions leak)"
- type: related_to
  target: '[[post-grpo-preference-stage-recovers-over-refusal-without-reopening-unknown]]'
  target_id: mechanism:post-grpo-preference-stage-recovers-over-refusal-without-reopening-unknown
  confidence: high
  evidence:
  - "experiments/grpo-three-seed-confirmatory/NOTEBOOK.md RED-TEAM PASS FINDING 1 (G2 survives stratification: seed 3 contaminated stratum -1.70 pp vs clean stratum -1.85 pp; seed 2 reviewer stratification -0.85 pp vs -0.77 pp, uniform across strata)"
---

Standing limitation on the whole `grpo-three-seed-confirmatory` block,
adjudicated MAJOR and ACCEPTED at the red-team pass. The contamination is
behaviorally active, not inert: the contaminated stratum shows markedly lower
over-refusal than the clean stratum, so it is measurably easier for the model.
Gate impact was verified rather than assumed: G1's two metrics are computed
over unknown-labeled rows only, so the falsifier gate is structurally immune;
G2's recovery effect was re-derived per stratum and found uniform, so the
delta-level finding survives even though absolute known-row levels do not.
Consequence: any absolute (non-delta) figure for `over_refusal_pct`,
`correct_on_known_pct`, or `truthful_pct` on known rows must carry this
caveat in paper 2. Follow-up item registered alongside this finding: extend
the leakage guard to assert normalized-question disjointness against
SelfAware before any future block trains on these datasets.
