# ood-breadth-beyond-selfaware

Status: resolved (machine state in `experiment.yaml`; verdict on record
there -- see experiment.yaml `verdict:`). This header was stale
boilerplate reading "draft (not signed)" until 2026-08-11; corrected to
match the machine state, which was already `resolved`. The gap flagged at
that same correction pass — this document's own "Outcome" section still
carrying the unfilled placeholder text ("Filled at resolve...") — was
backfilled 2026-08-11 in a PI-approved governed pass, written from the
recorded verdict and the committed artifacts. No adjudication was
performed and no verdict, gate, threshold, or status changed.

Machine state lives in `experiment.yaml`; the instrument specification lives in
`cell.yaml`; the pre-stated thresholds live in `gates.yaml`. This document is the
prose home and does not duplicate them.

Burn-down origin: TODO.md paper-3 limitations burn-down, item 26.

## Motivation and posture

Paper 3 (`papers/paper-3-knows-but-doesnt-say/manuscript.md`) carries this
limitation verbatim at lines 1027-1029:

> SelfAware-only OOD surface. Behavior and stated-calibration numbers are on one
> OOD benchmark. Generalization to other known/unknown surfaces is untested.

Every behavior number (`refusal_recall`, `over_refusal`, `correct_on_known`,
`truthful_pct`) and every stated-calibration number (emitted-scalar AUROC against
response appropriateness, ECE, standard deviation, per-behavior-cell mean) in
Sections 4 and 7 is computed on SelfAware and only SelfAware. Manuscript lines
266-270 state the setup: "The out-of-distribution evaluation is SelfAware
[arXiv:2305.18153] (n = 3369; 1032 unknown-labeled, 2337 known-labeled), scored
with the locked-training-regimen eval harness."

The internal-versus-stated gap is the paper's headline. If the stated side of
that gap is a SelfAware artifact, the headline narrows from a claim about the
model to a claim about one benchmark. This cell re-runs the behavior panel and
the stated-calibration panel on three additional known/unknown surfaces, adds an
internal known-unknown readout panel on one of them, holds the checkpoints and
the instrument fixed, and reports whether the readings transfer.

This is re-estimation of existing directional claims on new surfaces. It is not a
new claim and it cannot promote anything.

### Posture

Tier 2, exploratory, per
`.skills/experiment-runner/reference/amendment-vs-lab-notebook.md` decision
question 2: it adds a new eval cell that will be reported as evidence. It is not
tier 1 because it changes no hypothesis, no metric definition, and no locked
headline matrix. It is not tier 3 because its results will be cited in the
manuscript, so a prediction, a falsifier, and gates must be fixed before the run.

Results are reported separately from the PROTOCOL v0.3 locked headline matrix and
are never pooled with it or labeled as headline results. Paper 3's Section 7
cells are already exploratory (manuscript Appendix A, "Governance notes"); this
cell joins them at the same tier. Per the same reference's promotion section, a
successful exploratory result becomes a claim only through a confirmatory
replication registered in advance.

### Why this design is front-loaded with screens

The recent SelfAware contamination finding is the reason the screens are a gate
rather than a caveat. Manuscript lines 1006-1023 record the training/evaluation
overlap, and the governing record corrects the accounting:
`experiments/grpo-three-seed-confirmatory/NOTEBOOK.md` lines 1835-1839, entry
"2026-08-07 ~09:50Z POST-RESOLUTION ADDENDUM", gives a 128-question union of 117
verbatim gradient-training hits plus 11 that leak only into the GRPO dev split,
all known, zero unknown. It also records that the red team missed the dev-split
leg because it checked train files only, and that the leak surfaced after the
block resolved.

The pipeline was supposed to catch this. `archive/experiment/phase1/eval/ood.py`
lines 20-22 state that "the run_eval driver additionally asserts the trained
question set does not appear in any OOD set (section 6.5 defensive check) using
norm_question from scorers.py". No such assertion exists: searching `run_eval.py`
for `norm_question`, `train_questions`, `overlap` and `contamin` returns only an
unrelated thinking-token contamination message at line 172. The documented guard
is absent from the code. This cell therefore treats disjointness as a standalone
fail-closed pre-run gate (G0) with its own script and committed manifests, and
relies on the harness for nothing. Repairing the false docstring claim is
registered as follow-up F1 in `cell.yaml` and is explicitly not done here.

## Design

Full specification in `cell.yaml`. Summary of the parts that carry the argument:

### Arms

The eight checkpoints paper 3's Section 7 cites, taken from the run table in
`papers/paper-3-knows-but-doesnt-say/analysis/clean_subset_sensitivity_p3.py`
lines 78-141, which derives from manuscript Appendix A: clean-SFT base,
answer-supervised, answer-masked, GRPO v2, proper-scoring GRPO v3, RL on the
answer-supervised base at beta 0.10 and at beta 0.05, and probe-axis
distillation. The GRPO-par-true checkpoint is excluded.

**The answer-supervised merged base is absent from disk.** The directory
`scratch/schema_response_confidence/runs/sft_schema_contrastive_seed1_full/20260627_203232/Qwen3-4B-bnb-4bit/`
exists but is empty; the `merged-16bit/` weights were deleted. The surviving
artifact is the LoRA adapter at
`.../20260627_203232/final_model/adapter_model.safetensors` (252.1 MB). Three of
the eight arms serve from that base, including the answer-supervised versus
answer-masked contrast the manuscript calls the localizing result (line 595).
The base is recoverable by re-merging the surviving adapter to 16-bit without
retraining, and gate G1 turns that recovery into a measurement: A2 must reproduce
its committed SelfAware metrics within 0.10 percentage points or arms A2, A6 and
A7 are voided and the cell reports on five arms.

### Surfaces

Three surfaces, each with a known and a gold-unanswerable side, mirroring
SelfAware's structure. All counts in `cell.yaml` were measured read-only at
registration time as the pre-sign feasibility probe the tier reference requires,
touching row membership only and never any outcome.

- **KUQ** (MIT, tracked in git), 5540 rows retained, 2469 unknown and 3071 known.
- **AmbigQA validation split** (cc-by-sa-3.0), 1832 rows retained, 1002 unknown
  and 830 known, whole split with no subsampling.
- **BIG-bench known-unknowns** (apache-2.0), 46 rows, 23 per side, spot check
  only under G6.

7418 rows per arm, 59,344 generations across the eight arms.

**The item-26 guard fires, and it fires hard.** 169 KUQ known questions appear
verbatim, whitespace and case normalized, as user prompts in the training pools.
Zero KUQ unknown questions do. The mechanism is transparent: KUQ's known side is
drawn from SQuAD (1928 rows), TriviaQA (854) and HotpotQA (665), and paper 3's
training data is TriviaQA-RC via the Cheng recipe (manuscript lines 263-266).
Unscreened KUQ is not an OOD surface for known-side metrics. It becomes one only
after the screen and only with the screen's counts reported.

A second contamination the TODO row does not mention: **220 KUQ questions also
appear in SelfAware**, 207 known and 13 unknown. Reusing those rows would make
the surface partly a re-run of the one it is meant to be independent of, so they
are screened out. In the ordered screen 197 known and 13 unknown are attributed
to the SelfAware step, because 10 of the 207 were already removed as duplicates
or training hits; both figures are recorded in `cell.yaml` so neither is mistaken
for the other.

AmbigQA and BIG-bench are clean on every screen.

### Screens

Method identical to the pinned SelfAware derivation so the two are comparable:
`normq(text) = re.sub(r"\s+", " ", text.strip().lower())` matched against the
verbatim user-turn content of every training file, as in
`clean_subset_sensitivity_p3.py` line 186. The training union covers all eight
files any paper-3 checkpoint lineage consumes, 15,465 distinct prompts, and
includes `grpo_dev` because the 2026-08-07 addendum established that
checkpoint-selection exposure is exposure.

The PAR mining pool overlap is measured and recorded but is not binding for these
arms, since none of them trains on that pool. It is binding as a standing
exclusion for any PAR-trained checkpoint: of the retained rows, all 1002 AmbigQA
unknown, all 23 BIG-bench unknown, 627 KUQ unknown and 44 KUQ known sit in that
pool.

### Internal panel

Per the registration decision, the internal known-unknown readout panel runs on
AmbigQA at 1.5 times the drafted size: **2748 rows, 1503 unknown and 1245 known**.
It is the whole 1832-row screened validation surface plus a 916-row top-up (501
unknown, 415 known) drawn from the screened AmbigQA train split, so the panel is
a superset of the behavior surface and the like-for-like internal-versus-emitted
contrast is computed on the 1832 shared rows while the top-up adds probe power
only. Top-up selection is deterministic and stated before the run: screen the
train split by the same three screens plus a fourth removing anything already in
the validation split, sort survivors by AmbigQA id as a string, take the first N
per class at the validation split's unknown fraction. No randomness and no seed.
At registration 4739 unknown and 5286 known screened train rows were available
against the 501 and 415 needed.

The panel runs on arms A1 and A4, the two arms in this list for which paper 3
publishes a SelfAware internal number, so a like-for-like comparison exists:
clean SFT at 0.9968 and SFT-to-GRPO-v2 at 0.9971 (manuscript lines 387-390), plus
the GRPO-v2 like-for-like contrast of internal 0.972 against emitted 0.637 on
n=1233 joined rows (manuscript lines 359-364). Layer 35 and the generation-position
read follow manuscript lines 270-272 and 277-279; the probe is fit with 5-fold
cross-validation without correct/wrong leakage per lines 311-315. Only the
extraction pass is GPU work; the fit is CPU.

### Rendering and scoring

Byte-identical to the SelfAware panels, surface swapped only. The parity
precedent is `docs/preparation/amendment-ai-cloud-verdict-cells.md` lines 179-181,
which records that panel parity requires the same pipeline and config on the same
surface with only the checkpoint swapped, and that a wrong-pipeline comparison is
worse than a late one. System prompt, generation settings, vLLM settings,
bootstrap settings, `scorers.score_quadrants` and `calibration_gap_report.py`
Analysis A are all carried over unchanged; the exact values are in `cell.yaml`.
Three deviations are declared there with rationale: `gold_path` populated but
unused, two additive loaders in `ood.py`, and surfaces consumed from the screened
manifest rather than by positional `offset`/`limit`.

Generation serves through vLLM on the local dgpu lane, one GPU job at a time,
inside the pinned image
`sha256:f21629b9ae4ed11231768edfaed0f40d41d85d6ea9a71e8096a3d96ea0311772`,
verified char for char with `docker inspect` before any stage counts as valid.

### Metric availability is not uniform across surfaces

`correct` requires usable gold on the known side, and only AmbigQA has it.
KUQ's answers are long-form rather than strict aliases by the loader's own
statement (`ood.py` lines 45-47), so alias matching under-counts correct answers
and everything downstream of appropriateness inherits that noise on KUQ's known
side; those metrics are reported with the caveat and are not gated. BIG-bench is
multiple choice with no free-form gold, so correctness is not computable there at
all. AmbigQA therefore carries the appropriateness-based gates (G5, and the
margin leg of G7).

A binding reporting constraint applies to `correct_on_known_pct` regardless of
surface: it is `correct_known / answered_known` (`scorers.py` line 287), a
filtered denominator that excludes refused known rows.
`docs/sessions/20260806T115256Z-grpo-three-seed-confirmatory-seed-3-chain-and-g1-adjudication.md`
line 190 records that this metric rose from 47.49 to 55.05 while the raw correct
count fell from 455 to 403, and rules it blocked from any write-up unless quoted
with its denominator and raw count. `refusal_recall_pct`, `answer_on_unknown_pct`
and `over_refusal_pct` use unconditional full-class denominators and are safe to
quote bare.

## Prediction

Stated once, before any generation, and not softened afterwards.

Unknown-side abstention behavior transfers in rank order across arms (Spearman
rho at least 0.7 against SelfAware on KUQ and AmbigQA); the stated-confidence
collapse transfers unchanged (every arm at emitted AUROC against appropriateness
no greater than 0.65 and emitted standard deviation no greater than 0.10 on
AmbigQA); the internal known-unknown readout still separates the AmbigQA
answerability boundary (held-out AUROC at least 0.90 on both internal-panel
arms); and known-side over-refusal levels shift by more than 10 points on at
least one surface because the new known sides are drawn from different source
corpora.

The four components in detail:

- **P1, unknown-side behavior transfers.** Arm rank order by `refusal_recall_pct`
  matches SelfAware's, and the abstention-trained arms retain at least 80 percent
  refusal recall on KUQ's unknown side.
- **P2, the stated-confidence collapse transfers.** This is the strongest
  component. Paper 3 reports the emitted scalar at AUROC 0.52 to 0.56 against
  appropriateness (manuscript lines 335-337) with standard deviation about 0.015
  on the held-in known set (lines 329-331). The collapse is attributed to the
  single-token-via-CE output channel rather than to the question distribution, so
  a surface swap should not move it.
- **P3, over-refusal is surface-sensitive and will move.** Predicted as a real
  effect, not as noise, and the reason absolute behavior levels are reported per
  surface and never averaged across surfaces.
- **P4, the answer-supervision dissociation keeps its sign.** The
  answer-supervised versus answer-masked contrast holds its direction on AmbigQA.
  The SelfAware values are 0.684 against 0.552 with a 0.62 gate
  (`papers/paper-3-knows-but-doesnt-say/scripts/build_figures.py` line 116).

## Falsifier

Stated once, before any generation, and not softened afterwards.

On AmbigQA, two or more of the eight arms show emitted AUROC against
appropriateness of at least 0.70 together with emitted standard deviation above
0.15.

Two arms rather than one, because a single arm at 0.70 on n=1832 is within the
range one lucky recipe could produce, while two independent arms is a pattern.

**The sentence that dies:** manuscript lines 346-347, "the discriminating signal
exists internally and the verbalized number is a collapsed near-constant", must
be narrowed in writing to hold on SelfAware rather than in general, and the
SelfAware-only bullet at lines 1027-1029 is not lifted. A model whose stated
confidence does real discriminative work on a surface where paper 3 says it
cannot means the stated channel is surface-dependent rather than structurally
bottlenecked, and the paper's central framing is overstated as written.

If the falsifier fires it is reported as a falsification. The response is to
narrow the claim to the surfaces where it holds and write the new surface into
Section 9 as a scope boundary. It is not to retune the threshold, drop AmbigQA,
or reweight toward KUQ.

Not falsifiers, stated so they are not mistaken for one: P3 moving, since it is
predicted to move; BIG-bench disagreeing, since no gate reads it; and KUQ's
correctness-dependent metrics disagreeing, since that surface's gold is known to
be unreliable.

## Gates

Thresholds, directions and derivations are in `gates.yaml`. In summary:

| Gate | Kind | Threshold | Direction |
|---|---|---|---|
| G0 disjointness screen | integrity, fail-closed | 0 training-pool hits and 0 SelfAware-overlap hits among retained rows; dataset sha256 must match | pass required |
| G1 re-merge parity | integrity | all nine behavior metrics within 0.10 pp of committed A2 SelfAware values, n and class counts exact | pass required |
| G2 surface construction | integrity | retained n exactly as registered per surface; `label_from_target` false; JSON coverage at least 99.0 percent | pass required |
| G3 no thinking contamination | integrity | both run_eval assertions clean, `enable_thinking` false | pass required |
| G docker digest | integrity | image digest equals the pinned sha256 char for char | pass required |
| G4 unknown-side behavior transfer | evidential | Spearman rho at least 0.70 against SelfAware on KUQ and AmbigQA | higher is pass |
| G5 stated-collapse transfer | evidential | every arm at emitted AUROC no more than 0.65 and std no more than 0.10 on AmbigQA | lower is pass |
| G6 BIG-bench labeling | labeling, not outcome | every rate carries n and a Wilson 95 percent interval, labeled spot check, read by no evidential gate | pass required |
| G7 internal readout transfer | evidential | held-out probe AUROC at least 0.90 on both panel arms, and at least 0.15 above the same checkpoint's emitted AUROC on the 1832 shared rows | higher is pass |

All integrity gates are read first and all must pass before any evidential gate
is read. G0 failure voids the affected surface. G1 failure voids arms A2, A6 and
A7 and the cell reports on five arms.

Every threshold is fixed at signing. An ambiguous result is reported as
ambiguous.

## Design decisions at registration

Adjudicated by the PI and the lead, recorded here as binding:

1. **Internal panel on AmbigQA, expanded by 50 percent over the drafted size.**
   Implemented as 2748 rows against the drafted 1832. Construction, top-up rule
   and availability check are in `cell.yaml` under `internal_panel`.
2. **AmbigQA-as-unknown convention accepted**, with the construct caveat stated
   under Limitations below.
3. **GRPO-par-true excluded** from the arm list, with the measured overlap that
   independently disqualifies it recorded in `cell.yaml`.
4. **Eight multi-surface configs**, one per arm, rather than 24 single-surface
   configs.
5. **Screens registered as G0, fail-closed**, covering both the 169-question KUQ
   training contamination and the 220-question SelfAware overlap. G0 failure
   voids the affected surface.
6. **The absent answer-supervised merged base is handled inside this cell** as
   the G1 re-merge parity gate at 0.10 percentage points, with the arm voided on
   failure.
7. **The false disjointness-assert claim in `ood.py` is not fixed here.**
   Recorded as follow-up F1 against the leakage-guard extension follow-up already
   on file from grpo-three-seed-confirmatory (NOTEBOOK.md line 1848).

Self-resolved at registration under the least-assumption rule, each recorded
because none was adjudicated explicitly:

8. **Internal-panel arms: A1 and A4 only.** The two arms in this list for which
   paper 3 publishes a SelfAware internal number, so a like-for-like comparison
   exists. Extending to all eight would multiply the extraction cost without a
   published comparison value to read the result against.
9. **Internal-panel layer, read position and fit protocol reuse paper 3's**
   (L35, generation position, 5-fold cross-validation without correct/wrong
   leakage). Introducing a new layer or protocol would confound a transfer
   question with an instrument change.
10. **Internal-panel top-up drawn from AmbigQA train, sorted by id, no seed.**
    A deterministic rule with no randomness cannot be re-drawn to taste, and the
    validation split alone cannot supply 2748 rows.
11. **The top-up preserves the validation split's unknown fraction** (0.5469)
    rather than balancing the classes, so the expanded panel's composition is a
    scaled version of the behavior surface rather than a differently shaped
    population.
12. **The experiment runs from the canonical checkout, not the worktree.**
    `datasets/ambigqa/` and `datasets/bigbench-known-unknowns/` are gitignored in
    full (`.gitignore` lines 75 and 76), dataset cards included, so they exist in
    no worktree checkout. Governed files are authored in the worktree; nothing
    here commits dataset bytes.
13. **The four gitignored dataset files are pinned by sha256 in `cell.yaml` and
    verified by G0**, because `bin/exp sign` cannot pin files it cannot see. A
    sha mismatch is a G0 failure, so the fail-closed property survives the files
    being untracked.
14. **Screened id manifests are not committed.** Only counts, input shas and the
    sha256 of each retained id list go into the committed surface; the id lists
    themselves stay under the gitignored `analysis/` directory. This matches the
    repo's existing containment posture for these two datasets and keeps the
    public repo free of row-level data.
15. **The screen script stays local to this experiment** rather than being
    promoted into the experiment-runner skill. Recorded as follow-up F2.
16. **GPU budget revised from the drafted 7 to 11 hours up to 8 to 12 hours** to
    absorb the expanded internal panel, with the basis recorded in `cell.yaml`
    under `run_plan.gpu_budget_basis`.

## Limitations

- **Construct heterogeneity across surfaces.** AmbigQA "unanswerable" means
  ambiguous or underspecified, a question with multiple valid readings each
  carrying a different answer. SelfAware and KUQ "unknown" means unknown to
  anyone. These are different constructs. Breadth across kinds of unanswerability
  is the point, but the two must be labeled rather than blurred in any write-up.
  KUQ's own `ambiguous` category (411 retained rows) is the bridge between the
  readings and is reported as its own stratum.
- **KUQ correctness is unreliable**, so its correctness-dependent metrics are
  caveated and ungated (`ood.py` lines 45-47).
- **BIG-bench is n=23 per side**, spot check only, gated as such by G6.
- **Single seed, single model.** This cell inherits paper 3's seed-1 Qwen3-4B
  scope entirely; it broadens the evaluation surface and nothing else.
- **The internal panel covers two arms and one surface**, so this cell can show
  the stated side of the gap transfers across three surfaces but can speak to the
  gap itself only on AmbigQA and only for the clean-SFT and GRPO-v2 checkpoints.
- **Three surfaces is not all surfaces.** On success, Section 9's bullet is
  narrowed to name the surfaces tested and the construct boundary, not deleted.

## Reporting rule

- Exploratory, tier 2, reported separately and never pooled with the locked
  headline matrix.
- Per surface, never averaged across surfaces, with each surface's n and class
  denominators attached. P3 predicts the levels genuinely differ, so a
  cross-surface average would be a number about nothing.
- `correct_on_known_pct` always with its denominator and raw count.
- Screen counts published in the manuscript, not only in this document, because
  the unscreened version of the KUQ surface would have been contaminated.
- BIG-bench labeled spot check with Wilson intervals on every rate, per G6.
- On success, paper 3 Section 9's SelfAware-only bullet is rewritten to name the
  surfaces tested, the surfaces not tested, and the construct boundary.
- On falsification, the Falsifier section's response applies.
- Promotion to a claim requires a confirmatory replication registered in advance.

## Predictions scoreboard

| Predictor | Call |
|-----------|------|
| orchestrator | |
| user | |

## Outcome

Resolved 2026-08-09. Gates were adjudicated by the lead at 2026-08-09T16:45Z
(`NOTEBOOK.md`, stage-8 entry); the verdict was PI-approved and the resolve
stamp applied the same day. The falsifier did not fire; the cell reports on
five arms after the registered G1 void.

One-sentence summary (also in `experiment.yaml` `verdict:`): "Falsifier not
fired; behavior transfers in level but the internal known-unknown readout does
not transfer to AmbigQA (G7 FAIL both arms, 0.6279/0.6349 vs 0.90 floor) and
the stated-confidence collapse is not universal (G5 FAIL); G4 unadjudicable
after the registered G1 void of arms A2/A6/A7."

### Gate results

Integrity gates, read first as registered:

- **G0 disjointness screen: PASS.** `screen_summary.json`
  (`dataset_sha256_verification.all_match: true` over all six pinned files;
  `registered_count_check.all_match: true` with an empty `mismatches` list).
  Retained rows carry zero training-pool hits and zero SelfAware overlaps on
  every surface: KUQ retained 3071 known (from 3447 raw, dropping 10
  duplicates, 169 training hits, 197 SelfAware overlaps) and 2469 unknown
  (from 3437, dropping 955 duplicates, 0 training hits, 13 overlaps), total
  5540; AmbigQA validation retained 830 known and 1002 unknown with zero drops
  on every screen and 170 mixed-annotation rows excluded by rule; BIG-bench
  retained 23 per side with zero drops. Training-pool union 15,465 distinct
  prompts. The AmbigQA internal panel was built to 2748 rows (1245 known, 1503
  unknown) as the 1832-row validation surface plus the registered 916-row
  deterministic train top-up (415 known, 501 unknown selected against 5286 and
  4739 available).
- **G1 re-merge parity: FAIL.** `analysis-committed/gate_report.json`,
  `integrity_gates.G1`. Row counts reproduced exactly (n 3369, known 2337,
  unknown 1032), but five of the nine behavior metrics exceeded the registered
  0.10 pp bar on the re-merged answer-supervised base: `refusal_recall_pct`
  83.72 to 84.11 (0.39 pp), `answer_on_unknown_pct` 16.28 to 15.89 (0.39 pp),
  `over_refusal_pct` 79.20 to 79.59 (0.39 pp), `refusal_rate_pct` 80.59 to
  80.97 (0.38 pp), `correct_on_known_pct` 36.63 to 36.90 (0.27 pp).
  `correct_on_unknown_pct` (0.00) and `truthful_pct` (0.06 pp) were within.
  The registered consequence was applied unchanged and no retry was taken:
  `void_arms_A2_A6_A7_report_on_five_arms`. The cell reports on A1, A3, A4,
  A5, A8. (`correct_on_known_pct` appears here only as a reproduction delta on
  a fixed population; its filtered denominator makes it unquotable as a level
  without its denominator and raw count, per the reporting rule above.)
- **G2 surface construction: PASS.** All 15 surviving arm-by-surface cells at
  their exact registered counts (KUQ 5540 = 3071 + 2469; AmbigQA 1832 = 830 +
  1002; BIG-bench 46 = 23 + 23), stated-confidence JSON coverage 100.0 percent
  against the 99.0 floor, `label_from_target` false everywhere.
- **G3 no thinking contamination: PASS.** `enable_thinking` false on every arm
  config and zero think-marker hits across all 15 scored-rows files.
- **G docker digest: PASS.** Live image digest equal to the pinned
  `sha256:f21629b9ae4ed11231768edfaed0f40d41d85d6ea9a71e8096a3d96ea0311772`
  character for character.

Evidential gates, from `analysis-committed/evidential_report_fivearm.json`
(and `g7_A1.json` / `g7_A4.json` for G7):

- **G4 unknown-side behavior transfer: NOT_RUN as registered.** `gates.yaml`
  registers G4 over eight arms and derives its 0.70 Spearman threshold from
  that count; after the registered G1 consequence only five arms exist. The
  pinned scorer's eight-arm requirement therefore refused the gate, and
  `no_goalpost_movement` forbids re-deriving a five-arm threshold after the
  fact. G4 is unadjudicable in this cell, not failed. Two harness gaps are
  recorded for the record and change nothing: the two registered clauses (the
  G1 five-arm reporting consequence and G4's eight-arm instrument) conflict,
  and the pinned `score_g4` never implemented the registered
  `paired_bootstrap_200_resamples_seed_12345` uncertainty, which is moot for a
  gate that did not run.
- **G5 stated-collapse transfer: FAIL.** The gate requires both conditions on
  every arm. Emitted AUROC against appropriateness / emitted standard
  deviation on AmbigQA: A1 0.6023 / 0.0490 pass-pass, A4 0.4530 / 0.0106
  pass-pass, A5 0.5007 / 0.0274 pass-pass, A3 0.3953 / 0.1687 (AUROC passes,
  standard deviation fails the 0.10 ceiling), A8 0.3588 / 0.4238 (same
  pattern). Two of the five surviving arms show real stated-confidence spread
  on AmbigQA, so the collapse does not transfer uniformly. The spread carries
  no positive appropriateness signal: both high-spread arms rank below chance.
- **G6 BIG-bench labeling: read as a labeling gate, not an outcome gate.**
  n = 23 per side. `refusal_recall_pct` 100.0 on all five arms (Wilson 95
  percent interval [85.69, 100.0]); `over_refusal_pct` 43.48 (A1), 47.83 (A3),
  56.52 (A4), 56.52 (A5), 52.17 (A8) with wide Wilson intervals spanning
  roughly 25 to 75 percent. Every rate carries its n and interval and is
  labeled a spot check; no evidential gate reads it.
- **G7 internal readout transfer: FAIL on both panel arms.** Held-out probe
  AUROC at layer 35 on the 2748-row panel: 0.6279 (A1, fold standard deviation
  0.0164) and 0.6349 (A4, 0.0149), both far under the 0.90 floor. The margin
  leg also fails: internal minus same-checkpoint emitted AUROC on the 1832
  shared rows is 0.1326 (A1: internal 0.6319 against emitted 0.4994) and
  0.1379 (A4: internal 0.6412 against emitted 0.5034), under the 0.15 floor,
  with zero rows missing a stated confidence. Panel composition exact on both
  arms (2748 = 1245 known + 1503 unknown).

### Prediction scoring, as worded

The four components of the Prediction section's opening sentence, scored as
worded and numbered as the adjudication entry numbers them:

1. **Unknown-side rank-order transfer at Spearman rho at least 0.70: NOT
   ADJUDICABLE** (G4 NOT_RUN as registered).
2. **The stated-confidence collapse transfers unchanged on every arm: FAILED**
   (G5 FAIL, two arms exceed the standard-deviation ceiling).
3. **The internal known-unknown readout still separates the AmbigQA
   answerability boundary at held-out AUROC at least 0.90 on both panel arms:
   FAILED** (0.6279 and 0.6349).
4. **Known-side over-refusal shifts by more than 10 points on at least one
   surface: SUPPORTED.** Every surviving arm moves more than 10 pp on at least
   one surface against its own committed SelfAware level.

The Prediction section's detail bullets are labelled P1 to P4 but do not map
one-to-one onto these four components: the bulleted P3 is the over-refusal
component scored as 4 above, and the internal-readout component scored as 3
above has no bullet. The bulleted P4, that the answer-supervised versus
answer-masked contrast holds its direction on AmbigQA, is **not recorded** as
scored anywhere in the adjudication entry. What the record does establish is
that A2, the answer-supervised arm (`cell.yaml` `arms`, "Table 1 col 2
(answer-supervised)"), is one of the three arms G1 voided, so its side of that
contrast was never generated.

### Falsifier reading

The registered falsifier required two or more arms on AmbigQA at emitted AUROC
against appropriateness of at least 0.70 together with emitted standard
deviation above 0.15. The two high-spread arms (A3 at 0.1687, A8 at 0.4238)
rank at 0.3953 and 0.3588, below chance, and the highest AUROC on any
surviving arm is A1's 0.6023. **The falsifier DOES NOT FIRE.** Paper 3's
"collapsed near-constant" sentence does not take the registered narrowing.
The G5 failure nonetheless obliges a variance qualifier wherever that collapse
is described as universal across arms.

### Readouts recorded in the notebook but not in a committed artifact

The per-arm, per-surface behavior levels behind the verdict's "behavior
transfers in level" clause live in gitignored eval outputs; only the lead's
2026-08-09T16:45Z adjudication entry in `NOTEBOOK.md` records them, as refusal
recall 93.7 to 97.4 on KUQ, 100.0 on BIG-bench, and 67.9 to 77.5 on AmbigQA,
with the P4 over-refusal shifts against each arm's committed SelfAware level
at BIG-bench -8.6 to -14.9 pp, AmbigQA +7.3 to +11.9 pp, and KUQ +8.0 to +10.3
pp. Also from that entry, explicitly DESCRIPTIVE, UNREGISTERED and UNGATED and
to be labeled as such wherever quoted: the five-arm Spearman of arm rank by
refusal recall against SelfAware is approximately 0.10 on KUQ and 0.20 on
AmbigQA under a plain rank, on SelfAware reference levels compressed into about
6.5 pp with one exact tie, so arm ordering is noise-dominated at that spread.

### Scope limits carried from the signed text

- Tier 2, exploratory. Reported separately from the PROTOCOL v0.3 locked
  headline matrix and never pooled with it or labeled as a headline result.
  This cell re-estimates existing directional claims on new surfaces; it
  promotes nothing, and promotion to a claim requires a confirmatory
  replication registered in advance.
- Per surface, never averaged across surfaces, with each surface's n and class
  denominators attached.
- Three of the eight registered arms were voided before the panel by G1, so
  every reading above is a five-arm reading.
- Construct heterogeneity is real and must be labeled rather than blurred:
  AmbigQA "unanswerable" means ambiguous or underspecified, while SelfAware
  and KUQ "unknown" means unknown to anyone.
- KUQ correctness is unreliable by the loader's own statement, so its
  correctness-dependent metrics are caveated and ungated; BIG-bench is n = 23
  per side, spot check only.
- Single seed, single model: this cell inherits paper 3's seed-1 Qwen3-4B scope
  entirely and broadens the evaluation surface only.
- The internal panel covers two arms and one surface, so the internal-versus-
  stated gap itself is addressed only on AmbigQA and only for the clean-SFT and
  GRPO-v2 checkpoints.
- Three surfaces is not all surfaces.

### Run provenance

The stage-6 extraction runtime was pinned, then superseded twice before first
evidential use (missing `requests`/`peft`, then `pandas`, each fixed generically
in the tuner submodule and pushed before rebuild); zero extraction rows were
produced under either superseded digest, and the digest of record is
`experiment.yaml` `instrument.runtime_image_digest`
(`sha256:2471502c...`), governing the stage-6 extract verb only. Eval-lane
stages 2 to 5 ran under `cell.yaml` `lane.docker_digest` as registered. At
stage 8 the pinned `gate_score.py` was found to gate its evidential block on a
flat `all()` over integrity gates, which contradicts `gates.yaml` scoping G1's
failure to voiding three arms; the lead adjudicated this a pinned-script defect
against the registration and remedied it with `score_evidential_fivearm.py`,
which imports and calls the pinned scoring functions unchanged and bypasses
only the flat short-circuit. No threshold, formula, seed, or population was
altered, and its run reproduced the integrity statuses verbatim.
