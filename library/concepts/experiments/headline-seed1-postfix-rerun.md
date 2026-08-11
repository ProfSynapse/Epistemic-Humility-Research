---
title: headline-seed1-postfix-rerun
aliases:
- Headline DPO/KTO seed-1 rerun on post-fix dataset build
- postfix-rerun
tags:
- kg/experiment
- experiment
- abstention
kg:
  id: experiment:headline-seed1-postfix-rerun
  type: experiment
  status: canonical
related:
- '[[selfaware]]'
- '[[direct-preference-optimization]]'
- '[[kahneman-tversky-optimization]]'
- '[[dev-split-fix-dataset-confound-is-provenance-only]]'
- '[[dpo-trl-version-pin-shifts-truthful-and-known-accuracy]]'
relationships:
- type: evaluates_on
  target: '[[selfaware]]'
  target_id: dataset:selfaware
  confidence: high
  evidence:
  - "experiments/headline-seed1-postfix-rerun/AMENDMENT.md section 4 (both cells evaluated on the full SelfAware surface, 3369 rows, 1032 unknown / 2337 known, thinking disabled, temperature 0.0, generation seed 20240601)"
- type: uses
  target: '[[direct-preference-optimization]]'
  target_id: method:direct-preference-optimization
  confidence: high
  evidence:
  - "experiments/headline-seed1-postfix-rerun/AMENDMENT.md section 4 (dpo__4b__headline__seed1__postfix cell, learning rate 5.0e-06, beta 0.1 sigmoid, cold-start from unsloth/Qwen3-4B-bnb-4bit)"
- type: uses
  target: '[[kahneman-tversky-optimization]]'
  target_id: method:kahneman-tversky-optimization
  confidence: high
  evidence:
  - "experiments/headline-seed1-postfix-rerun/AMENDMENT.md section 4 (kto__4b__headline__seed1__postfix cell, learning rate 1.0e-06, beta 0.1, cold-start from unsloth/Qwen3-4B-bnb-4bit)"
- type: supports
  target: '[[dev-split-fix-dataset-confound-is-provenance-only]]'
  target_id: mechanism:dev-split-fix-dataset-confound-is-provenance-only
  confidence: high
  evidence:
  - "experiments/headline-seed1-postfix-rerun/experiment.yaml verdict field (G1 PASS, pair, section 10.5 rule)"
  - "experiments/headline-seed1-postfix-rerun/NOTEBOOK.md 2026-08-08 ~01:30Z RESOLVED entry"
- type: supports
  target: '[[dpo-trl-version-pin-shifts-truthful-and-known-accuracy]]'
  target_id: mechanism:dpo-trl-version-pin-shifts-truthful-and-known-accuracy
  confidence: high
  evidence:
  - "experiments/headline-seed1-postfix-rerun/NOTEBOOK.md 2026-08-07 ~12:55Z entry (retroactive G0 finding, DPO cell skipped setup.pip and trained on baked-in trl 0.23.1)"
  - "experiments/headline-seed1-postfix-rerun/NOTEBOOK.md 2026-08-08 ~00:55Z entry (r2 vs deviated-attempt comparison table)"
---

Tier-appropriate training-run experiment, SIGNED 2026-08-01, resolved 2026-08-08.
A provenance audit found that the locked PROTOCOL v0.3 headline seed-1 cells for
cold-start DPO and cold-start KTO at 4B had consumed a dataset build predating
the dev-split grouping fix (commit `3dc58e9b`, 2026-06-14), while the seed-2 and
seed-3 headline cells for the same two arms consumed the corrected build. The
three-seed headline interval for those two arms therefore mixed a dataset-version
change with the seed variation it was meant to isolate. This experiment reran
both seed-1 cells, training seed still 1, on the post-fix build already consumed
by seeds 2 and 3, at the cohort's trainer vintage `089fa9b7` (a second confound
found during drafting: the original seed-1 cells ran at different, earlier
synaptic-tuner commits than the cohort), then evaluated both on the same full
3369-row SelfAware surface used to produce the committed headline metrics.

**Per section 3, this experiment is exploratory provenance work.** The locked
PROTOCOL v0.3 headline matrix is unchanged by it: the original
`dpo__4b__headline__seed1` and `kto__4b__headline__seed1` cells remain the
locked headline record. Adopting the rerun numbers into the headline table
would require a new signed PROTOCOL revision with its own changelog, decided
separately by the user; nothing here should be read as that decision having
been made or as automatic on a gate PASS.

**G1 PASS (pair, section 10.5 decision rule).** Both cells of record land
inside all eight cohort-derived (seeds 2/3) replication bands: KTO
0.00/0.13/18.88/27.25 (refusal_recall/over_refusal/truthful/correct_on_known
pct) and DPO cell of record (the recipe-honoring r2 retrain)
0.10/0.17/13.86/19.97. The signed prediction is confirmed and the falsifier
did not fire: the dev-split-fix dataset confound is provenance-only; see
[[dev-split-fix-dataset-confound-is-provenance-only]]. The gate's own
power disclosure, stated at pre-registration, is that applying the same bands
to the original pre-fix seed-1 rows also passes 8 of 8 metric-arm
combinations, since both arms sit at the cohort's abstention floor; a PASS
here means no dataset-version effect is detectable at this instrument's
resolution, not that the dataset version demonstrably did not matter.

**Deviated DPO attempt and the trl pin.** The first DPO retrain launch
(executor-dispatched, ported the GRPO-chain launch pattern) skipped the
recipe-mandated `setup.pip` step and trained on the training image's baked-in
trl 0.23.1 instead of the recipe-pinned trl 0.22.2; this is a retroactive G0
environment-identity failure, not the cell of record. A recipe-honoring
relaunch (r2) cured it. Both attempts land inside the same G1 bands, but the
trl version measurably shifted `truthful_pct` and `correct_on_known_pct` by
2-4 percentage points; see
[[dpo-trl-version-pin-shifts-truthful-and-known-accuracy]]. The deviated
attempt's results stay on disk and in the record as corroborating context,
never pooled with the r2 cell of record.

**G0 PASS both cells of record**, at trainer vintage `089fa9b7` on the
post-fix builds (data sha, config identity, pinned container digest, clean
training completion, eval-surface identity). **G2 satisfied as ruled**: the
sign-time PI ruling accepted that pinning the cohort's trainer commit for
both arms removes both confounds at once but means the rerun is a
commensurability check against the cohort bands, not a single-variable
attribution of the dataset change alone.

Source of truth: `experiments/headline-seed1-postfix-rerun/AMENDMENT.md`,
`gates.yaml`, `experiment.yaml`, and `NOTEBOOK.md`.
