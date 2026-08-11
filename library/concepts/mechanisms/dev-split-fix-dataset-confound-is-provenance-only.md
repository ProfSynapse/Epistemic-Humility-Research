---
title: dev-split-fix-dataset-confound-is-provenance-only
aliases:
- headline seed-1 DPO/KTO dataset-version confound has no detectable metric effect
- pre-fix vs post-fix dev-split build produces no headline SelfAware shift within instrument resolution
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:dev-split-fix-dataset-confound-is-provenance-only
  type: mechanism
  status: canonical
cause: "Retraining the locked PROTOCOL v0.3 headline seed-1 DPO and KTO cells (4B, cold-start from unsloth/Qwen3-4B-bnb-4bit) on the post-fix dataset build already consumed by the seed-2/seed-3 headline cohort - the build produced by the dev-split grouping fix, commit 3dc58e9bfc5bbe1ade318f698936236edcd2112e, which changed split_dev from a row-key shuffle to a shuffle over groups keyed by norm_question(question) so duplicate TriviaQA rows sharing identical prompt text can no longer be split across train and dev - in place of the pre-fix build the original seed-1 cells consumed, at the cohort's trainer vintage 089fa9b7 rather than the original per-arm vintages."
effect: "produces SelfAware metrics for both rerun arms that land inside all eight cohort-derived (seeds 2/3) G1 replication bands - refusal_recall, over_refusal, truthful, correct_on_known - with both arms remaining at the cohort's abstention floor (refusal_recall 0.00 or near it). The dev-split-fix dataset-version confound therefore explains no headline metric shift detectable at this instrument's resolution, and the pre-fix seed-1 rows are confirmed as valid bounded comparators rather than retired. The gate's own pre-registered power disclosure holds: applying the identical bands to the ORIGINAL pre-fix seed-1 rows also passes all 8 of 8 metric-arm combinations, so a PASS here is read as 'no effect detectable', not as 'the dataset version demonstrably did not matter' - the value of the rerun is provenance hygiene, not a sensitive discovery test."
polarity: prevents
related:
- '[[headline-seed1-postfix-rerun]]'
- '[[selfaware]]'
- '[[direct-preference-optimization]]'
- '[[kahneman-tversky-optimization]]'
relationships:
- type: supported_by
  target: '[[headline-seed1-postfix-rerun]]'
  target_id: experiment:headline-seed1-postfix-rerun
  confidence: high
  evidence:
  - "experiments/headline-seed1-postfix-rerun/experiment.yaml verdict field (G1 PASS pair, section 10.5 rule; both rerun arms INSIDE all eight cohort-derived G1 bands)"
  - "experiments/headline-seed1-postfix-rerun/gates.yaml g1_replication_band power_disclosure (bands applied to original pre-fix seed-1 rows pass 8 of 8 metric-arm combinations)"
  - "experiments/headline-seed1-postfix-rerun/NOTEBOOK.md 2026-08-08 ~01:30Z RESOLVED entry"
- type: related_to
  target: '[[selfaware]]'
  target_id: dataset:selfaware
  confidence: high
  evidence:
  - "experiments/headline-seed1-postfix-rerun/AMENDMENT.md section 4 (full 3369-row SelfAware surface, same measurement surface as the cohort rows in selfaware_seed_metrics.csv)"
- type: related_to
  target: '[[direct-preference-optimization]]'
  target_id: method:direct-preference-optimization
  confidence: high
  evidence:
  - "experiments/headline-seed1-postfix-rerun/NOTEBOOK.md 2026-08-08 ~00:55Z entry (DPO r2 arm INSIDE all four G1 bands)"
- type: related_to
  target: '[[kahneman-tversky-optimization]]'
  target_id: method:kahneman-tversky-optimization
  confidence: high
  evidence:
  - "experiments/headline-seed1-postfix-rerun/NOTEBOOK.md 2026-08-07 ~19:15Z entry (KTO arm INSIDE all four G1 bands)"
---

A provenance audit found that the locked PROTOCOL v0.3 headline seed-1 cells
for cold-start DPO and cold-start KTO at 4B consumed a dataset build predating
the dev-split grouping fix, while seeds 2 and 3 for the same arms consumed the
corrected build - so the three-seed headline interval mixed a dataset-version
change with the seed variation it was meant to isolate. The rebuild changed no
row content (the union of train and dev rows is byte-identical across builds
for both arms); it only reassigned which rows fall in train versus dev, moving
about 10 percent of rows across the boundary for each arm.

Rerunning seed 1 on the post-fix build at the cohort's trainer vintage
produced metrics inside all eight cohort-derived replication bands for both
arms, confirming the signed prediction and leaving the falsifier unfired.

**Why it matters here:** this closes the provenance question the audit
opened without changing any published number. Per the experiment's section 3,
the locked headline matrix is untouched; adopting the rerun numbers would
require a separate signed PROTOCOL revision. The result should be read
narrowly - both arms sit at the abstention floor with little dynamic range
for a dataset effect to appear in, so the honest claim is "no effect
detectable at this instrument's resolution", not a demonstration that the
dataset version could not matter.

**Lineage:** produced by [[headline-seed1-postfix-rerun]], a targeted
provenance rerun of the two affected PROTOCOL v0.3 headline seed-1 cells.
Distinct from the [[grpo-abstention-shift-replicates-across-seeds]] family of
findings, which belongs to the separate GRPO/response-confidence exploratory
track and is not related to this dataset-provenance question. Source of
truth: `experiments/headline-seed1-postfix-rerun/AMENDMENT.md` sections 2-4,
`gates.yaml` g1_replication_band, and `NOTEBOOK.md`, resolved 2026-08-08.
