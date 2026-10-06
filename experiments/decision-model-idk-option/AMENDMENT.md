---
amendment: decision-model-idk-option
slug: decision-model-idk-option
tier: 2
posture: exploratory
question: >-
  Given an explicit "I don't know" option added at analysis time, and with no
  further training, do the existing PopQA decision models pick it when the
  base torso truly does not know (cannot recall or recognize the answer) and
  not when it knows, and does the option beat a confidence threshold at a
  matched over-abstention rate?
predictions:
  orchestrator:
    who: the orchestrating AI agent (not the PI)
    call: "IDK recall sometimes (10-50%); over-IDK almost never (< 5%); known-recognized mostly answers; threshold better than IDK option"
    confidence: "not stated"
    recorded: 2026-10-05
    basis: >-
      The models never saw an IDK option in training, and the pointer head
      scores each option line's content against the answer state, so IDK
      should win mainly when every real option scores poorly, not on most
      unknowns. The same reason gives "threshold better".
    quote: >-
      IDK recall on unknown-true: "Sometimes (10–50%)". Rationale: the models
      never saw an IDK option in training, and the pointer head scores each
      option line's content against the answer state, so IDK should win
      mainly when every real option scores poorly, not on most unknowns.
      Over-IDK on known: "Almost never (< 5%)". Known-recognized: "Mostly
      answers". IDK option vs confidence threshold: "Threshold better", for
      the same reason as the IDK-recall rationale.
  user:
    call: "H1 mostly (>= 50%); over-IDK some (5-20%); known-recognized mostly answers; IDK option better than threshold"
    recorded: 2026-10-05
    selected_from: candidate outcomes listed by the orchestrator, which recommended none
    quote: >-
      1. IDK recall on truly unknown questions: "Mostly (≥ 50%)". Its
      confidence already tracks knowledge, so with a way out it takes it on
      most true unknowns. 2. Over-IDK on known questions: "Some (5–20%)". IDK
      leaks onto known questions at a noticeable rate. 3. Known-recognized
      questions: "Mostly answers". Recognition is enough; it picks the
      (usually right) answer over IDK. 4. IDK option vs confidence threshold:
      "IDK option better". At the same over-IDK rate, the explicit option
      catches more true unknowns.
outcome: pending
scoreboard:
  user: pending
  orchestrator: pending
---

# Decision-model IDK option: with no further training, do decision models pick an explicit I don't know when the base torso truly does not know?

Status: draft (not signed; do not launch as confirmatory evidence). Nothing
in this cell has been run on a GPU. Drafted 2026-10-05 for the PI.

Keep this document the prose home for the experiment. The machine state lives
in `experiment.yaml` and is never duplicated here.

**Short name:** decision-model-idk-option (dmio)

**Scope:** one exploratory evidence cell. A new labeling stage splits the
predecessor cell's base-model "unknown" rows by whether the base model can
*recognize* the answer on a 4-way multiple choice. The two existing decision
models are then re-read, without any training, on the same rows with one
extra option, "I don't know", placed in turn at each of the five option
positions, and compared with a calibrated-confidence threshold on the same
rows without that option. The unit of analysis is the question.

**Session note:** none opened for this draft; the lead adds a checkpoint at
sign-off (protocol-amendments.md workflow step 8).

## Motivation and posture

`experiments/decision-model-calibrated-choice/` (dmcc; signed `1387e92d`, run
2026-10-05, resolution pending with the PI) found that the pointer decision
model's calibrated confidence ranks base-model known above unknown rows at
AUROC 0.9407, but sits 0.1769 above chance on unknowns (H-A FAIL). Its
post-hoc note on H-A named the reason this cell exists: the dmcc "unknown"
label measures *recall* failure (0 of 32 sampled generations correct), and on
a 4-way choice the model can still *recognize* the answer or eliminate the
distractors. Unknown-row accuracy was 0.383 against 0.25 chance.

A decision model cannot refuse: it always returns one of the listed options.
The simplest way to give it a way out is to list one. This cell asks whether
the trained models, with no training on such an option, take it where the
base torso truly does not know, and leave it alone where the torso knows. It
also asks whether that explicit option does better than the obvious
alternative, abstaining when calibrated confidence is low.

"Truly does not know" needs a recognition measurement that is independent of
the decision model. Using the decision model's own correctness to define the
population would be circular: dmcc already showed its unknown-row accuracy
moves with recognition, and any population cut on that accuracy would select
on the outcome. So recognition is measured on the BASE model, with no
adapter, by a separate pre-registered instrument (Design / Recognition).

Posture: EXPLORATORY tier-2 Amendment (a new evidence cell). Reported
separately from the locked headline matrix and never pooled with it. Single
checkpoint per arm, no seeds.

## Relationship to existing protocols

- Additive. Touches neither PROTOCOL v0.3's locked matrix nor any signed
  amendment's gates. No headline claim is made or changed.
- **Depends on dmcc, which is not on `origin/main`** at drafting time (local
  branch `amendment-decision-model-calibrated-choice`, signed commit
  `1387e92d`, branch not pushed; its run results are uncommitted in that
  worktree). This cell does not stack on dmcc's branch. It reads dmcc's
  gitignored artifacts by absolute path and sha256 (cell.yaml `predecessor`),
  copies them into its own gitignored `analysis/dmcc_inputs/`, and refuses on
  any digest mismatch. Nothing in the EH rules read for this draft requires
  the predecessor to be merged first; the operator-discipline rule is that a
  file must be committed or copied before another worktree references it,
  and this cell copies and hashes. One dependency is on uncommitted bytes:
  dmcc's `analysis-committed/label_and_split_counts.json` (digest
  `f347db21...`). If dmcc's commit changes those bytes, this cell's pin is
  updated before sign.
- The promotion rule (`experiments` skill) does not move anything to
  `experiments/common/` yet: the consumed artifacts are gitignored row-level
  data that may not be committed, and the shared code (EH `normalize_answer`,
  Amendment Y's exemplars) is already common. If a third experiment consumes
  dmcc's rows, the lead should promote a committed manifest of them.
- Reuses, unchanged: dmcc's 12,067 primary decision rows, its known/unknown
  labels, its FIT/CAL/TEST split, its exclusions (dmcc's recall-ambiguous
  rows and the 27 exemplar-collision "AU" rows were dropped before dmcc's
  split, so they are absent here too), and both decision checkpoints
  (tree digests in cell.yaml).
- Amendment Y (`experiments/pretrain-only-base-readout/AMENDMENT.md` section
  6) requires the base-mode k-shot surface, not a chat template, for
  pretrain-only bases. The recognition stage prompts Qwen3.5-2B-Base, so it
  uses Y's surface in multiple-choice form, with Y's five exemplar questions
  and answers byte-identical (a test pins them to
  `experiments/common/readouts/amendment_x_cross_model_extract.py`). dmcc
  applied the same rule to its labeling (its pre-sign checklist item 10).
- Calls the tuner's generic decision-analysis CLI
  (`Trainers/decision/analyze_confidence.py`) through `tuner.py local-run`
  and materialized recipes, never by import (no-pollution rule).
- Supersedes nothing. dmcc's verdicts are not revisited.

## Prior exposure (disclosed before sign; binding on interpretation)

Verbatim, as the orchestrator stated it for the PI:

1. dmcc's no-IDK decision outputs on these exact rows have been observed:
   accuracy, confidence, and per-group results including "unknown accuracy
   0.383, mean confidence 0.427". The IDK-option condition and the
   recognition labels have NOT been observed.
2. The recognition idea came from dmcc's post-hoc H-A observation.

Added by the drafter:

3. Everything in dmcc's Outcome section (uncommitted working tree,
   2026-10-05) was read while drafting, including: TEST known 514 / unknown
   4,314; pointer known accuracy 0.9689 and mean R1 0.7534; unknown accuracy
   0.3832 and mean R1 0.4269; H-C AUROC 0.9407; underconfident-right on known
   0.0603; per-relation unknown accuracy ranging 0.28 to 0.85; and the same
   blocks for the letter-logit arm. The H2 cap (0.10) is dmcc's known-row
   cap carried over by rule, not chosen from these numbers (Gates).
4. The drafter ran three CPU-only stages of this cell's harness on
   2026-10-05 as the pre-sign feasibility probe that
   amendment-vs-lab-notebook.md requires (NOTEBOOK): `import-dmcc`,
   `build-recognition` and `build-idk-rows`. They read dmcc's rows (question
   text, options, gold labels, dmcc's known/unknown label) and PopQA meta.
   No model was loaded, no recognition score exists, and no per-row decision
   output was opened (dmcc's two `test_rows.jsonl` files were hashed, not
   read).
5. The drafter also ran a no-model collision probe over every dmcc primary
   row to choose exemplar distractors (NOTEBOOK). It looked only at option
   and alias strings.
6. The PI's four predictions (2026-10-05, verbatim under Predictions
   scoreboard) were in the drafter's hands before the gate thresholds were
   written. See Gates, "Threshold provenance".

## Design

### Populations (all on dmcc's rows and split)

| Group | Definition | Role |
|---|---|---|
| known | dmcc label known (greedy correct and >= 16/32 sampled correct) | H2 population; R0 positive control |
| unknown-true | dmcc unknown (0/32) AND recognition c = 0 of 4 | H1 and H3 population |
| known-recognized | dmcc unknown AND c >= 3 of 4 | H4, descriptive |
| recognition-ambiguous | dmcc unknown AND c in {1, 2} | reported, excluded from every gate |

dmcc's recall-ambiguous rows (2,187) are not in dmcc's primary rows and stay
excluded. Expected TEST sizes: known 514 (fixed by dmcc); the three
recognition groups partition dmcc's 4,314 TEST unknowns, in proportions no
one has measured.

### Recognition labeling (new; base model, no adapter)

- **Model.** `Qwen/Qwen3.5-2B-Base` @ `b1485b2fa6dfa1287294f269f5fb618e03d52d7c`,
  the decision models' torso, no adapter, bf16, `Qwen3_5ForCausalLM` under
  transformers 5.17.0 in dmcc's pinned runner image
  (`mechinterp-runner:dmcc-tf5.17.0`, Image ID `sha256:b4166dbd...`). One
  prompt per forward pass (batch size 1): no padding and no batch-composition
  effects.
- **Rows.** Every dmcc primary row (12,067). Unknown rows are labeled; known
  rows are the positive control (R0-V1).
- **Options.** The same 4 options as the row's decision prompt (gold plus
  dmcc's 3 same-relation distractors), with NO IDK option.
- **Orderings.** The 4 cyclic rotations of the decision row's canonical
  option order: ordering k shows options k, k+1, k+2, k+3 (mod 4). The gold
  option sits at every letter exactly once across the 4 orderings.
- **Prompt.** Amendment Y's base-mode 5-shot surface in multiple-choice
  form. Each exemplar renders as `Q: <question>\nA. <opt>\nB. <opt>\nC. <opt>\nD. <opt>\nA: <letter>\n\n`;
  the target ends at the answer cue `A:`. The five exemplar questions and
  gold answers are Y's (Jupiter, Six, Au, 1945, Mount Everest). The
  distractors are hand-written (cell.yaml). Exemplar gold letters are B, D,
  A, C, B: not balanced, which is why the target's position is rotated.
- **Answer per ordering.** The argmax of the next-token logits over the four
  tokens " A", " B", " C", " D" (each must encode to one token; the worker
  refuses otherwise). Exact ties go to the lowest letter and are counted.
- **Rule.** c = the number of orderings (of 4) whose argmax is the gold
  option. known-recognized: c >= 3; unknown-true: c = 0;
  recognition-ambiguous: c in {1, 2}.
- **Chance.** Under uniform independent guessing in each ordering,
  c ~ Binomial(4, 1/4): P(c >= 3) = 13/256 = 0.0508, P(c = 0) = 81/256 =
  0.3164, P(c in {1, 2}) = 0.6328. A responder that always picks the same
  letter gets c = 1 on every row and is always recognition-ambiguous, so pure
  position bias cannot create either primary group.
- **What "unknown-true" means, stated.** c = 0 is "no evidence of
  recognition in 4 tries", not proof of ignorance. About 32% of pure guessers
  land there by chance, and a model drawn consistently to one wrong
  distractor (a lure) lands there too. That is the intended population: rows
  where the torso neither recalls nor reliably picks the answer.
- **Exemplar/PopQA overlap check** (pre-sign, no model). None of Y's
  exemplar questions is a PopQA question (dmcc's check, repeated). No
  normalized exemplar option text (20 strings) equals a normalized gold
  alias or option text of any dmcc primary row. Some exemplar distractors
  (Five, Seven) are PopQA *subjects* (work titles), which appear in question
  text only; reported, not excluded.
- **Pre-registered exclusion.** A primary row is excluded from every
  recognition-defined group iff any normalized exemplar option text equals a
  normalized gold alias or option text of that row. Pre-sign count: 0
  (`gates.yaml g0_exemplar_option_collision_exclusion.expected_count: 0`;
  `build-recognition` refuses on any other count).
- **Independence from the decision model.** The labels come from the base
  model alone. They are frozen (`analysis-committed/recognition_freeze.json`,
  labels sha256) before any decision-model run of this cell is staged;
  `stage-engine` and `analyze` refuse without the marker.
- **Instrument validity (R0).** V1, positive control: on all dmcc-known rows
  (n = 1,307), the share with c >= 3 must have a Wilson lower bound >= 0.80.
  These are answers the base model already generates; a recognition probe
  that misses more than one in five of them is not measuring recognition.
  V2, format adherence: at least 95% of all 48,268 prompts must have one of
  the four letter tokens as the full-vocabulary top-1 next token. If R0
  fails, H1, H3 and H4 are NOT-ADJUDICABLE; H2 does not depend on
  recognition.

### The intervention: an "I don't know" option (analysis time only)

- **Text.** `I don't know` (ASCII apostrophe U+0027), empty description. The
  engine renders option lines as `<marker>. <name>`, so the line reads
  `3. I don't know` for the pointer model (number markers) and
  `C. I don't know` for the letter-logit model (letter markers). It is a
  normal option line; nothing else in the prompt changes (pre-sign render
  check).
- **Position control: all five positions** (PI decision 2026-10-05, before
  any outcome). Every question is run five times, with the IDK option at
  canonical index 0, 1, 2, 3 and 4 in turn. The four real options keep
  dmcc's relative order in every copy; the gold index shifts by one when the
  IDK position is at or before it. The engine renders canonical order at
  eval (option shuffling happens only in training collate), so the canonical
  index is the rendered position. Position effects therefore cancel in each
  question's rate instead of adding noise, and they are measured directly
  (Secondary, position bias).
- **Runs.** One engine run per IDK position per model, each over all 12,067
  rows, so every run keeps dmcc's exact FIT/CAL/TEST split (TEST and CAL are
  the scored splits; FIT is needed only because the engine fits its probes
  there). The no-IDK baseline is unchanged: one run per model, one copy per
  question.
- **Split identity.** The engine's FIT/CAL/TEST split depends only on row
  order and task, which are unchanged. The ported split of each position's
  rows equals dmcc's `splits.json` (checked in `build-idk-rows` and in
  tests); G0 re-checks it against every engine output.
- **Unit of analysis: the question.** A question's IDK rate is the mean of
  its 5 pick-IDK indicators, in [0, 1]. Every IDK statistic (H1 to H4, the
  3-way breakdowns) averages question-level values, and its CI comes from a
  cluster bootstrap that resamples questions, never copies.
- **No training, no prompt changes.** Same checkpoints, same instructions
  ("Which option correctly answers the question in the state?"), same
  header, same engine config apart from the rows.
- **Abstention.** Picking IDK = the decision model's argmax option is the
  IDK option. Argmax does not depend on the temperature, so R0 and R1 agree.
  This is a closed-class option choice, not text. The abstention-grading
  rule (`.skills/experiment-runner/reference/abstention-grading.md`: frozen
  detector plus blinded adjudication lane) governs free-text abstention and
  has nothing to grade here; it does not apply, and no rubric is needed.
  "IDK option" is used deliberately: "IDK switch" is reserved for the
  validated Qwen3.5-4B actuator (`papers/common/terminology.md`).

### Arms and engine runs

Twelve read-only runs of `analyze_confidence.py`: per model (pointer
PRIMARY, letter-logit SECONDARY), 5 IDK runs (one per IDK position) and 1
no-IDK run. The no-IDK runs recompute dmcc's analysis on identical rows under
this cell's engine pin, because H3 needs CAL per-row records that dmcc's pin
did not export. dmcc's own TEST outputs are used only for a descriptive
reproduction check. The analysis configs equal dmcc's except the staged rows,
the run paths, `export.cal_rows` and the absent `directions:` block.

The 5 IDK runs of a model share one pinned template pair
(`analysis_idk_<model>.yaml`, `recipe_idk_<model>.yaml`, written for
position 0, run_id `dmio-idk-p0-<model>`). `stage-engine --run
idk_p<k>_<model>` materializes position k by replacing that run_id with
`dmio-idk-p<k>-<model>` (nothing else changes; the staged rows file has the
same name at every position) and records the sha256 of the template and of
each materialized file in the run record. A test checks that every
materialized config points only at its own staging directory, and the
engine `--dry-run` accepted a materialized position-3 config for both models
(NOTEBOOK).

### Engine capability: CAL per-row export (generic tuner feature)

- **Needed:** per-row records for the CAL split. At `29f7af0c`,
  `confidence_analysis.analyze` writes per-row records for TEST only
  (`test_rows.jsonl`). H3 fits its cutoff on CAL known rows and needs, for
  both arms, each CAL row's `pred`, `correct`, `conf_r1` and `meta`.
- **Feature (PI decision 2026-10-05: fit the H3 cutoff on CAL):** a generic
  `export.cal_rows` option, added in the tuner by a tuner agent (no
  EH-specific logic), that writes `cal_rows.jsonl` beside `test_rows.jsonl`
  with the same per-row schema plus a `split` field (`"cal"` / `"test"`).
  All four analysis configs set `export.cal_rows: true`.
- **Wiring.** `collect` refuses an engine output without `cal_rows.jsonl`,
  and G0 checks that its qids equal dmcc's CAL split (`split == "cal"` on
  every row). A missing export is therefore an integrity failure, never a
  designed NOT-ADJUDICABLE for H3.
- **Pin.** Landed as tuner `e51a802b` (branch
  `jev-models-tuner-training-b55d92`, pushed): `export.cal_rows` and
  `export.fit_rows` on top of dmcc's `29f7af0c`; TEST and CAL records carry
  `split`, CAL `row_index` is CAL-relative, and CAL R1 uses the same CAL-fit
  temperatures. cell.yaml `engine.commit` and the submodule gitlink are at
  `e51a802b`.
- **Not needed (done cell-side):** multi-valued knowledge groups. The rows
  keep dmcc's binary `meta.knowledge`, so the engine's own knowledge block
  behaves as in dmcc (descriptive only here). Recognition groups are joined
  by qid in `score`. The extra option is just an option in the row.

### Lane, runtime and timing

- Local RTX 3090, one GPU job at a time. Recognition in
  `mechinterp-runner:dmcc-tf5.17.0` from WSL against the Docker Desktop
  daemon (`docker --context default`); engine runs in
  `unsloth/unsloth@sha256:0b8efd89...` via `py.exe -3.11 tuner.py local-run`
  (dmcc's working launch path).
- Estimates, to be replaced by the smoke's measurement:
  - Recognition: 48,268 single forwards of roughly 250-token prompts on a
    2B model, about 20 to 40 ms each, so about 15 to 35 min plus model load.
  - Engine: 12 runs. dmcc's runs took 17 min each (2026-10-05, 12,067
    four-option rows, all layers captured). The IDK runs add one short option
    line, so assume about 17 to 20 min each: about 3.4 to 4 h for all 12
    (5x the IDK decision passes of the one-slot draft), plus container
    start-up per run.
  - Total GPU time about 4 to 4.5 h, run as separate stages.
- Long stages are launched detached (a tool background task dies at 2 h).
  Each engine run is its own `analyze` invocation, well under 2 h, so a kill
  loses one run; the recognition append-log resumes after a kill.

### Implementation boundary

Pinned at sign: `cell.yaml`, `gates.yaml`, `analysis_{idk,noidk}_{pointer,letter_logits}.yaml`
(the two `idk` files are the position templates),
`recipe_{idk,noidk}_{pointer,letter_logits}.yaml`, `idk_harness.py`. Tests:
`tests/test_recognition_rule.py`, `tests/test_idk_insertion.py` (44 pass).
Materialized per-position recipes are written to gitignored
`analysis/engine_recipes/` and their digests go in the run records.
Containment: prompts, question and option text, recognition logs and
row-level outputs stay in gitignored `analysis/`. Only counts, aggregate
statistics, verdicts, the recognition freeze marker and run records go
under `analysis-committed/`. No committed file under `synaptic-tuner/` apart
from the gitlink.

## Prediction

Registered hypotheses (the manifest's `prediction:` condenses them). Pointer
model PRIMARY; letter-logit model SECONDARY with identical gates, labelled
exploratory, no multiplicity correction. All on TEST.

- **H1 (IDK recall):** the mean question-level IDK rate over unknown-true
  questions is >= 0.50.
- **H2 (over-IDK):** the mean question-level IDK rate over known questions
  is <= 0.10.
- **H3 (IDK option vs confidence threshold):** at a matched over-abstention
  rate on known questions, the IDK option's question-level recall on
  unknown-true exceeds the threshold baseline's (paired question-level
  difference, CI above 0).
- **H4 (descriptive):** on known-recognized questions, the question-level
  IDK rate and accuracy among non-IDK answers, reported without a gate.

H1 and H2 are EH's refusal pair (refusal recall on unknowns, over-refusal on
knowns), here with "pick IDK" as the refusal. They are reported as a pair and
never averaged.

## Falsifier

- The selective-IDK-use line is falsified if H1 FAILS (cluster-bootstrap CI
  upper bound of the mean question IDK rate on unknown-true < 0.50) or H2
  FAILS (CI lower bound of the mean question IDK rate on known > 0.10), on
  the primary pointer arm.
- The IDK-beats-threshold line is falsified if H3, adjudicable with matched
  operating points, is THRESHOLD_BETTER (paired CI upper bound < 0).
  NO_DIFFERENCE_DETECTED (CI contains 0) is reported as such: neither
  support nor falsification.

## Gates

Pre-stated in `gates.yaml`, fixed at signing, never retuned. **The PI
confirmed the drafted thresholds on 2026-10-05, before any outcome** (H1
>= 0.50, H2 <= 0.10, H3 CI > 0, the CI-straddle INCONCLUSIVE rule, R0 floors
0.80 / 0.95). The same day, also before any outcome, the PI replaced the
one-slot design with all five IDK positions and copy-level Wilson CIs with
question-level cluster-bootstrap CIs; the thresholds did not change.

| Gate | Statistic (TEST population) | PASS | FAIL | CI |
|---|---|---|---|---|
| G0 integrity | dmcc input digests, split identity (TEST and CAL, all 6 runs per model), engine commit, checkpoint digests, IDK row shape and every question at all 5 positions, recognition frozen before analysis | all hold | any fails: scoring refuses | n/a |
| G0 collision count | exemplar-option collisions | = 0 | otherwise: stop, consult PI | n/a |
| G0 floors (questions) | known >= 150; unknown-true >= 150; CAL known >= 100 | met | not met: the gates using that population NOT-ADJUDICABLE | n/a |
| R0-V1 | share of all dmcc-known rows with c >= 3 | Wilson lo >= 0.80 | otherwise: R0 not valid | Wilson |
| R0-V2 | share of prompts with a letter as top-1 token | point >= 0.95 | otherwise: R0 not valid | n/a |
| H1 | mean question IDK rate, all unknown-true questions | CI lo >= 0.50 | CI hi < 0.50 | cluster bootstrap over questions |
| H2 | mean question IDK rate, all known questions | CI hi <= 0.10 | CI lo > 0.10 | cluster bootstrap over questions |
| H3 | question-level IDK recall - threshold recall, unknown-true, at CAL-matched question-level over-abstention | CI lo > 0 (IDK_BETTER) | CI hi < 0 (THRESHOLD_BETTER) | paired cluster bootstrap |
| H4 | question IDK rate and answered accuracy, known-recognized | descriptive | descriptive | cluster bootstrap |

H1 and H2 also report, as secondaries, the share of questions with IDK
chosen in >= 3 of 5 positions (Wilson).

- **INCONCLUSIVE rule:** a gate whose 95% CI contains its threshold is
  INCONCLUSIVE and reported as such. For H3 the threshold is 0 and the label
  is NO_DIFFERENCE_DETECTED.
- **NOT-ADJUDICABLE** (distinct from PASS, FAIL and INCONCLUSIVE): a floor
  fails; R0 is not valid (H1, H3, H4); for H3 also when the operating points
  are not matched on TEST (below). A G0 integrity failure (which covers every
  run's TEST and CAL per-row records and all five positions) stops scoring
  altogether and is reported as such.
- **H3 baseline and cutoff (PI decision 2026-10-05: fit on CAL).** Baseline:
  the no-IDK arm, abstaining iff its calibrated max option probability
  R1 < tau; each question's baseline abstention is 0 or 1. Cutoff: fit on
  CAL to match the IDK arm's CAL question-level over-IDK rate, not a fixed
  value. A fixed value would put the two arms at different over-abstention
  rates, and the comparison would then mix a recall difference with a cost
  difference. The fit uses CAL known questions only: r_cal = the IDK arm's
  mean question-level IDK rate over CAL known questions; sort the no-IDK
  arm's CAL-known R1 ascending s_1 <= ... <= s_n; k = round(r_cal n);
  tau = s_(k+1) (+inf if k = n). No unknown question and no TEST question
  enters the fit. On TEST, the operating points count as matched iff the
  paired question-level bootstrap 95% CI of (baseline over-abstention -
  IDK-arm question-level over-IDK) on known questions contains 0; otherwise
  H3 is NOT-ADJUDICABLE and only the descriptive TEST-matched comparison is
  reported. The H3 statistic is the mean over unknown-true questions of
  (question IDK rate - baseline abstention indicator), with a paired
  question-level bootstrap CI. tau is held fixed in the bootstrap, so CAL
  uncertainty is not propagated (stated limitation). CAL has 268 known
  questions.
- **Diagnosticity.** The IDK option is in every copy, so every known
  question is exposed to it (fired fraction 1.0): H2 has no undosed-denominator problem
  (gate-diagnosticity.md). H1 alone would pass for a model that picks IDK
  everywhere; H2 is the guard, which is why the two are read as a pair.
- **Floor derivation.** Floors count questions, so the five-position design
  does not change them. A question's IDK rate lies in [0, 1], so its variance
  is at most 0.25, the Bernoulli maximum; the cluster-bootstrap CI of the
  mean is therefore no wider than a Bernoulli interval on the same number of
  questions, and the repeated positions can only narrow it. The Wilson
  arithmetic still bounds the floors. H1, at threshold 0.50: a mean 0.10 from
  the threshold resolves from about 91 questions; the floor of 150 adds
  margin (half-width at most 0.080). H2, cap 0.10: 150 is dmcc's floor; TEST
  known is fixed at 514 questions, where a mean of 0.05 has a half-width of
  at most about 0.019. A percentile bootstrap near 0 can be narrower than
  Wilson; at 514 questions that matters for H2 only within about 0.02 of the
  cap (stated, not corrected). CAL known >= 100 for the cutoff fit (268
  available). For predictions on H4 (no gate), known-recognized needs
  n >= 50 questions to be scored.
- **Threshold provenance (disclosure).** The PI's predictions reached the
  drafter before the thresholds were written. Each threshold comes from the
  rule stated beside it and was not adjusted toward the predictions:
  - H1 0.50 is the majority rule the question implies ("picks it when the
    torso does not know" = the IDK option is its answer on more than half of
    such rows). It coincides with the boundary of the PI's candidate band
    ">= 50%" because both use the majority boundary.
  - H2 0.10 is dmcc's known-row cost cap (H-B) carried over unchanged. It
    falls inside the PI's predicted band (5-20%), so prediction 2 is scored
    on the over-IDK statistic itself, not on the H2 verdict.
  - H3 has no free threshold (the sign of a paired difference).
  - R0 thresholds (0.80, 0.95) are instrument-validity floors stated with
    their reasons in gates.yaml.
  The PI confirmed the thresholds as drafted on 2026-10-05, before any
  outcome.

## Interpretation matrix (fixed before any number exists)

| | H2 PASS (few knowns lost) | H2 FAIL |
|---|---|---|
| **H1 PASS** | selective IDK use: taken on most true unknowns, rarely on knowns | IDK over-attracts: taken on most true unknowns, and on knowns above the cap |
| **H1 FAIL** | IDK under-used: the model keeps answering on true unknowns | IDK use not knowledge-selective |

Any INCONCLUSIVE or NOT-ADJUDICABLE input leaves its cell unresolved; it is
never rounded to a neighbor. H3 and H4 are read beside the matrix, not in it.

## Secondary (descriptive only; no gate)

- Per group (known, unknown-true, known-recognized, recognition-ambiguous,
  all dmcc-unknown), question-level: IDK rate, share with IDK in >= 3 of 5
  positions, accuracy among non-IDK answers, mean calibrated IDK mass.
- Unknown-true 3-way breakdown, question-level: each question's picked-IDK /
  answered-right / answered-wrong shares (summing to 1), averaged over
  questions with cluster-bootstrap CIs.
- **Position bias.** Pick-IDK rate at each IDK position 1 to 5 (one copy per
  question per position; Wilson), pooled over all TEST questions and per
  group, plus the position x group table. A range (max - min over positions)
  of 0.10 or more within a group is flagged as a strong position effect; a
  flag on the pooled, known or unknown-true rows is reported as a caveat
  beside H1 and H2. It changes no verdict.
- Calibration of the IDK-option distribution: AUROC of each question's mean
  calibrated IDK mass for unknown-true vs known, with a bootstrap CI, and its binary ECE
  (15 bins) against the unknown-true indicator.
- Answer change vs the no-IDK arm among non-IDK copies, per group (does the
  extra option move answers?).
- Threshold curve: baseline recall on unknown-true vs over-abstention on
  known at R1 cutoffs, with the IDK arm's operating point; and the
  TEST-matched comparison (never a verdict).
- Reproduction of dmcc: no-IDK arm vs dmcc's TEST outputs (prediction
  agreement, max abs R1 difference).
- Recognition: c distribution by dmcc label and split, argmax ties,
  per-letter pick shares, chance reference.
- The letter-logit arm: every gate above, labelled exploratory.

## Rerun / launch policy

- Nothing here is launched from this draft. Every GPU stage
  (`recognize-smoke`, `recognize`, `analyze --run <key>`) needs explicit PI
  launch approval naming the stage and run; the harness also requires
  `--i-know-this-runs-on-gpu`.
- Order is enforced in code: import-dmcc -> build-recognition ->
  recognize -> recognition-labels (freeze) -> build-idk-rows (5 position
  files) -> stage-engine / analyze / collect per run key (12) -> score per
  model.
- GPU smoke before the full recognition run (standing directive 2026-07-16):
  `recognize-smoke` on cell.yaml's 8 non-PopQA items x 4 orderings, twice
  (format adherence, single-token letters, repeat identity, throughput), and
  an engine `--dry-run` on the staged IDK rows inside the pinned engine
  image. Each is a tier-3 NOTEBOOK entry. A smoke FAIL is a gate event for
  the lead, not a retry.
- A crash is re-run as tier-3 recovery. `recognize` resumes from its
  append-log.
- Out of scope: any training on an IDK option, prompt or instruction changes,
  free-text abstention, other datasets, other models. Each needs its own
  amendment.

## Pre-sign checklist (the cell cannot be signed until each item is closed or waived in writing by the PI)

1. **Engine CAL per-row export. CLOSED** (2026-10-05). PI chose the CAL-fit
   cutoff; tuner `e51a802b` adds `export.cal_rows`; engine and gitlink
   repinned. Engine `analyze_confidence.py --dry-run` (host Python, no model
   load) accepted the IDK and no-IDK pointer configs with
   `export.cal_rows: true`; split counts FIT 4,829 / CAL 2,410 / TEST 4,828,
   equal to dmcc's.
2. **IDK render check. OPEN.** Inside the pinned engine image, render staged
   IDK rows at all 5 positions through the engine's own prompt path for both
   models; confirm the `<marker>. I don't know` line at the intended
   position, the pointer span is non-empty, and the 5 markers resolve to
   single tokens for the letter-logit model. The host `--dry-run` of the
   templates and of a materialized position-3 config already passed
   (split counts equal dmcc's); repeat it inside the image on staged rows.
3. **Recognition smoke on non-PopQA items. OPEN.** `recognize-smoke`:
   letters single-token, V2-style format adherence on the smoke set, repeat
   identity of logits, seconds per prompt.
4. **Recognition kill-resume drill. OPEN.** Kill `recognize` after the first
   lines; resume; no duplicate keys; pre-kill lines unchanged.
5. **Timing estimate. OPEN.** Replace the Lane estimate (about 4 to 4.5 h:
   12 engine runs plus recognition) with the smoke's measured recognition
   rate and the first engine run's wall time.
6. **Pins. PARTLY CLOSED.** dmcc input digests verified by `import-dmcc`
   (2026-10-05). Open: runner Image ID equals `runtime_image_digest`
   (`docker image inspect`); `bin/exp doctor decision-model-idk-option`
   after staging (checkpoint tree digests); the dmcc
   `label_and_split_counts.json` digest after dmcc's results commit.
7. **Feasibility probe. CLOSED** (NOTEBOOK 2026-10-05, no model):
   collision count 0; 48,268 recognition prompts over 12,067 rows; IDK rows
   built at all 5 positions, each with a ported split identical to dmcc's.
8. **Predictions and thresholds. CLOSED.** PI and orchestrator predictions
   recorded 2026-10-05 (verbatim below). PI confirmed the drafted thresholds
   on 2026-10-05.
9. **Design choices. CLOSED** (PI, 2026-10-05, before any outcome): H3
   cutoff fit on CAL; IDK at all five positions with the question as the
   unit of analysis; R0 floors 0.80 / 0.95 confirmed.

## Predictions scoreboard

| Predictor | Call |
|-----------|------|
| orchestrator (the orchestrating AI agent, 2026-10-05; not the PI) | 1. IDK recall on unknown-true: "Sometimes (10–50%)". Rationale: the models never saw an IDK option in training, and the pointer head scores each option line's content against the answer state, so IDK should win mainly when every real option scores poorly, not on most unknowns. 2. Over-IDK on known: "Almost never (< 5%)". 3. Known-recognized: "Mostly answers". 4. IDK option vs confidence threshold: "Threshold better", for the same reason as the IDK-recall rationale. |
| user (PI, 2026-10-05) | 1. IDK recall on truly unknown questions: "Mostly (≥ 50%)". Its confidence already tracks knowledge, so with a way out it takes it on most true unknowns. 2. Over-IDK on known questions: "Some (5–20%)". IDK leaks onto known questions at a noticeable rate. 3. Known-recognized questions: "Mostly answers". Recognition is enough; it picks the (usually right) answer over IDK. 4. IDK option vs confidence threshold: "IDK option better". At the same over-IDK rate, the explicit option catches more true unknowns. |

Recording notes (PI prediction):

- Recorded verbatim as the PI's own predictions, dated 2026-10-05. The PI
  chose them from candidate outcomes the orchestrator listed, without a
  recommendation from the orchestrator.
- All four are scored on the PRIMARY pointer arm only. NOT-ADJUDICABLE or an
  unresolved statistic scores a TIE (protocol-amendments.md).
- **1 -> H1** (mean question-level IDK rate on unknown-true). Supported by
  H1 PASS (cluster-bootstrap CI lower bound >= 0.50). Contradicted by H1
  FAIL (CI upper bound < 0.50). INCONCLUSIVE: TIE.
- **2 -> the H2 statistic (mean question-level IDK rate on known), not the
  H2 verdict.** The H2 cap (0.10) lies inside the predicted band, so both H2
  PASS and H2 FAIL are compatible with it. Supported if its
  cluster-bootstrap 95% CI lies inside [0.05, 0.20]. Contradicted if the CI
  upper bound is below 0.05 ("none") or the lower bound is above 0.20 ("a
  lot"). Otherwise TIE.
- **3 -> H4 (descriptive).** "Mostly answers" means a mean question-level
  IDK rate on known-recognized below 0.50. Supported if its
  cluster-bootstrap CI upper bound is < 0.50; contradicted if the lower
  bound is > 0.50. The parenthetical "(usually right)" is scored too:
  contradicted if the CI upper bound of the mean question-level accuracy
  among non-IDK answers on known-recognized is < 0.50. Either contradiction
  scores the call wrong. Needs n >= 50 known-recognized TEST questions and
  R0 valid; otherwise TIE.
- **4 -> H3.** Supported by IDK_BETTER. Contradicted by THRESHOLD_BETTER.
  NO_DIFFERENCE_DETECTED or NOT-ADJUDICABLE (including a missing engine CAL
  export, which G0 treats as an integrity failure, or unmatched operating
  points): TIE.
- Joint reading: calls 1 and 2 together are compatible with two matrix
  cells, "selective IDK use" (over-IDK 0.05 to 0.10) and "IDK
  over-attracts" (over-IDK 0.10 to 0.20).
- Metric note (2026-10-05): with the five-position design every mapping
  above is on question-level rates with cluster-bootstrap CIs, replacing the
  copy-level Wilson CIs of the first draft. The predictions themselves are
  unchanged.

Recording notes (orchestrator prediction):

- Recorded verbatim as the orchestrating AI agent's prediction, dated
  2026-10-05, separate from the PI's. Recorded after the gate thresholds
  were drafted; not used to set them.
- It disagrees with the PI on IDK recall (call 1) and on H3 (call 4). It
  also differs on over-IDK (call 2: < 5% vs the PI's 5–20%). It agrees on
  known-recognized (call 3).
- Scored on the PRIMARY pointer arm only; NOT-ADJUDICABLE or unresolved
  scores a TIE.
- **1 -> H1 statistic** (mean question-level IDK rate on unknown-true).
  Supported if its cluster-bootstrap 95% CI lies inside [0.10, 0.50] (so H1
  FAILS with a lower bound >= 0.10). Contradicted by H1 PASS (lower bound
  >= 0.50) or a CI upper bound < 0.10 ("rarely"). Otherwise (e.g. H1
  INCONCLUSIVE) TIE.
- **2 -> H2 statistic** (mean question-level IDK rate on known). Supported
  if the CI upper bound is < 0.05 (which implies H2 PASS). Contradicted if
  the CI lower bound is > 0.05. Otherwise TIE.
- **3 -> H4 (descriptive).** Supported if the CI upper bound of the mean
  question-level IDK rate on known-recognized is < 0.50; contradicted if its
  lower bound is > 0.50. Needs n >= 50 questions and R0 valid; otherwise
  TIE.
- **4 -> H3.** Supported by THRESHOLD_BETTER. Contradicted by IDK_BETTER.
  NO_DIFFERENCE_DETECTED or NOT-ADJUDICABLE: TIE.
- Where the two parties diverge, the same gate decides both: H1 PASS
  supports the PI and contradicts the orchestrator; H1 FAIL with a lower
  bound >= 0.10 does the reverse; an H1 FAIL below 0.10 contradicts both.
  For H3, IDK_BETTER supports the PI, THRESHOLD_BETTER the orchestrator.
- Metric note (2026-10-05): mapped to question-level rates as above; the
  prediction itself is unchanged.

Resolution: each call is compared with the outcome in Outcome. WIN / LOSS /
TIE scores are the PI's to ratify and are recorded in
`docs/prediction-scoreboard.md`.

## Outcome

Filled at resolve. Record the verdict, the gate results, and the one-sentence
summary that also goes into `verdict:` in the manifest.
