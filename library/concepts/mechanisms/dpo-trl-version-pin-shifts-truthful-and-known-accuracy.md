---
title: dpo-trl-version-pin-shifts-truthful-and-known-accuracy
aliases:
- trl 0.22.2 vs trl 0.23.1 shifts DPO truthful/correct_on_known by 2-4pp without flipping the replication verdict
- skipping the recipe-mandated setup.pip step trains DPO on the wrong trl version
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:dpo-trl-version-pin-shifts-truthful-and-known-accuracy
  type: mechanism
  status: canonical
cause: "Training the DPO headline-seed1-postfix-rerun cell with the materialized recipe's mandated setup.pip step (trl==0.22.2 plus unsloth/unsloth_zoo git deps, executed before the trainer) versus a first, deviated launch attempt that skipped setup.pip - ported from the GRPO-chain launch pattern, which uses a direct --entrypoint python3 invocation with no pip preamble - and so trained on the training image's baked-in trl 0.23.1 instead. Both attempts used the identical staged post-fix dataset (sha256 39e2ba8c..., 14395 rows), the same trainer commit 089fa9b7, and byte-identical LoRA/training hyperparameters (seed 1, batch 2, grad-accum 4, LR 5.0e-06, beta 0.1, r32/alpha64/dropout 0.05)."
effect: "shifts truthful_pct from 16.62 (trl 0.23.1, deviated attempt) to 13.86 (trl 0.22.2, cell of record r2), and correct_on_known_pct from 23.99 to 19.97 - both roughly 2-4 percentage points - while refusal_recall_pct (0.00 to 0.10) and over_refusal_pct (0.13 to 0.17) move less than 0.1pp. Both attempts remain inside the same cohort-derived G1 replication bands (r2's correct_on_known_pct 19.97 lands near its band's lower edge, 19.48, but inside), so the trl pin is behaviorally real without being large enough to change the pair verdict. This retroactively confirms the DPO deviated attempt's setup.pip skip as a genuine G0 environment-identity failure - the rerun differed from the original in something other than the intended dataset-build variable - rather than a cosmetic launch-pattern difference."
polarity: mediates
related:
- '[[headline-seed1-postfix-rerun]]'
- '[[direct-preference-optimization]]'
- '[[dev-split-fix-dataset-confound-is-provenance-only]]'
relationships:
- type: supported_by
  target: '[[headline-seed1-postfix-rerun]]'
  target_id: experiment:headline-seed1-postfix-rerun
  confidence: high
  evidence:
  - "experiments/headline-seed1-postfix-rerun/NOTEBOOK.md 2026-08-07 ~12:55Z entry (RETROACTIVE G0 FINDING: the DPO cell skipped setup.pip, trained on baked-in trl 0.23.1 instead of recipe-pinned trl 0.22.2)"
  - "experiments/headline-seed1-postfix-rerun/NOTEBOOK.md 2026-08-08 ~00:55Z entry (G1, DPO r2 arm table: r2 rerun 0.10/0.17/13.86/19.97 vs deviated-attempt context 0.00/0.13/16.62/23.99)"
  - "experiments/headline-seed1-postfix-rerun/experiment.yaml verdict field ('the first DPO attempt ... is a recorded deviated attempt, inside bands, context only, and its 2-4 pp spread vs the r2 cell shows the trl pin is behaviorally real')"
- type: related_to
  target: '[[direct-preference-optimization]]'
  target_id: method:direct-preference-optimization
  confidence: high
  evidence:
  - "experiments/headline-seed1-postfix-rerun/NOTEBOOK.md 2026-08-07 ~12:55Z entry (all four materialized recipes, both originals and both postfix reruns, carry setup.pip: [trl==0.22.2, unsloth_zoo git, unsloth git])"
- type: related_to
  target: '[[dev-split-fix-dataset-confound-is-provenance-only]]'
  target_id: mechanism:dev-split-fix-dataset-confound-is-provenance-only
  confidence: medium
  evidence:
  - "experiments/headline-seed1-postfix-rerun/AMENDMENT.md section 10 item 4 and NOTEBOOK.md 2026-08-07 ~12:55Z entry (a second, environment-axis confound surfaced within the same rerun that was designed to isolate the dataset-version confound)"
---

While closing out the headline-seed1-postfix-rerun DPO cell, the lead found
that its first launch attempt had silently skipped the materialized recipe's
`setup.pip` step (a step every one of the four relevant recipes - both
originals and both postfix reruns - mandates: `trl==0.22.2` plus the
`unsloth`/`unsloth_zoo` git dependencies, run before the trainer). The
attempt instead trained on whatever trl version the pinned training image
ships baked in, 0.23.1. This was a genuine G0 environment-identity failure,
not a cosmetic difference: the rerun's whole purpose is isolating the
dataset-build variable, and this silently introduced a second, unintended
variable.

A recipe-honoring relaunch (r2) reran the identical cell with `setup.pip`
executed. Comparing the two attempts, which are otherwise identical in data,
seed, trainer commit, and hyperparameters, isolates the trl-version effect:
truthful and correct-on-known accuracy move 2-4 percentage points, while the
refusal-related metrics barely move. Both attempts still land inside the same
signed G1 bands, so the pin did not change the replication verdict - but it
was large enough to be worth catching rather than silently absorbed into the
deviated attempt's numbers.

**Why it matters here:** this is a rare same-cell, same-data, single-variable
comparison of a training-library patch version, and it demonstrates the
environment pin is not mere reproducibility hygiene - it has a measurable
behavioral footprint on this task. It also validates the G0 gate's design:
catching an unpinned environment difference before treating a result as
clean.

**Lineage:** discovered mid-close-out inside [[headline-seed1-postfix-rerun]],
distinct from but co-located with that experiment's primary question, which
[[dev-split-fix-dataset-confound-is-provenance-only]] answers. Source of
truth: `experiments/headline-seed1-postfix-rerun/NOTEBOOK.md`, entries
2026-08-07 ~12:55Z and 2026-08-08 ~00:55Z, and `experiment.yaml`'s verdict
field, resolved 2026-08-08.
