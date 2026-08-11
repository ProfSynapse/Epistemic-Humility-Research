# Headline DPO/KTO seed-1 rerun on post-fix dataset build

Status: **SIGNED 2026-08-01** (`bin/exp sign`, PI approval "Sign as drafted"
in session; pins recorded in `experiment.yaml`). Launch authorized once the
GPU frees after the GRPO three-seed chain; digest mismatch at launch is a
hard stop.

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
9. Trainer commit, RESOLVED by user/PI adjudication 2026-08-01 (section 10, item
   4): both cells pin synaptic-tuner commit `089fa9b7`, the commit used by
   cohort seeds 2 and 3, whose rows derive the G1 bands. The rerun is compared
   against the cohort, so it must match the cohort's trainer vintage; this
   fixes both the data-build confound and the trainer-vintage confound in one
   rerun. The original seed-1 commits are superseded vintages, not used in this
   rerun: DPO seed 1 ran at `3a3d7a26`, KTO seed 1 ran at `04005402`.

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

Proposed by lead 2026-08-01; APPROVED by PI 2026-08-01 ("Sign as drafted" in session). Mirrored in
`experiment.yaml:prediction`. This is proposed text, not a ratified prediction;
the PI can still change it at sign time.

Both rerun arms land inside all eight cohort-derived G1 bands, with both arms
remaining at the abstention floor observed across the cohort; the
dev-split-fix confound is provenance-only and headline conclusions are
unchanged.

## 8. Falsifier

Proposed by lead 2026-08-01; APPROVED by PI 2026-08-01 ("Sign as drafted" in session). Mirrored in
`experiment.yaml:falsifier`. This is proposed text, not a ratified falsifier;
the PI can still change it at sign time.

Any rerun metric outside its G1 band falsifies the provenance-only reading for
that arm; the affected pre-fix seed-1 row is retired as a comparator and
paper-2 numbers for that arm are recomputed from the rerun row, with the
published caveat escalated accordingly.

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

Items 1-4 RESOLVED 2026-08-01. Item 5 proposed 2026-08-01 and APPROVED by PI
2026-08-01 ("Sign as drafted" in session). The section 7/8 prediction and
falsifier were likewise proposed by lead and APPROVED by PI 2026-08-01 in the
same sign-off.

1. **The headline eval config was never committed.** RESOLVED, ruled by lead,
   2026-08-01. The eval that produced the locked seed-1/2/3 headline metrics
   ran from `.tmp/eval_selfaware_full_seed1_all_arms_4b.yaml`, whose own header
   calls it "Disposable ... Not a headline/protocol aggregation artifact", and
   `.tmp/` is gitignored (`.gitignore:10`). The committed
   `archive/experiment/phase1/eval/config/eval_selfaware_full_local_4b.yaml` is a
   different, earlier config covering base/SFT/DPO only. This rerun's eval
   config is now committed at
   `experiments/headline-seed1-postfix-rerun/configs/eval_selfaware_full_seed1_rerun_4b.yaml`,
   modeled structurally on the disposable `.tmp/` config but scoped to only the
   two rerun arms, with adapter paths left as clearly-marked placeholders to be
   filled once the rerun adapters exist. Same eval dataset reference and
   scoring settings as the original. `cell.yaml:eval.config_target` points at
   this file.
2. **Container pin or re-pull.** RESOLVED, ruled by lead, 2026-08-01. Pin
   `sha256:f21629b9ae4ed11231768edfaed0f40d41d85d6ea9a71e8096a3d96ea0311772`, the
   phase-1 lane digest recorded in
   `.skills/experiment-runner/reference/local-runtime.md:82-86` (verified
   character for character against that file at resolution time). This is the
   same pinned container as the cohort-era lane and the currently running GRPO
   chain; a digest mismatch at launch is a hard stop, not a silent
   substitution. The originals recorded only the mutable tag
   `unsloth/unsloth:latest`; pinning the 2026-06-13 digest makes the rerun
   reproducible but not necessarily identical to the DPO seed-1 original, which
   ran 2026-06-11 and may have been served by an earlier pull. There is no
   record of the digest in force on 2026-06-11; this residual gap is accepted
   as part of the resolution.
3. **Beta is implicit.** RESOLVED, ruled by lead, 2026-08-01. Neither original
   materialized recipe writes `beta`; both relied on the trainer's shipped
   default, which PROTOCOL section 3.1a records as 0.1 for both arms. Lead
   verified at commit `089fa9b7` that DPO/KTO beta flows only from the config
   file (`Trainers/dpo/train_dpo.py` line 576, `Trainers/kto/train_kto.py` line
   729), with no hidden trainer default; a `--beta` CLI override exists but will
   not be used. Both cell configs now state `beta: 0.1` explicitly rather than
   relying on an implicit default, matching PROTOCOL 3.1a and the original
   materialized recipes' effective value.
4. **A second confound the brief did not mention.** RESOLVED, ruled by
   user/PI, 2026-08-01. The originals and the seeds-2/3 cohort were not run at
   the same tuner commit. From the run records: DPO seed 1 at submodule
   `3a3d7a26`, KTO seed 1 at `04005402`, and seeds 2 and 3 for both arms at
   `089fa9b7`. So the seed-1 cells differed from their cohort on the trainer
   axis as well as the dataset axis, and the two seed-1 cells differed from
   each other. Ruling: both cells pin `089fa9b7`, the cohort's commit. This
   removes both confounds and makes seed 1 fully commensurate with seeds 2 and
   3, at the cost of no longer attributing any observed change to the dataset
   alone; the rerun is a joint dataset-and-trainer-vintage replication, not a
   dataset-only isolation. See section 5, item 9.
5. **Whether a single out-of-band metric is a FAIL.** Proposed by lead
   2026-08-01, APPROVED by PI 2026-08-01 ("Sign as drafted" in session).
   Each cell adjudicates independently against its own
   four G1 bands. Both cells within bands: PASS for the pair (the pre-fix rows
   are confirmed as valid bounded comparators; the confound is provenance-only).
   Exactly one cell outside any band: PARTIAL (the failing arm's pre-fix
   seed-1 row is retired as a comparator; paper-2 numbers for that arm
   recompute from the rerun row; the published caveat escalates). Both cells
   outside any band: FAIL (same retirement applies to both arms). No pooling
   across arms in any of the three outcomes.

   **Governed revision 2026-08-05.** `gates.yaml`'s `g1_replication_band`
   `decision_rule` did not match this item: it counted METRICS within an arm
   (one metric out = PARTIAL for that arm, two or more = FAIL for that arm) and
   left the question open, calling it "a sign-time decision" that was never
   closed in that file. The two therefore disagreed on whether a single
   out-of-band metric puts a cell "outside". Found 2026-08-05 while correcting
   that file's stale sign-time metadata, surfaced rather than silently
   harmonized, and resolved by the PI the same day in favour of THIS text: a
   cell is outside when ANY ONE of its four metrics is outside its band.
   `gates.yaml` was revised to restate it and repinned (audit entry in
   `experiment.yaml` `instrument.repins`). Resolved BEFORE launch, so no rerun
   number informed the choice. Note this is the STRICTER reading and, given the
   narrow floor-driven bands described in `power_disclosure`, makes a PARTIAL
   comparatively easy to trigger on eval discreteness alone; that cost was
   accepted knowingly.

## Predictions scoreboard

| Predictor | Call |
|-----------|------|
| orchestrator | Joint prediction, recorded once in the manifest `prediction:` field at sign time: both rerun arms land inside all eight cohort-derived G1 bands, both remain at the cohort abstention floor, and the dev-split-fix confound is provenance-only. CONFIRMED at resolve. |
| user | See above; no separate user call was recorded for this cell. |

This table was backfilled from the manifest on 2026-08-08 (paper-4 review
pass); the sign tooling left the placeholders in place, the same bin/exp gap
recorded in `grpo-three-seed-confirmatory`.

## Outcome

Resolved 2026-08-08 (verdict stamped in `experiment.yaml`; full record in
`NOTEBOOK.md`). This section was back-filled 2026-08-08 during the paper-4
review pass; the resolve step had stamped the manifest but left this
placeholder in place, a bin/exp tooling gap already registered.

- G1 PASS under the section 10.5 pair rule: both rerun arms INSIDE all eight
  cohort-derived G1 bands. KTO arm 0.00 / 0.13 / 18.88 / 27.25; the DPO cell
  of record is the recipe-honoring r2 retrain at 0.10 / 0.17 / 13.86 / 19.97
  (466/2333). The falsifier (any metric outside its band) did not fire.
- G0 PASS for both cells at trainer vintage 089fa9b7 on the post-fix dataset
  builds. G2 satisfied as ruled: a commensurability check with both arms at
  the same trainer vintage, not a single-variable attribution.
- The first DPO attempt (setup.pip skipped, trl 0.23.1) is a recorded
  deviated attempt: inside bands, context only. Its 2-4 pp spread against the
  r2 cell shows the trl pin is behaviorally real.
- Per section 3, this experiment adopts nothing into the headline: it tests
  whether the locked seed-1 rows survive the corrected dataset build, and
  they do.

One-sentence verdict (as stamped in the manifest): the signed prediction is
CONFIRMED; the dev-split-fix dataset confound is provenance-only, both arms
stay at the cohort abstention floor, and headline conclusions are unchanged.
