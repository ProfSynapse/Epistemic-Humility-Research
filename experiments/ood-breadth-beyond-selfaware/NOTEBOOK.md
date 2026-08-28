# ood-breadth-beyond-selfaware notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

### 2026-08-11 -- Bookkeeping: Outcome section backfilled from the recorded verdict

**Tier 3, bookkeeping only, no goalpost implications.** The `## Outcome`
section of `AMENDMENT.md` still held the unfilled "Filled at resolve"
placeholder despite `experiment.yaml` reading `status: resolved` with a verdict
on record. Backfilled in a PI-approved governed pass from the recorded verdict
line, the 2026-08-09T16:45Z stage-8 adjudication entry below, and the committed
artifacts (`screen_summary.json`, `analysis-committed/gate_report.json`,
`analysis-committed/evidential_report_fivearm.json`,
`analysis-committed/g7_A1.json`, `analysis-committed/g7_A4.json`). Every gate
number in the new prose was re-read from those files; the behavior levels and
the descriptive five-arm Spearman, which exist only in the adjudication entry
and not in any committed artifact, are labelled as such in the Outcome. Two
things were recorded as "not recorded" rather than resolved: the bulleted P4
(answer-supervision dissociation) is not scored anywhere in the adjudication
record, and the Prediction section's bullets do not map one-to-one onto the four
scored components. NO ADJUDICATION WAS PERFORMED: no verdict, gate, band,
threshold, prediction, falsifier or status was changed, and no number was
recomputed. The header's "Outcome placeholder still unfilled" flag was updated
to record the backfill.

### 2026-08-11 -- Bookkeeping: AMENDMENT.md header corrected to match machine state

**Tier 3, bookkeeping only, no goalpost implications.** `AMENDMENT.md`'s header claimed a draft/not-signed (or otherwise stale) status that contradicted `experiment.yaml`'s machine state (`status: resolved`), which has read verdict "falsifier not fired, G7 readout non-transfer" on record. Corrected the AMENDMENT.md header ("Status:" line) to match the machine state. Also flagged (not fixed, no scientific content authored): this document's own "Outcome" section is still the unfilled placeholder text despite the machine state showing resolved with a verdict on record. Follows the precedent set by `gemma-4-e4b-family-atlas/AMENDMENT.md`'s 2026-07-20 header correction. No signed content (question, prediction, falsifier, gates, Outcome) touched.

### 2026-08-08 registration drafted, pre-sign feasibility probe run

Governed files filled from the reviewed design draft
(`docs/preparation/amendment-draft-ood-breadth.md`) with the PI-adjudicated
decisions applied. Status stays `draft`; `bin/exp sign` is lead-only and has not
been run. Nothing committed, nothing launched.

**Pre-sign feasibility probe (read-only, membership only, no outcome touched).**
Required by `.skills/experiment-runner/reference/amendment-vs-lab-notebook.md`,
"Pre-sign feasibility probe: every arm must be constructible from real data".
Run against the canonical checkout at `53f0ba3f203f585f4ae5402753f93f15b7117fff`.
The reference explicitly permits and requires this under a self-blinding rule:
confirming an arm can be built is not computing its result.

Measured, all now frozen in `cell.yaml`:

- Training-pool union across the eight lineage files: 15,465 distinct user
  prompts. Per-file counts in `cell.yaml` under `screens.training_pool_union`.
- KUQ: 3437 unknown and 3447 known raw. Known side loses 10 duplicates, **169
  verbatim training-pool hits**, and 197 SelfAware overlaps, retaining 3071.
  Unknown side loses 955 duplicates, **zero training hits**, and 13 SelfAware
  overlaps, retaining 2469. Total retained 5540.
- KUQ known-side source breakdown, which explains the 169: squad 1928,
  triviaqa 854, hotpotqa 665 raw. Paper 3 trains on TriviaQA-RC.
- KUQ against SelfAware: **220 shared questions** (207 known, 13 unknown). The
  ordered screen attributes 197 known plus 13 unknown to the SelfAware step
  because 10 of the 207 were already removed upstream. Both figures recorded.
- AmbigQA validation: 1002 pure-multipleQAs and 830 pure-singleAnswer with
  non-empty gold, zero drops on every screen. 170 mixed-annotation rows excluded
  by rule. Known-side gold alias median 3.
- AmbigQA train (internal-panel top-up source): 4739 unknown and 5286 known
  available after screening, against 501 and 415 needed. One training-pool hit
  exists in the train split and is screened out; the validation split has none.
- BIG-bench known-unknowns: 23 Unknown-gold and 23 knowable, zero drops.
- PAR mining pool (10,759 distinct questions), non-binding for these arms:
  1002/1002 AmbigQA unknown, 23/23 BIG-bench unknown, 627 KUQ unknown and 44 KUQ
  known are present in it. Recorded as the standing disqualification for any
  PAR-trained checkpoint.
- Internal panel constructibility confirmed: 2748 rows (1503 unknown, 1245
  known) as 1832 validation plus a 916-row deterministic train top-up. Top-up
  id-list sha256 `76a8a7384727958cd78098b27fce1ddc0dbd6a5b515ca46a42fcb2b4d4998580`.
  Note for the analyst: the top-up known rows have a gold alias median of 1
  against the validation split's 3. This does not affect the internal panel,
  whose label is dataset answerability rather than correctness, and the top-up
  rows are not part of the behavior or stated-calibration surface.

**Blocking prerequisite found and gated, not worked around.** The
answer-supervised merged base at
`scratch/schema_response_confidence/runs/sft_schema_contrastive_seed1_full/20260627_203232/Qwen3-4B-bnb-4bit/`
is an empty directory; the `merged-16bit/` weights are gone. The LoRA adapter
survives at `.../20260627_203232/final_model/` (adapter_model.safetensors,
252.1 MB, plus adapter_config.json and training_args.bin). Verified by listing
both paths. Arms A2, A6 and A7 depend on it. Registered as gate G1 (re-merge,
then reproduce A2's committed SelfAware metrics within 0.10 pp or void the three
arms).

**Harness gap recorded, not fixed.** `ood.py` lines 20-22 claim `run_eval.py`
asserts training/OOD disjointness as a section 6.5 defensive check. Grepping
`run_eval.py` for `norm_question`, `train_questions`, `overlap` and `contamin`
returns only an unrelated thinking-token message at line 172. The assertion does
not exist. Follow-up F1 in `cell.yaml`; this cell does not depend on it.

**Execution-location constraint.** `datasets/ambigqa/` and
`datasets/bigbench-known-unknowns/` are gitignored in full (`.gitignore` lines 75
and 76), dataset cards included, so neither exists in this worktree. Confirmed by
`git check-ignore -v` and by their absence from the worktree checkout. The screen
and the eval both run from the canonical checkout; the four affected files are
pinned by sha256 in `cell.yaml` and verified by G0 instead of by `bin/exp sign`.

**Open for the lead at sign time.** The eight arm configs,
`screen_ood_surfaces.py`, and the `ood.py` loader diff do not exist yet, so they
are not listed under `experiment.yaml` `instrument.modules`. They must be created
and added to the pin set before stage 0 runs. Signing now would pin `cell.yaml`
and `gates.yaml` only.

Nothing in this entry is a result. No generation has been run and no gate has
been read.

## 2026-08-09T00:50Z Harness build accepted; lead hand-pin of the build modules (audit entry)

Harness build delivered by the build agent and verified by the lead: all
reported sha256s reproduced on disk, `cell.yaml` and `gates.yaml` byte-identical
to their manifest pins, `AMENDMENT.md` untouched, `ood.py` diff purely additive
(95 insertions, 0 deletions, pre-change sha e747f232 matching the
`frozen_inputs.instrument_pre_change` record). G0 screen reproduced every
registered `expected_drop_counts` value exactly; dataset sha verification 6/6.

**Hand-pin.** `bin/exp sign` refuses non-draft experiments and `bin/exp repin`
refuses files not already in `instrument.pins`, so there is no CLI path to add
the new modules to this signed manifest (third recorded occurrence of this
tooling gap, after wrong-answer-cell-power-fix twice). Per `cell.yaml`
`configs.pin_requirement`, the lead hand-added to `instrument.modules` and
`instrument.pins`: the three experiment-local scripts
(`screen_ood_surfaces.py`, `gate_score.py`, `internal_panel_probe_gate.py`),
the two extraction recipes (`extract_A1.yaml`, `extract_A4.yaml`), the shared
render module
(`experiments/common/renders/ood_breadth_response_confidence_render.py`), the
post-change `archive/experiment/phase1/eval/ood.py` (cfd6cf8b, as the
registration's D2 note directs), and the eight
`eval_ood_breadth_*` arm configs. Persistence declared short-run for the three
scripts (measured wall-clocks below); config files and the import-only render
module carry no persistence entry, matching the wrong-answer-cell-power-fix
precedent that only executable modules are declared.

**Ordering repair.** The build agent ran the G0 screen before the modules were
pinned (the pin_requirement says before stage 0). To cure the ordering, the
lead re-ran `screen_ood_surfaces.py` after pinning, under the pinned sha:
`screen_summary.json` came back byte-identical
(36d80b90c5ab552399578177643876c14670cb0fbefd77d317c66daabd0af746), every
registered count again reproduced, wall-clock 2.91 s. The committed screen
output is therefore generated under the pinned instrument. `gate_score.py`
no-data invocation verified (reports G3/G_docker computable, evidential gates
NOT_RUN) at 0.22 s.

Nothing in this entry is a result. No generation has been run and no
evidential gate has been read.

## 2026-08-09T09:55Z LAUNCH: stages 2-4 (re-merge, G1 re-parity, smoke), then stage-5 panel on gate pass

Harness merged to main (PR #411, commit 6d8da5fd). PI merge-and-proceed
approval received 2026-08-09; the 8-12 GPU-h panel launch is covered by the
standing burn-down approval. GPU queue is free (item-27 census complete).

Launching now, per RUNBOOK.md: stage 2 (re-merge the surviving contrastive
LoRA to 16-bit), stage 3 (SelfAware re-parity for A2, gate G1, 0.10pp
parity bar), stage 4 (A1 on S_AMBIGQA 64-row smoke, gates G2 and G3). The
run agent reports raw gate inputs and STOPS after stage 4; the lead
adjudicates G1/G2/G3 from artifacts before authorizing stage 5. A G1 FAIL
voids arms A2, A6, A7 per gates.yaml; it does not void the cell.

Runtime: docker lane with the pinned digest recorded in experiment.yaml
instrument.runtime_image_digest, one GPU job at a time. Row-level outputs
stay gitignored; committed artifacts are counts, metrics and shas only.

Nothing in this entry is a result. No evidential gate has been read.

## 2026-08-09T10:40Z Stages 2-4 complete. G1 FAIL adjudicated: arms A2/A6/A7 VOID, cell reports on five arms. G2/G3 smoke readings clear. Stage 5 authorized on A1/A3/A4/A5/A8

**Stage results (run agent, verified by lead).** Stage 2 re-merge exit 0
(98 s; ~7 GB). Stage 3 re-parity exit 0 (25m33s), fresh metrics under
archive/experiment/phase1/eval/results_amendment_k_response_confidence_selfaware_contrastive_sft_seed1_merged_full_4b/.
Stage 4 smoke exit 0 (1m39s), 64-row AmbigQA slice, output under
archive/experiment/phase1/eval/results_ood_breadth_smoke64_A1_ambigqa/.
Docker digest verified char-for-char before every launch.

**G1 adjudication (lead, from primary artifacts).** The lead re-read both
metrics.json files directly (committed reference under
experiments/contrastive-sft-behavior-conditional-confidence/analysis/phase1-migrated/eval/,
fresh rerun above) and confirmed the pinned gate_score.py comparison:
n/n_known/n_unknown exact (3369/2337/1032), but five of nine behavior
metrics exceed the registered 0.10pp bar: refusal_recall 83.72 -> 84.11
(0.39pp), answer_on_unknown 16.28 -> 15.89 (0.39pp), over_refusal
79.20 -> 79.59 (0.39pp), refusal_rate 80.59 -> 80.97 (0.38pp),
correct_on_known 36.63 -> 36.90 (0.27pp). correct_on_unknown (0.00) and
truthful (0.06pp) are within. Per gates.yaml g1_remerge_parity, whose
derivation sets 0.10pp deliberately below the rounding grain so that only
bit-faithful reproduction passes: G1 FAIL. Registered consequence applied
unchanged: on_failure void_arms_A2_A6_A7_report_on_five_arms. The
re-merged base is an unverified substitute for the absent original
answer-supervised merged weights; no retry is registered and none is
taken. The falsifier now evaluates over the five surviving arms
(A1, A3, A4, A5, A8); this is the registered five-arm reporting shape,
not a goalpost move.

**G2/G3 smoke readings (stage-4 scope only).** G2: n=64 as constructed,
label_from_target false, stated-confidence coverage 100.0 vs 99.0 floor.
G3: exit 0, no assertion or traceback in the container log, zero think-tag
matches over the 64 scored rows, enable_thinking false in config. Full-
surface G2/G3 read at stage 5.

**Correction to the 2026-08-09T09:55Z launch entry.** That entry cited
"experiment.yaml instrument.runtime_image_digest" as the digest of record;
no such field exists in this experiment's manifest. The digest of record
is cell.yaml lane.docker_digest, which matches the digest used and
verified at every stage
(sha256:f21629b9ae4ed11231768edfaed0f40d41d85d6ea9a71e8096a3d96ea0311772).

**Stage 5 authorized (lead), reduced panel.** Arms A1, A3, A4, A5, A8
across the three screened surfaces; the three voided arm configs are not
run. Budget shrinks from the registered 8-12 GPU-h eight-arm estimate to
roughly five eighths of it. Stages 6 (A1/A4 extraction) and 7 (CPU probe
fit) may follow the panel without further authorization; stage 8
adjudication is the lead's and waits for the artifacts.

## 2026-08-09T15:35Z Stage-6 runtime pinned: mechinterp-runner image built, digest hand-added (audit entry)

The run agent stopped before stage 6 on a genuine missing precondition it
was right to flag: RUNBOOK stage 6 gives a bare `MechInterp.cli extract`
invocation, but the standing directive of 2026-07-10
(.skills/mechinterp-cells/reference/modal-launch.md) requires every local
`mechinterp` GPU verb to run inside the pinned mechinterp-runner image,
with the digest recorded as experiment.yaml instrument.runtime_image_digest.
No such image existed on this host and no such field existed in this
manifest. Root cause of the gap: the directive requires delegation prompts
for mechinterp work to restate the invariant, and the harness-build prompt
did not; the RUNBOOK inherited the omission. The item-25 host-python
extraction precedent does not apply here: that cell ran its own pinned
knowledge-probe module, not the tuner CLI, so the directive never bound it.

Resolution taken (option a, no waiver): built mechinterp-runner:local from
synaptic-tuner/docker/mechinterp-runner/ per its README (build exit 0,
2026-08-09), captured the local Image ID
sha256:c927f4200d49f62207dd954e9d20b80b902d1d845e7a908240ab3767452e33bc
(not registry-pushed, Image ID per the directive), and hand-added it to
experiment.yaml as instrument.runtime_image_digest, a sibling of
instrument.pins as the directive specifies. Scope note recorded beside it:
this digest governs the stage-6 extract verb; the eval-lane stages 2-5 ran
under cell.yaml lane.docker_digest as registered and verified.

Stage 6 is authorized inside this image only; the runner entrypoint's
provenance JSON line must appear in the stage-6 run log. Stage 7 (CPU)
follows. Nothing in this entry is a result; no evidential gate has been
read beyond the G1/G2/G3 adjudications recorded at 10:40Z.

## 2026-08-09T16:00Z Runtime pin superseded before first use: image rebuilt with requests and peft

The run agent found the freshly built runner image unable to execute the
stage-6 path at all: the MechInterp.cli router imports requests at dispatch
time (ModuleNotFoundError before any handler), and A4's --adapter load
imports peft; neither was in the Dockerfile's pinned set. The agent
correctly refused to pip-install into the pinned runtime ad hoc and
stopped. Zero extraction rows were produced under the defective image, so
nothing evidential ran under the superseded pin.

Fix, kept generic in the tuner submodule: requests==2.32.3 and peft==0.18.1
added to the Dockerfile pin set (versions validated on the local stack),
committed as 69c65b3 on synaptic-tuner branch
fix/mechinterp-runner-requests-peft and pushed BEFORE the rebuild, so the
image provenance line records a revision that contains the fix. Rebuilt
image verified importing both packages. instrument.runtime_image_digest
superseded in place (never used for an evidential run):
sha256:c927f4200d49f62207dd954e9d20b80b902d1d845e7a908240ab3767452e33bc ->
sha256:44950acd646764ada50f020de0a2b2733a07ec93e0270dce58581a2c859ba41c.

Stage 6 re-authorized inside the rebuilt image only. Nothing in this entry
is a result.

## 2026-08-09T16:20Z Runtime pin superseded a second time: pandas added after full handler sweep

The rebuilt image still failed at the router gate: route_command eagerly
imports all 22 handler modules before dispatching any verb, and five
cloud/experiment handlers import pandas at module load. The run agent's
per-handler import sweep inside the image established pandas as the ONLY
remaining gap (17 handlers including mechinterp_handler import cleanly).
Fix committed in the tuner submodule as 552775a (pandas==2.2.3, validated
on the local stack), pushed before rebuild, image rebuilt and all three
added packages verified importing. Zero extraction rows ran under the
superseded pin. instrument.runtime_image_digest superseded in place:
sha256:44950acd646764ada50f020de0a2b2733a07ec93e0270dce58581a2c859ba41c ->
sha256:2471502c3110a96d4955b48eb58da41e96a90276d22c4d5f1eac2c99b60a2cf8.

Stage 6 re-authorized inside the rebuilt image only. Nothing in this entry
is a result.

## 2026-08-09T16:45Z Stage 8 complete. Full gate adjudication, prediction scoring, falsifier reading (lead)

**Instrument events first.** The pinned gate_score.py gates its evidential
block on a flat all() over the integrity gates; gates.yaml scopes G1's
failure to voiding A2/A6/A7 only. Adjudicated as a pinned-script defect
against the registration; remedied per the wrong-answer-cell-power-fix
precedent with a new module, score_evidential_fivearm.py (sha256
013300c4..., hand-pinned this entry), which imports the pinned scoring
functions and calls them unchanged, bypassing only the flat short-circuit.
Lead read the wrapper line by line before pinning: no threshold, formula,
seed, or population is altered. Its run reproduced the integrity statuses
verbatim and produced G5 and G6; wall-clock 0.35 s.

**Gate verdicts (lead, from artifacts).**
- G1 FAIL, consequence applied as registered: arms A2/A6/A7 VOID, cell
  reports on A1/A3/A4/A5/A8 (entry 2026-08-09T10:40Z).
- G2 PASS: all 15 surviving arm x surface cells at exact registered counts,
  coverage 100.0 vs 99.0 floor, label_from_target false everywhere.
- G3 PASS: enable_thinking false on all configs, zero think-marker hits
  across all 15 scored_rows files.
- G_docker_digest PASS.
- G4 NOT_RUN AS REGISTERED. gates.yaml g4 registers n_arms: 8 and derives
  its 0.70 threshold explicitly from the eight-arm count; after the
  registered G1 consequence, only five arms exist. The two registered
  clauses (g1 on_failure five-arm reporting; g4 eight-arm instrument)
  conflict, and no_goalpost_movement forbids re-deriving a five-arm
  threshold post hoc. The pinned score_g4's len(arm_rr) < 8 check is
  faithful to the registration and its NOT_RUN stands. Recorded gap, for
  the record only: the pinned score_g4 also never implemented the
  registered paired_bootstrap_200_resamples_seed_12345 uncertainty; moot
  for a NOT_RUN gate, but a harness lesson. DESCRIPTIVE, UNREGISTERED,
  UNGATED context (labeled as such wherever quoted): five-arm Spearman of
  arm rank by refusal_recall vs SelfAware is approximately 0.10 on KUQ and
  0.20 on AmbigQA, computed with a plain rank; the SelfAware reference
  levels are compressed into about 6.5pp with one exact tie (93.51 twice),
  so arm ordering is noise-dominated at this spread and these values carry
  no gate weight.
- G5 FAIL as registered (requires both conditions on every arm): A1
  0.6023/0.0490 pass-pass, A4 0.4530/0.0106 pass-pass, A5 0.5007/0.0274
  pass-pass, A3 0.3953/0.1687 auroc-pass std-FAIL, A8 0.3588/0.4238
  auroc-pass std-FAIL. The stated-confidence collapse does not transfer
  uniformly: two of five surviving arms show real stated-confidence spread
  on AmbigQA. Note the spread carries no positive appropriateness signal
  (both arms rank below chance).
- G6 read (labeling context, n=23 per side, registered not_falsifier
  surface): refusal_recall 100.0 on all five arms; over_refusal 43.48 to
  56.52 with wide Wilson CIs.
- G7 FAIL on both internal-panel arms, per the pinned script's own fields,
  lead-verified from g7_A1.json / g7_A4.json: held-out probe AUROC 0.6279
  (A1) and 0.6349 (A4) vs 0.90 floor; margin over same-checkpoint emitted
  0.1326 / 0.1379 vs 0.15 floor; n_panel 2748 (1245/1503) exact both arms.

**Prediction scoring (four registered components, scored as worded).**
1. Unknown-side rank-order transfer (rho >= 0.7): NOT ADJUDICABLE (G4
   NOT_RUN as registered).
2. Stated-confidence collapse transfers unchanged on every arm: FAILED
   (G5 FAIL, two arms exceed the std ceiling).
3. Internal readout separates the AmbigQA boundary at >= 0.90 held-out on
   both internal-panel arms: FAILED (0.63 both arms).
4. Known-side over-refusal shifts by more than 10 points on at least one
   surface: SUPPORTED. Every surviving arm moves more than 10pp on at
   least one surface (BIG-bench -8.6 to -14.9pp, AmbigQA +7.3 to +11.9pp,
   KUQ +8.0 to +10.3pp vs each arm's committed SelfAware level).

**Falsifier reading (as worded, thresholds untouched).** The registered
falsifier requires two or more arms with emitted AUROC to appropriateness
>= 0.70 together with emitted std > 0.15 on AmbigQA. Measured: the two
high-std arms (A3 0.1687, A8 0.4238) rank at 0.3953 and 0.3588, below
chance; the highest AUROC on any surviving arm is A1's 0.6023. The
falsifier DOES NOT FIRE. Paper 3's "collapsed near-constant" sentence does
not take the registered narrowing, though the G5 failure obliges the
variance qualifier above wherever the collapse is described as universal.

**Headline for the write-up (verdict wording proposed, resolve pending PI
approval).** Behavior transfers in level (refusal recall 93.7-97.4 KUQ,
100.0 BIG-bench, 67.9-77.5 AmbigQA), and known-side levels move as
predicted; but paper 3's near-perfect internal known-unknown readout does
NOT transfer to the AmbigQA answerability boundary (0.997 on SelfAware ->
0.63 held-out here, G7 FAIL both arms), and the stated-confidence collapse
is not universal across arms on the new surface (G5 FAIL). Three of eight
arms were voided pre-panel by the registered G1 re-merge parity gate; the
rank-transfer gate was structurally unadjudicable thereafter.

Committable summaries copied to analysis-committed/ (gate_report.json,
evidential_report_fivearm.json, g7_A1.json, g7_A4.json, five
calibration_gap jsons; all verified counts-and-metrics only).

## 2026-08-27 — Exhaust published to HF (aggregate shape)

Data-exhaust release, PI-approved in-conversation (explicit permission
2026-08-27, batch 3 of the exhaust backfill, task-56c61a). Built with the
data-exhaust skill (aggregate-only copy-everything mirror of
analysis-committed/: no question text, generation text, or hidden states;
verify_exhaust.py PASS including the --experiment-dir completeness check;
zero exclusions). 11 files / ~43 KB, built at repo commit 37eaa399.

- HF repo: `professorsynapse/eh-ood-breadth-beyond-selfaware` (dataset)
- HF revision: `b1e3246c6b3f61c0f8c4d61dd738ba2d2cca0889`
