# Headline DPO/KTO seed-1 rerun on post-fix dataset build

Status: DRAFT (not signed; do not launch as confirmatory evidence).

This document is the prose home for the experiment. Machine state lives in
`experiment.yaml`, the matrix in `cell.yaml`, the thresholds in `gates.yaml`, and
none of it is duplicated here.

## 1. Question

Does the locked headline seed-1 result for cold-start DPO and cold-start KTO at
4B replicate when seed 1 is trained on the corrected dataset build that seeds 2
and 3 already consumed, so that the three-seed headline interval for these two
arms no longer mixes two dataset versions?

## 2. Motivation and posture

A provenance audit on 2026-08-01 found that the seed-1 DPO and seed-1 KTO
headline cells consumed a dataset build predating the dev-split grouping fix,
while seeds 2 and 3 consumed the corrected build. The three-seed interval
reported for each of those two arms therefore averages across a dataset-version
change as well as across training seeds.

Read from the records, not from memory:

- The fix is commit `3dc58e9bfc5bbe1ade318f698936236edcd2112e`, "Fix phase1 dev
  split grouping", 2026-06-14. It changed `split_dev` in
  `experiment/phase1/data/build_datasets.py` from a row-key shuffle to a shuffle
  over groups keyed by `norm_question(question)`, so duplicate TriviaQA source
  rows sharing identical prompt text can no longer be split across train and dev.
  The same commit added the "Dev split identity" bullet to PROTOCOL and recorded
  `dev_split_group_key` in the frozen-questions artifact.
- The seed-1 DPO cell consumed train sha `22669d2c8c0b19df...`; the seed-1 KTO
  cell consumed `4d79fa505f5ae424...`. Seeds 2 and 3 consumed
  `39e2ba8c9bc1b41e...` (DPO) and `9cb291ee45c8dd58...` (KTO), one shared build
  each. All six SHAs were byte-verified against the files still on disk under
  `synaptic-tuner/scratch/eh_staging/` on 2026-08-01.
- The SFT headline cells are NOT affected: all three SFT seeds record train sha
  `714577a8ce6d32ac...`, verified on disk. SFT seed 1 was launched
  2026-06-14T09:29:14Z, after the fix landed. Nothing about SFT is in scope here.
- The Amendment A SFT-warmed arms are out of scope for the same reason.

This experiment is exploratory provenance work, not a headline claim. It produces
evidence about whether the confound matters. It does not, by itself, change any
reported number.

## 3. Relationship to the locked matrix

This is a REGISTERED REPLACEMENT-CANDIDATE run.

The locked PROTOCOL v0.3 headline matrix is unchanged by this experiment. The
original `dpo__4b__headline__seed1` and `kto__4b__headline__seed1` cells remain
the locked headline record. This amendment produces evidence and pre-states the
comparison; it does not adopt anything and it does not authorize anything to be
swapped into a headline table.

Adopting the rerun numbers into the headline record would require a NEW signed
PROTOCOL revision with its own changelog and its own rationale, decided after
this evidence exists and by the user. Nothing in this document should be read as
that decision having been made, or as being automatic on a G1 PASS. The rerun
numbers are reported separately from the headline until such a revision exists,
and they are never pooled with the locked cells.

## 4. Design

Rerun exactly two cells, serially, on the local RTX 3090:

1. `dpo__4b__headline__seed1__postfix`
2. `kto__4b__headline__seed1__postfix`

Every hyperparameter is carried from the original seed-1 materialized recipes and
is enumerated in `cell.yaml`: batch size 2, gradient accumulation 4, one epoch,
LoRA r 32 / alpha 64 / dropout 0.05 over the seven attention and MLP projections,
`max_seq_length` 2048, 4-bit load, learning rate 5.0e-06 for DPO and 1.0e-06 for
KTO, on `unsloth/Qwen3-4B-bnb-4bit`. The TRAINING seed stays 1 in both cells:
this is a dataset-version replication, not a fresh-seed replication.

The single intended difference is the training file. Each cell consumes the
post-fix build already on disk (the file seeds 2 and 3 consumed), identified by
sha256 rather than by path, staged into its own staging directory.

Both cells are then evaluated on the full SelfAware surface (3369 rows, 1032
unknown / 2337 known) with thinking disabled, temperature 0.0, generation seed
20240601, matching the eval that produced the committed seed-1/2/3 headline rows,
so the rerun numbers land on the same measurement surface as the cohort they are
compared against.

What the fix actually did to the data, measured on 2026-08-01 rather than
assumed: for both arms the union of train and dev rows is a byte-identical set
across the two builds, so no row was added, removed, or edited. The fix
reassigned the train/dev boundary. For DPO, 1457 rows moved train to dev and 1460
moved dev to train; 10.14% of pre-fix train rows are absent from the post-fix
train file. For KTO, 2836 moved train to dev and 2915 moved dev to train; 10.15%
churn. This is consistent with a pure boundary reassignment carrying incidental
re-randomization, and it means the rerun changes which rows the model trains on
without introducing any content absent from the corpus.

## 5. Frozen inputs

1. Post-fix DPO train build, sha256
   `39e2ba8c9bc1b41ef1b7e797f80637c276ba150c97055962bbc4e2b550bd17b5` (dev
   `24a8a89281395e2449be158660b70c17e6d3b6c9c313fc2cbf99dbea9e3917da`), on disk at
   `synaptic-tuner/scratch/eh_staging/dpo__4b__headline__seed2/dpo_train.jsonl`.
2. Post-fix KTO train build, sha256
   `9cb291ee45c8dd5893b150abe033386127d0eedce9fa16faa2309e31a1a70e15` (dev
   `7965ee94fb6d2838753d6f278045eed1be871949c3e8cdf9a195b1fcd9c73bb2`), on disk at
   `synaptic-tuner/scratch/eh_staging/kto__4b__headline__seed2/kto_congruence_train.jsonl`.
3. Original seed-1 materialized recipes, the hyperparameter source of record:
   `archive/experiment/phase1/run_records/materialized_recipes/dpo__4b__headline__seed1.yaml`
   (recorded sha `c301df87c81dcbc4...`) and
   `.../kto__4b__headline__seed1.yaml` (recorded sha `c1b699af1b8d576b...`).
4. The churn measurement in section 4, reproducible from the two staged builds
   with `scripts/audit_data_provenance.py`.
5. Original seed-1 run records, the runtime and lineage source of record:
   `archive/experiment/phase1/run_records/dpo__4b__headline__seed1.json` and
   `.../kto__4b__headline__seed1.json`.
6. Post-fix cohort metrics, the G1 derivation source:
   `papers/paper-2-training-regimen/analysis/selfaware_seed_metrics.csv`.
7. Locked protocol: `archive/docs/protocols/phase1/PROTOCOL.md`, in particular the
   headline-only rule and the section 3.1a default-config table (DPO learning rate
   5e-6 / beta 0.1 sigmoid; KTO learning rate 1e-6 / beta 0.1).
8. Container digest
   `sha256:f21629b9ae4ed11231768edfaed0f40d41d85d6ea9a71e8096a3d96ea0311772`,
   recorded for the 2026-06-13 local `unsloth/unsloth:latest` pull in
   `.skills/experiment-runner/reference/local-runtime.md:82-86`. NOTE: this digest
   is NOT recorded in the `grpo-three-seed-confirmatory` experiment; that
   experiment's `cell.yaml:21` pins only the mutable tag `unsloth/unsloth:latest`.
   The runtime reference is the only place in the repo carrying the digest.
9. Trainer commit: DELIBERATELY NOT FROZEN HERE. See section 10, item 4.

## 6. Budget

Serial on the single RTX 3090, after the `grpo-three-seed-confirmatory` chain
releases the GPU (about 2.5 days from 2026-08-01).

- DPO training: about 1.19 h. From the original seed-1 run record, launched
  2026-06-12T01:14:29Z and completed 2026-06-12T02:25:45Z (1h11m16s).
- KTO training: about 5.80 h. From the original seed-1 run record, launched
  2026-06-13T19:13:37Z and completed 2026-06-14T01:01:18Z (5h47m41s); that
  record's own verification summary reports 5h43m4s for 3599/3599 steps.
- Eval: about 40 min per arm, roughly 1.33 h total. This figure is the
  orchestrator's estimate and is NOT verified from any record: the eval queue log
  `.tmp/full_selfaware_seed_eval_queue_20260615_2148.log` logs RUN_BEGIN with no
  matching RUN_END, so no measured per-arm eval wall clock exists.
- Total: about 8.3 h.

The brief that commissioned this draft cited about 1.3 h for DPO and about 6.5 h
for KTO from backfilled seed-2/3 run records. Those backfilled records are not
present on this branch: the seed-2 and seed-3 records readable here still carry
`"status": "launched"` with no `completed_at`, no adapter path, and
`"verified": false`. The figures above are therefore taken from the seed-1
records, which do carry completion timestamps. The two sets are close enough that
nothing in the plan changes, but the numbers should be refreshed from the
backfilled records once they land on main.

## 7. Prediction

<!-- INTENTIONALLY EMPTY. To be filled by PI and lead at sign time.
     `bin/exp sign` refuses to sign while `prediction:` is empty in
     experiment.yaml. Do not fill this from the drafter's expectations. -->

## 8. Falsifier

<!-- INTENTIONALLY EMPTY. To be filled by PI and lead at sign time.
     `bin/exp sign` refuses to sign while `falsifier:` is empty in
     experiment.yaml. -->

## 9. Gates

Full thresholds and their derivations are in `gates.yaml`, marked
`status: proposed` pending lead adjudication. In summary:

- **G0, stop-before-outcome.** Data sha matches the post-fix build and is not the
  superseded pre-fix sha; the rerun's materialized recipe differs from the
  original only in dataset and run-naming fields; the container resolves to the
  pinned digest; the trainer commit is the one pinned at sign time; training
  completes clean; the eval scores 3369 rows on the same surface as the cohort
  with a clean contamination scan. A G0 failure stops the cell before any metric
  is read.
- **G1, replication band.** For each arm, each of `refusal_recall`,
  `over_refusal`, `truthful`, and `correct_on_known` must land inside
  `[min(seed2, seed3) - tol, max(seed2, seed3) + tol]` with
  `tol = max(|seed2 - seed3|, 3 x one-question resolution)`.
- **G2, confound isolation.** A bookkeeping check that the rerun changed the
  dataset variable and nothing the lead did not explicitly pin.

Two things about G1 that the lead should weigh before signing, both stated here
before the run rather than discovered after it:

**The bare `[min, max]` rule the brief proposed is degenerate on this data.**
Both arms sit on the abstention floor. `refusal_recall` is exactly 0.00 at seed 2
AND seed 3 for both DPO and KTO, so a plain cohort band has zero width and would
fail on a single differently answered question out of 1032. The proposed `tol`
adds a three-question floor derived from the eval denominators (0.0969 pp per
question on the 1032-row unknown set, 0.0428 pp on the 2337-row known set, 0.0297
pp on the 3369-row full set) so that eval discreteness cannot masquerade as a
replication failure.

**G1 has low power, and the drafter is disclosing this at pre-registration rather
than post hoc.** Applying the proposed bands to the ORIGINAL pre-fix seed-1 rows,
the very rows suspected of contamination, passes 8 of 8 metric-arm combinations.
Because both arms are pinned at the floor there is very little dynamic range in
which a dataset effect could appear. A G1 PASS therefore means "no effect
detectable at this instrument's resolution", not "the dataset version
demonstrably did not matter". The defensible value of this rerun is provenance
hygiene, removing a known confound from the record, rather than a sensitive test
for one. If the lead wants a gate that could actually discriminate, that is a
design change to make at sign time, not after seeing the result.

## 10. Open questions for sign-time adjudication

1. **The headline eval config was never committed.** The eval that produced the
   locked seed-1/2/3 headline metrics ran from
   `.tmp/eval_selfaware_full_seed1_all_arms_4b.yaml`, whose own header calls it
   "Disposable ... Not a headline/protocol aggregation artifact", and `.tmp/` is
   gitignored (`.gitignore:10`). The committed
   `archive/experiment/phase1/eval/config/eval_selfaware_full_local_4b.yaml` is a
   different, earlier config covering base/SFT/DPO only. `cell.yaml` proposes
   writing this rerun's eval config into the experiment directory so the
   measurement surface is pinned by `exp sign`, but the lead should decide
   whether that is in scope here or a separate provenance repair.
2. **Container pin or re-pull.** The originals recorded only the mutable tag
   `unsloth/unsloth:latest`. Pinning the 2026-06-13 digest makes the rerun
   reproducible but not necessarily identical to the DPO seed-1 original, which
   ran 2026-06-11 and may have been served by an earlier pull. There is no record
   of the digest in force on 2026-06-11.
3. **Beta is implicit.** Neither materialized recipe writes `beta`; both rely on
   the trainer's shipped default, which PROTOCOL section 3.1a records as 0.1 for
   both arms. `cell.yaml` records `beta_expected: 0.1` so a trainer-default drift
   cannot change it silently, but the lead should confirm the pinned trainer
   commit still ships 0.1.
4. **A second confound the brief did not mention.** The originals and the
   seeds-2/3 cohort were not run at the same tuner commit. From the run records:
   DPO seed 1 at submodule `3a3d7a26`, KTO seed 1 at `04005402`, and seeds 2 and 3
   for both arms at `089fa9b7`. So the seed-1 cells differ from their cohort on
   the trainer axis as well as the dataset axis, and the two seed-1 cells differ
   from each other. Using `089fa9b7` removes both confounds and makes seed 1 fully
   commensurate with seeds 2 and 3, at the cost of no longer attributing any
   observed change to the dataset alone; using the original per-arm commit
   isolates the dataset variable but leaves seed 1 non-commensurate on the trainer
   axis. The drafter did not choose. This is a real design fork.
5. **Whether a single out-of-band metric is a FAIL.** `gates.yaml` proposes
   reporting it as PARTIAL and lifting to the lead; the alternative is to call the
   arm failed. Decide before signing.

## Predictions scoreboard

| Predictor | Call |
|-----------|------|
| orchestrator | |
| user | |

## Outcome

Filled at resolve. Record the verdict, the gate results, and the one-sentence
summary that also goes into `verdict:` in the manifest.
