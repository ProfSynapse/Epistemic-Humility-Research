---
amendment: decision-model-calibrated-choice
slug: decision-model-calibrated-choice
tier: 2
posture: exploratory
question: >-
  Does a trained decision model, which always chooses and reports a
  temperature-calibrated distribution over options, give confidence that
  tracks what its base torso knows (high on known, near chance on unknown,
  separating the two) without refusing, and does the base model's frozen
  known-unknown axis survive in the decision model's <answer> state?
predictions:
  orchestrator:
    call: S0 passes; H-C and H-D2 pass; H-A fails on the gap leg; H-D1 passes
    confidence: "~45% for the joint call; per-gate odds in the scoreboard"
    recorded: 2026-10-04
    basis: >-
      Temperature is fit on a CAL pool that is mostly unknown, so unknown-row
      confidence settles near the pooled 4-way accuracy (recognition lifts it
      above chance) rather than at 0.25; entity familiarity is linearly
      present at many positions after the question, so a probe and the
      frozen base axis both read it.
  user:
    call: "Readout blind to knowledge (H-C fails); knows but doesn't say (H-D1 and H-D2 pass)"
    recorded: 2026-10-04
    selected_from: candidate outcomes listed by the orchestrator, which offered no recommendation
    quote: >-
      Readout (H-A/H-B/H-C): "Blind to knowledge". H-C fails (AUROC < 0.75):
      calibrated confidence reflects option-format cues more than what the
      torso knows, even if it's calibrated on average. Internal signal
      (H-D1/H-D2): "Knows but doesn't say". D1 high (the frozen base KU
      direction reads known/unknown on the decision model's <answer> state at
      >= 0.75), but the readout lags: a probe beats the readout by >= 0.03
      (H-D2 passes). This is the EH "knows but doesn't say" result in a model
      that can't refuse.
outcome: >-
  Run complete 2026-10-05 (see "Outcome"). Primary pointer arm: H-A FAIL (a1
  gap 0.1769 [0.1737, 0.1798] above the 0.10 cap; a2 PASS), H-B PASS, H-C PASS
  (AUROC 0.9407 [0.9266, 0.9526]), H-D1 PASS (0.9762 [0.9718, 0.9805]), H-D2
  PASS (+0.0509 [0.0393, 0.0639]); matrix cell "readout confidence tracks the
  base known-unknown axis". Secondary letter-logit arm: same verdict pattern.
  Terminal status and scores pending PI resolve.
scoreboard:
  user: pending
  orchestrator: pending
---

# Decision-model calibrated choice: does a never-refusing readout track what the base torso knows?

Status: signed 2026-10-05 (commit `1387e92d`); signed run executed 2026-10-05.
The Outcome section records the result; the terminal status and verdict live
in `experiment.yaml`. This header read "draft (not signed; do not launch as
confirmatory evidence) ... Nothing in this cell has been run" until
2026-10-05; corrected to match the machine state (the
gemma-4-e4b-family-atlas 2026-07-20 header-correction pattern). First written
2026-10-04 by the orchestrator for the PI.

Keep this document the prose home for the experiment. The machine state lives in
`experiment.yaml` and is never duplicated here.

**Short name:** decision-model-calibrated-choice (dmcc)

**Scope:** one exploratory evidence cell. Stage 0 fits and freezes the base
model's known-unknown (KU) readout directions. Stage 1 asks whether a trained
decision model's calibrated option confidence tracks the base torso's prior
known/unknown label on PopQA, and whether the frozen base KU axis is still
readable in the decision model's `<answer>` state. Read-only over a trained
checkpoint: no training, no write arm, no refusal channel.

**Session note:** none opened for this draft; the lead adds a checkpoint at
sign-off (protocol-amendments.md workflow step 8).

## Motivation and posture

The program's generative-model results (paper 3, `papers/paper-3-knows-but-doesnt-say/manuscript.md`)
show a model that represents what it does not know but does not report it: on
SelfAware (Qwen3-4B, n = 3369) the internal known-unknown readout separates
known from unknown at AUROC 0.997, while stated confidence ranks
appropriateness at AUROC 0.52 to 0.56, pinned near a constant.
`experiments/stated-confidence-under-pstruct/` adds that the stated channel is
severely miscalibrated on every trained arm. Training moves refusal but has not
produced a stated confidence that tracks knowledge.

A decision model removes the verbalized channel. It never refuses: it returns a
distribution over the listed options and an argmax, and its confidence is the
softmax at `<answer>`, calibrated by temperature. "Confident when it knows, near
chance when it does not, still choosing" becomes measurable. The open question
is whether that structural change is enough: does the option readout carry the
KU signal that generative models fail to report, or can an internal probe still
see more than the readout says?

Posture: EXPLORATORY tier-2 Amendment (a new evidence cell). Reported
separately from the locked headline matrix and never pooled with it. Model
family, size and population all differ from paper 3 (Qwen3.5-2B-Base torso,
PopQA, labels generated by the base model itself), so paper 3's numbers are
context for the question, not a matched comparison.

## Relationship to existing protocols

- Additive. Touches neither PROTOCOL v0.3's locked matrix nor any signed
  amendment's gates. No headline claim is made or changed.
- Uses EH's canonical known/unknown instrument unchanged
  (`experiments/common/knowledge_probe/probe.py`, scorer `scoring.py`, render
  path `backends.py`). Only its config differs, in `probe.yaml` (model, pool,
  output; every sampling, prompt, label and sensitivity value is copied
  verbatim from `experiments/common/configs/knowledge-probe/probe.yaml`).
- Uses the tuner's generic `mechinterp extract` / `mechinterp probe-fit` verbs
  for Stage 0, in the pattern of `experiments/rawbase-ambigqa-boundary-readout/`
  and the frozen two-signal directions under
  `experiments/common/artifacts/two_signal_probe_directions/` (which have no
  Qwen3.5-2B entry).
- Calls the tuner's generic decision-analysis CLI
  (`synaptic-tuner/Trainers/decision/analyze_confidence.py`) through
  `tuner.py local-run` and a materialized recipe, never by import.
- Supersedes nothing. The write arm sketched in the original design
  (gated erase-write on a KU direction) is out of scope here (see Rerun /
  launch policy).

## Prior exposure (disclosed before sign; binding on interpretation)

The PI asked for this to be stated plainly. Verbatim facts:

1. A preliminary PopQA labeling run with a tuner-side reimplementation of the
   labeler has already been done: 3,000 questions gave 304 known / 2,177
   unknown / 518 ambiguous. That run is a preflight only and is NOT used.
   This cell relabels with EH's own instrument. The 3,000 preflight questions
   are a subset of the 14,267 rows this cell labels.
2. In that preflight, the answer matcher was changed from substring to
   bidirectional prefix after inspecting greedy labels. This happened before
   any decision-model outcome was observed. It does not carry into this cell:
   EH's `scoring.is_correct` (word-bounded alias membership) is the matcher
   of record here.
3. No decision-model outcome on PopQA has been observed. A pilot knowledge
   analysis was started and stopped before it produced output.
4. The pointer model's own training evaluation on strands held-out tasks HAS
   been observed: accuracy 0.633, calibrated ECE 0.031,
   answer-change-under-reordering 0.086 on 10,500 rows. The letter-logit
   model's own strands held-out training evaluation HAS also been observed
   (disclosed 2026-10-04, after its training finished): accuracy 0.654,
   calibrated ECE 0.015, answer-change-under-reordering 0.097. Any
   strands-holdout claim for either model is therefore exploratory, not
   pre-registered. These are strands-only results, not PopQA. This
   amendment's confirmatory gates are PopQA-only.

Added by the drafter:

5. The preflight's counts are not a forecast for this cell. The preflight used
   a 4-shot raw `Q:/A:` prompt with its own exemplars, 16 new tokens and the
   bidirectional matcher. This cell uses Amendment Y's 5-shot base-mode block,
   first-line answers capped at 64 tokens, and EH's word-bounded alias
   membership. The known rate may move in either direction.
6. Pre-sign feasibility probe (allowed and required by
   amendment-vs-lab-notebook.md; no model, no labels, no outcome): PopQA
   test.tsv @ `098765c7` has sha256 `9a5227f4...6089b`, 14,267 unique ids, 16
   relations, every needed field present, every row has a normalizable alias,
   and every row has at least 3 same-relation distractor candidates. Details
   in the NOTEBOOK.
7. The drafter read the base tokenizer's chat template (copied into the
   pointer checkpoint as `chat_template.jinja`). It supports the
   `enable_thinking` switch and renders the empty thinking-off marker that
   probe.py's self-check accepts. No generation was run.
8. The sample size (all 14,267 rows) was chosen from the gate floors below,
   not from any outcome.
9. The pre-sign infrastructure checks (2026-10-04) generated text with the
   base model only on 20 fixed non-PopQA smoke questions and on deterministic
   synthetic arithmetic and unit-conversion prompts. They observed:
   - completions, as token IDs, compared for identity and never scored;
   - the frequency of generated thinking markers (checklist item 7), and
     a four-format prompt diagnostic on 140 non-PopQA questions, mostly
     arithmetic, with known answers (checklist item 10);
   - generation and extraction throughput;
   - how much the adapter displaces hidden states on 6 generic prompts.
   No PopQA row was generated on, labeled or extracted, and no decision-model
   output on any QA item was produced.

## Design

### Labels (EH protocol, base torso as labeler)

- Substrate: PopQA (`akariasai/PopQA` @ `098765c79ea10a2cb19c828324e33281b8336ec0`,
  `test.tsv`), every row (14,267; 16 relations). `dmcc_harness.py build-pool`
  writes the probe pool in EH's format: `question`, `question_id = popqa-<id>`,
  `answer.normalized_aliases` = EH `normalize_answer` over `possible_answers`,
  `answer.value` = `obj`.
- Labeler: the decision torso's base model `Qwen/Qwen3.5-2B-Base` @
  `b1485b2fa6dfa1287294f269f5fb618e03d52d7c`, adapter-free. Facts live in the
  torso; the decision LoRA was trained on classification, not trivia.
- Instrument: `experiments/common/knowledge_probe/probe.py` on vLLM 0.27.1,
  with two opt-in options whose defaults leave every other cell unchanged
  (prompting surface, below; generated-thinking policy, below). Batch
  invariance is OFF (vLLM 0.27.1 refuses it for Qwen3.5's
  gated DeltaNet layers; see Lane). 1 greedy + 32 sampled answers per
  question (T = 1.0, top-p 0.9, 64 new tokens, master seed 20260610).
  probe.py's vLLM backend takes no revision argument, so `stage-model` stages
  the pinned snapshot and writes a materialized config whose `model_name` is
  that snapshot directory, asserted to be named by the pinned revision.
- Prompting surface: **base-mode 5-shot** (`probe.yaml prompt.surface:
  base_kshot`). PI decision, 2026-10-04, before any PopQA labeling or outcome
  (pre-sign checklist item 10).
  - **What it is.** Amendment Y's pre-stated surface for pretrain-only base
    models (`experiments/pretrain-only-base-readout/AMENDMENT.md` section 6),
    reused, not reinvented. The fixed exemplars and the
    `"Q: {q}\nA: {a}\n\n"` block come from
    `experiments/common/readouts/amendment_x_cross_model_extract.py`
    (`_BASE_MODE_FEWSHOT`, `build_base_mode_prompt`), vendored byte-identical
    into `experiments/common/knowledge_probe/backends.py` as
    `flavor-atlas-gemma-pt-confirmatory` also did. A test pins them to the
    source (`tests/test_base_kshot_surface.py`). No chat template and no
    system prompt are used; `prompt.system` is kept in the config only for
    provenance. The answer is the first line of the completion (Y's
    `cont.split("\n", 1)[0].strip()`), and vLLM generation stops at the first
    newline. That changes no scored answer, because the first line is all the
    parse reads. Stage 0 renders the identical string, and its `answer_end` is
    Y's first-line content end.
  - **Why.**
    - It complies with Amendment Y's registered rule for pretrain-only bases.
    - In the 2026-10-05 lab-notebook diagnostic on 140 non-PopQA questions
      (NOTEBOOK, run record `dmcc-presign-think-diagnostic-20261005`), the chat
      surface emitted thinking markers in 1.93% of generations. The model
      wrote an answer, closed an implicit think block, and restated the
      answer, giving 17-word answers. The base-mode surface emitted markers in
      0.11% of generations, gave 1.2-word answers, and had higher greedy and
      sampled accuracy (0.75 / 0.67 vs 0.59 / 0.48).
    - The other chat variants (thinking on; no think block) were worse, at
      10.5% and 30.5%.
  - **Caveat.** The diagnostic set was mostly arithmetic (120 of 140), and the
    exemplars are trivia. The size of the surface effect on PopQA entity
    questions may differ. The two surfaces disagreed on 34% of known/unknown
    labels in that set, so the surface choice changes which questions count as
    known. That is why it was fixed before any PopQA labeling.
  - **Exemplar/PopQA overlap check** (pre-sign, no model).
    - None of the five exemplar questions is a PopQA item, and no exemplar
      answer is a PopQA subject.
    - One coincidence: the exemplar answer "Au" (gold) normalizes to the
      PopQA alias "AU" (Australia) on 27 country questions.
    - The exemplars stay byte-identical to Y's.
  - **Pre-registered exclusion of exemplar-answer collisions.** PI decision,
    2026-10-05, before any PopQA labeling or outcome.
    - **Rule** (deterministic; `dmcc_harness.exemplar_collision_qids`): a
      PopQA row is excluded from every primary analysis iff any of its
      normalized gold aliases (EH `normalize_answer` over `possible_answers`,
      plus `obj`) equals a normalized base-mode exemplar answer (`jupiter`,
      `six`, `au`, `1945`, `mount everest`).
    - **Matches.** On PopQA test.tsv @ `098765c7` (pre-sign, no model) the
      rule matches exactly **27** rows, all via `au` (relation: country), which
      are the 27 found by the overlap check and no others. The qids are in
      `analysis-committed/exemplar_collision_qids.json`.
      `gates.yaml g0_exemplar_collision_exclusion.expected_count: 27`, and
      `convert` refuses if the rule matches any other count.
    - **Scope.** These rows are still labeled (the probe pool is unchanged).
      They are then dropped in `convert`, BEFORE the FIT/CAL/TEST split. So
      they never enter the splits, the Stage 0 FIT/CAL fit and validation, or
      Stage 1 TEST.
    - **Reporting.** Sensitivity only: their label counts
      (`exemplar_collision_excluded`) and the echo count (`exemplar_echo_au`:
      first-line answers that are exactly "Au" on those rows).
    - **Tests.** `tests/test_exemplar_collision_exclusion.py`.
- Labels (EH bands): known = greedy correct AND p_correct >= 0.5 (>= 16/32);
  unknown = 0/32; everything else is EH `discard`, called ambiguous here, and
  is excluded from the primary analysis (counts reported).
- Generated-thinking policy: **`count_wrong`**
  (`probe.yaml scoring.generated_thinking_policy`).
  - **What it does.** A sampled or greedy generation containing a thinking
    marker (`<think>` or `</think>`, the same substring test as EH's abort
    path) is scored INCORRECT and the run continues. Each probe row records
    `n_sampled_thinking_marker` and `greedy_thinking_marker`. The probe
    manifest and the harness's label run record carry the run total and rate.
  - **Why it is kept.** It began as the fix for the chat surface's markers.
    It is retained as a safety net under the base-mode surface, where markers
    are rare (pre-sign figures in the NOTEBOOK). EH probe.py's default is a hard
    abort, so a single marker would otherwise void the run. The earlier
    chat-surface rationale and its measured rates are superseded by the
    surface decision. They are kept in the NOTEBOOK entries of 2026-10-04
    (late) and 2026-10-05.
  - **Why this policy.** It is conservative: it can only lower p_correct and
    can never make a greedy decode correct. It therefore cannot create a false
    "known", which needs a correct greedy decode and at least 16/32 correct
    samples.
  - **Decision.** The PI chose this policy on 2026-10-04, before any PopQA
    labeling or outcome; the alternatives considered are listed under pre-sign
    checklist item 7.
  - **Implementation.** An opt-in addition to the shared EH instrument
    (`experiments/common/knowledge_probe/backends.py` and `probe.py`). The
    default stays `abort`, so existing cells, configs and `probe_config_sha`
    values are unchanged. Row schema and manifest are unchanged under the
    default. Tests are in `tests/test_generated_thinking_policy.py`; the full
    knowledge-probe suite shows no new failures (NOTEBOOK).
  - **Pre-stated sanity bound** (`gates.yaml g0_label_marker_bound`). If the
    marked rate over all label generations (sampled + greedy) on the real run
    exceeds **5%**, labeling is FLAGGED. The PI is consulted before Stage 0 or
    Stage 1 proceeds; `dmcc_harness convert` refuses until the PI's decision is
    recorded in `analysis-committed/pi_marker_rate_ack.json`.
  - **Registered sensitivity analysis** (descriptive, reported beside the
    primary). It compares primary label counts with the counts after dropping
    every question that had any marked generation, and it recomputes the H-A,
    H-B, H-C and H-D1 statistics on TEST with those questions dropped. The
    primary verdicts are not changed by it.

### Decision rows

`convert` renders each known/unknown question as one decision `choice` row
(schema `decision-row/v1`), a port of the tuner-side `build_choice_rows`:

- state = the PopQA question; instructions = "Which option correctly answers
  the question in the state?"; 4 options = gold `obj` + 3 distractors drawn
  (seed 0) from other objects of the SAME relation whose normalized text
  matches no gold alias; option order shuffled; task = `popqa:<relation>`.
- meta: `qid`, `knowledge` (known / unknown), greedy_correct, p_correct,
  sampled-correct count, `s_pop`, relation, probe_config_sha.
- Port differences, stated: EH's alias normalizer replaces the tuner port's
  SQuAD-style one, and the gold `obj` itself is added to the exclusion set.
- Known caveat: PopQA objects are single-valued in the data, but some subjects
  really have several (occupations, genres). A same-relation distractor can
  occasionally also be true. This hits known and unknown rows alike, so it
  adds noise rather than bias.

### Splits

FIT / CAL / TEST = 40 / 20 / 40, stratified by relation, seed 0, drawn by the
engine (`split_fit_cal_test`). The harness reproduces the identical split
before the engine runs (a port verified identical on synthetic rows at
drafting time) so Stage 0 can use FIT and CAL without ever touching TEST.
G0 then checks, fail-closed, that the engine's TEST qids and split counts equal
the harness's. Probes fit on FIT; temperatures, conformal q-hat and the stacker
fit on CAL; every Stage 1 number comes from TEST.

### Stage 0: base-model KU readout (mech-interp prework, frozen before Stage 1)

EH's extraction -> probe-fit -> freeze pipeline, applied to the labeler.

- **0a extraction** (`stage0_extract.yaml`): `tuner.py mechinterp extract`,
  `Qwen/Qwen3.5-2B-Base` @ `b1485b2f`, no adapter, in the native generative
  setting. The render (`dmcc_harness:render`) is byte-identical to the
  labeling prompt, which is Amendment Y's base-mode 5-shot block
  (`backends.build_base_mode_prompt`; see Labels). Rows: FIT + CAL
  known/unknown only. Positions: gate = `anchor`, the last prompt token (the
  `:` of the final `A:` cue, as in Amendment Y). Dial = `answer_end`, the last
  content token of the FIRST LINE of the model's own greedy answer (Y's
  `_first_line_content_end` rule; 64 new tokens). Rows whose first line is
  empty are excluded from the dial. All hidden states (0 = embeddings).
  Runs in the pinned mechinterp-runner image (local GPU invariant, 2026-07-10)
  built with `TRANSFORMERS_VERSION=5.17.0` to share the decision stack's
  transformers. Rows are sharded (500 per call) so a kill loses one shard.
- **0b readout fit** (`stage0_probe_fit_{gate,dial}.yaml`):
  `tuner.py mechinterp probe-fit` on FIT only, known = 1 vs unknown = 0,
  ambiguous excluded. PCA(128) -> saga logistic, 5-fold out-of-fold AUROC
  layer sweep, refit at the best layer, frozen as `mechinterp-direction/v1`
  JSON (layer, unit vector, mu, sigma, class-conditioned stats, recipe,
  provenance with the full layer surface). Dial rows with an empty greedy
  answer are excluded from the dial fit.
- **0c validation and freeze** (`stage0-validate`): CAL AUROC of the frozen
  projection with a stratified bootstrap CI; a label-permuted control (the
  same verb on FIT labels permuted with seed 0); Platt and isotonic maps fit
  on FIT and CAL ECE reported, mirroring `experiments/common/mechinterp/fit_calibration.py`
  (that script is not invoked: its loaders are bound to the legacy Amendment
  S/U extraction layout). It writes the freeze marker
  (`analysis-committed/stage0_freeze.json`) with the sha256 of every frozen
  direction. `analyze` refuses to launch without it, and `score` refuses a
  direction whose bytes differ from it.
- Stage 0 is instrument validation, not a claim. Its validity gates decide only
  whether H-D1 is adjudicable.
- Tier ruling: Stage 0 stays inside this amendment. It is the construction and
  validation of an instrument this cell's own hypothesis (H-D1) consumes. It
  produces no standalone claim, and its validity gate is pre-registered here.
  This matches `rawbase-ambigqa-boundary-readout`, which extracts and fits
  inside its own cell. Its GPU smoke and preflight are tier-3 lab-notebook
  entries under this amendment. If a second experiment ever consumes these
  directions, the promotion rule moves them to
  `experiments/common/artifacts/two_signal_probe_directions/qwen3.5-2b-base/`
  with provenance.

### Stage 1: decision models (read-only)

- Primary model: the pointer decision model, tuner run
  `decision-qwen35-2b-pointer` (LoRA r16 / alpha 32 + pointer head, strands v5
  short-task corpus, 1 epoch), recipe
  `Trainers/recipes/decision_qwen35_2b_pointer.yaml` (engine `31962293`);
  checkpoint `.../decision-qwen35-2b-pointer/20261004_122756/final_model`
  (3,045 steps, 2 h 40 m), tree sha256
  `e0cc616de238cfad85a8627aaa47583dba7689ece63c9bedc4c63a6e9a4acbfc`
  (adapter_model.safetensors
  `7d66a8a9d34f85eb3661b458598ed85e727a6748a4831effec83a820d3770ab6`,
  readout_head.safetensors
  `d7d979817375367ccec4bf09bfa54e2ffbea07872958b7462e328608c0857989`,
  decision_config `7cd67f75...`).
- SECONDARY arm (PI decision, 2026-10-04): the letter-logit readout model,
  tuner run `decision-qwen35-2b-letter-logits`, recipe
  `Trainers/recipes/decision_qwen35_2b_letter_logits.yaml`. It is scored with
  the identical gates and labelled secondary/exploratory. It carries no
  confirmatory claim, so no multiplicity correction is applied. Confirmatory
  claims rest on the PRIMARY pointer arm alone. Checkpoint provenance (run
  completed 2026-10-04): run dir
  `F:\Code\Toolset-Training\.claude\worktrees\jev-models-tuner-training-b55d92\toolset-training-artifacts\runs\local_docker\decision\decision-qwen35-2b-letter-logits\20261004_152616`
  (`final_model/`), recipe at tuner commit `29f7af0c` (training code unchanged
  since `31962293`), registry run id `55307ef8-ec80-414e-967d-c55ba6d7d1d6`,
  3,045 steps, 2 h 15 m. Tree sha256
  `3aef07e292b2892d7e2812d2935ed054c01d3422dc330e52c486805e13f9dd96`;
  adapter_model.safetensors
  `3ab902d84d2a937b74e1181a7018df9f558de5ee89310d66ea564d19b46b4180` (no
  readout head: the letter-logit readout uses the LM head).
- Engine call: `analyze_confidence.py` via `tuner.py local-run` with
  `recipe_pointer.yaml` (mirrors the engine's own analysis recipe) and
  `analysis_pointer.yaml` (ablation off, all layers captured at `<answer>`,
  PCA(128) probes with 5-fold sweep on FIT, permuted control on, conformal
  alpha in {0.1, 0.2}, thresholds 0.8 / 0.5, 15 ECE bins, paired bootstrap
  2000 / seed 0, `export.per_row: true`, `export.states: false`, and a
  `directions:` list naming the three frozen Stage 0 JSONs `base_gate`,
  `base_gate_permuted` and `base_dial`, each at its own frozen layer, with no
  layer override allowed). Inputs, including the frozen direction JSONs, are
  staged under the tuner's gitignored `scratch/eh_staging/<run_id>/`. The
  harness checks the staged directions byte-for-byte against the Stage 0 freeze
  marker before staging and again before launch. A run record is written
  before launch.
- Confidence of record: R1, the per-kind temperature-calibrated max option
  probability (temperature fit on CAL). R0 raw, P-dial and the CAL stacker S
  are reported descriptively.
- Arms the engine reports and how they are used: R0 (descriptive), R1
  (gated), P-dial (descriptive), S (descriptive), KU probe (H-D2), frozen
  base gate direction (H-D1: the engine scores it as the direction's own
  logistic decision value `h_L @ coef + intercept` at the frozen layer index of
  the decision model's `<answer>` state, and reports
  `directions.base_gate.auroc_known_vs_unknown`; the harness bootstraps the CI
  from per-row `direction_scores.base_gate` and requires its point AUROC to equal
  the engine's), frozen permuted gate (descriptive H-D1 control on TEST), frozen
  base dial (descriptive).

### Controls

- Label-permuted probes: Stage 0 (permuted gate fit, S0-G2) and Stage 1 (the
  engine's permuted control at the KU probe's best layer, an H-D2
  precondition).
- Readout baseline: H-D1 and H-D2 are both measured against R1 on the same
  TEST rows (paired bootstrap), not against chance.
- Chance reference: 1/N = 0.25 for every row; unknown-row accuracy is reported
  against it.
- If a write arm is ever added (out of scope here): matched-magnitude
  random-direction placebos (15 seeds) and a permuted gate are required, and
  the frozen Stage 0 artifact plus a readback smoke must exist first, per EH
  discipline.

### Sample size

All 14,267 rows are labeled. 14,240 enter the primary population after the
27-row exemplar-collision exclusion (0.19%; it does not change the power
argument). The G0 floors require at least 150 known and 300 unknown TEST
rows (derivation in Gates). If the known rate were near the preflight's 10%,
TEST would hold roughly 0.4 x 0.10 x 14,267, about 570 known rows, clearing the
floor with margin; a 3,000-question sample would give roughly 120 and could
miss it. This is a power argument from a disclosed preflight rate, not an
outcome.

### Lane, runtime and engine pin

- Local RTX 3090, one GPU job at a time.
- Labeling: vLLM 0.27.1 in the isolated WSL venv used by
  `dial-logprob-baseline-v3` (`/home/profsynapse/.venvs/vllm`; torch
  2.13.0+cu130, transformers 5.15.0), `VLLM_BATCH_INVARIANT=0`. The 2026-10-04
  pre-sign check found that vLLM 0.27.1 refuses batch-invariant mode for this
  model ("batch_invariant mode is not supported for GDN_ATTN"). Deviation from
  the batched-generation.md default, stated here: probe.py sends one request
  per question (greedy n = 1; sampled n = 32 with a per-question seed), so no
  cross-question batch composition enters any decode. Repeatability is gated by
  the exclusive-GPU repeat smoke instead (pre-sign checklist). vLLM loads the
  checkpoint as `Qwen3_5ForConditionalGeneration` and profiles its vision
  encoder at startup. That allocation can exceed a low
  `gpu_memory_utilization` cap, so the label stage needs the GPU to itself
  (NOTEBOOK, 2026-10-04 incident).
- Stage 0: `mechinterp-runner:dmcc-tf5.17.0`, built 2026-10-04 from the pinned
  submodule's `docker/mechinterp-runner/` with `TRANSFORMERS_VERSION=5.17.0`
  (torch 2.9.1+cu128). Image ID
  `sha256:b4166dbd15d0c7d9cad8a07c46be1301dc5941eb4b4d629ae754dc27cb03eb9c`,
  recorded as `instrument.runtime_image_digest`. It is run from WSL against
  the Docker Desktop daemon (`docker --context default`).
- Stage 1: `unsloth/unsloth@sha256:0b8efd89caf77bc4150f6464416d7bc6a5e00e27a4446615ecf99ef20f553397`
  (torch 2.11, transformers 5.17.0, peft 0.21.2, plus flash-linear-attention).
  Version note: the validated mechinterp-runner default is transformers
  5.12.1. The decision stack needs 5.17.0 for `Qwen3_5ForCausalLM`, which is
  why Stage 0's image is built at 5.17.0.
- Engine pin: `synaptic-tuner` at `29f7af0c35e3c825d96f770b62f46c60ac4db2b7`
  (branch `jev-models-tuner-training-b55d92`; `31962293` adds the `decision`
  method, `26cb57c7` adds the confidence analysis, and `29f7af0c` adds per-row
  export, TEST state export and external frozen directions). This is an INTERIM pin. It
  precedes the submodule-first API repoint (EH branch
  `feat/submodule-cloud-api-v1-host`), whose `api/v1` exposes only SFT today.
  This cell therefore reaches the engine through `tuner.py local-run` and the
  `mechinterp` verbs, not `api/v1`.

### Engine capability gaps (closed at `29f7af0c`)

The first draft pinned `26cb57c7`, whose `test_rows.jsonl` had no per-row
`<answer>` states, option probabilities or KU-probe scores, so H-D1 and the
conformal-by-knowledge secondary could not be computed. That gap was flagged to
the tuner as a generic capability and closed upstream in `29f7af0c`, with no
EH-specific code: an `export` section (`per_row` adds `row_index`, `probs_r0`,
`probs_r1`, `dial_score`, `stack_score`, `ku_probe_score` and
`direction_scores`; `states` optionally writes `test_states.npz`) and a
`directions:` list that scores external `mechinterp-direction/v1` JSONs on TEST
`<answer>` states. It fails loudly on a missing file, wrong schema, hidden-size
mismatch or uncaptured layer, including in `--dry-run`. The engine's layer
index is the decoder's `output_hidden_states` index (0 = embeddings, i = output
of block i), the same convention as `MechInterp.extraction`; the pre-sign
layer-index check confirms it on this model (NOTEBOOK). The cell does not load
the decision model itself.

### Implementation boundary

Cell files, all pinned at sign: `cell.yaml`, `gates.yaml`, `probe.yaml`,
`stage0_extract.yaml`, `stage0_probe_fit_gate.yaml`,
`stage0_probe_fit_dial.yaml`, `stage0_probe_fit_gate_permuted.yaml`,
`analysis_pointer.yaml`, `recipe_pointer.yaml`, `analysis_letter_logits.yaml`,
`recipe_letter_logits.yaml`, `dmcc_harness.py`, plus the shared EH instrument
modules `probe.py`, `backends.py` and `scoring.py`. Containment: question
text, generations, hidden states, directions and row-level outputs stay in
the gitignored `analysis/` and `directions/`. Only counts, aggregate
statistics, verdicts, run records and the freeze marker go under
`analysis-committed/`. No committed file is written under `synaptic-tuner/`
apart from the gitlink.

## Prediction

Registered hypotheses (the manifest's one-sentence `prediction:` condenses
them). All on TEST except Stage 0.

- **S0 (instrument validity):** the frozen base gate direction reads known vs
  unknown on CAL at AUROC >= 0.80, and its permuted twin reads 0.40 to 0.60.
- **H-A (unknowns near chance):** on unknown rows, mean(R1 - 1/N) <= 0.10, and
  confident-wrong (wrong with R1 >= 0.8, over all unknown rows) <= 5%.
- **H-B (knowns confident and right):** underconfident-right (right with
  R1 < 0.5, over all known rows) <= 10%.
- **H-C (readout separates):** AUROC(R1 -> known), known vs unknown, >= 0.75.
- **H-D1 (base axis transfer):** the FROZEN base gate direction, applied
  without refitting to the decision model's `<answer>` state at the same layer
  index, reads known vs unknown at AUROC >= 0.75. The index convention is
  verified (pre-sign, NOTEBOOK): `mechinterp extract` and the decision capture
  path give the same 25 states (0 = embeddings, i = block i, 24 = after the
  final norm). Whether the residual geometry survives the LoRA is what H-D1
  tests, not an assumption. The pre-sign check saw the adapter move the last
  prompt token's state by a mean relative L2 of 0.10 to 0.50 across indices 1
  to 23, measured on 6 generic non-PopQA prompts (descriptive; not a population
  result). The prompt and position also differ (QA prompt end vs decision
  `<answer>`). H-D1 is also compared against R1 with a paired bootstrap.
- **H-D2 (fresh probe beats readout):** an EH-style KU probe on the decision
  model's `<answer>` state (MechInterp PCA -> logistic, layer sweep on FIT)
  beats R1 on known vs unknown by >= 0.03 AUROC with the paired-bootstrap CI
  excluding 0. Passing means the model's state carries more than its
  confidence reports. Failing means the readout already carries the signal.

## Falsifier

- The readout-tracks-knowledge line is falsified if H-C FAILS (the bootstrap
  95% CI upper bound of AUROC(R1 -> known) is below 0.75) or H-A FAILS (the gap
  CI lower bound is above 0.10, or the confident-wrong Wilson lower bound on
  unknowns is above 0.05).
- The residual-signal prediction is falsified if H-D2 FAILS (the paired CI
  upper bound is below +0.03), read as: the readout already carries the KU
  signal a fresh probe finds.
- The base-axis-transfer prediction is falsified if H-D1 FAILS (the CI upper
  bound is below 0.75) with Stage 0 valid.

## Gates

Pre-stated in `gates.yaml`, fixed at signing, never retuned. **The PI
confirmed the drafted thresholds on 2026-10-04, before any outcome.** They
apply in full to the primary pointer arm and, identically but as exploratory
evidence only, to the secondary letter-logit arm. Summary:

| Gate | Statistic (population) | PASS | FAIL | CI |
|---|---|---|---|---|
| G0 integrity | digests, engine commit, split identity, ambiguous excluded | all hold | any fails: cell NOT-ADJUDICABLE | n/a |
| G0 floors | TEST known >= 150, unknown >= 300 | met | not met: cell NOT-ADJUDICABLE | n/a |
| S0 floors | FIT >= 100 / 100, CAL >= 60 / 60 (known / unknown) | met | not met: H-D1 NOT-ADJUDICABLE | n/a |
| S0-G1 | CAL AUROC, frozen gate projection | CI lo >= 0.80 | CI hi < 0.80 | stratified bootstrap |
| S0-G2 | permuted gate: FIT CV AUROC at gate layer AND CAL AUROC | both in [0.40, 0.60] | either outside | n/a |
| H-A a1 | mean(R1 - 0.25), unknown | CI hi <= 0.10 | CI lo > 0.10 | bootstrap |
| H-A a2 | confident-wrong share, all unknown rows | Wilson hi <= 0.05 | Wilson lo > 0.05 | Wilson |
| H-B | underconfident-right share, all known rows | Wilson hi <= 0.10 | Wilson lo > 0.10 | Wilson |
| H-C | AUROC(R1 -> known) | CI lo >= 0.75 | CI hi < 0.75 | stratified bootstrap |
| H-D1 | AUROC(h_L . v_gate -> known) | CI lo >= 0.75 | CI hi < 0.75 | stratified bootstrap |
| H-D2 | AUROC(KU probe) - AUROC(R1) | diff >= 0.03 and CI lo > 0 | CI hi < 0.03 | engine paired bootstrap |

- **INCONCLUSIVE rule:** a gate whose 95% CI contains its threshold is
  INCONCLUSIVE and reported as such. H-A is PASS only if both legs pass, FAIL
  if either fails, otherwise INCONCLUSIVE.
- **NOT-ADJUDICABLE** (distinct from PASS, FAIL and INCONCLUSIVE): a registered
  precondition failed. H-B is NOT-ADJUDICABLE if known-row accuracy is below
  0.50, because a model that is mostly wrong on knowns cannot often be
  underconfident-right and the cap would pass vacuously (gate-diagnosticity.md).
  H-D1 is NOT-ADJUDICABLE unless S0-G1 and S0-G2 pass. H-D2 is
  NOT-ADJUDICABLE if the engine's permuted control sits outside [0.40, 0.60].
- **Floor derivation:** a Wilson-upper cap c cannot be met at 0 events below
  N = z^2 (1 - c) / c, which gives 35 for c = 0.10 and 73 for c = 0.05. The
  floors are set so a point rate at half the cap still clears it: 0.05 at
  N = 150 has Wilson upper 0.0975 < 0.10, and 0.025 at N = 300 has Wilson upper
  0.0496 < 0.05. The S0 CAL floor of 60 known keeps the Hanley-McNeil 95%
  half-width near 0.06 at AUROC 0.85.
- **Denominators:** the H-A and H-B rates divide by every row of the
  prior-label class, a count fixed by the base model's label and not
  shrinkable by the decision model. Accuracy and conditional rates are
  reported alongside as companions.

## Interpretation matrix (fixed before any number exists)

| | H-C PASS (readout separates) | H-C FAIL |
|---|---|---|
| **H-D1 PASS** (base axis survives) | readout confidence tracks the base KU axis | KU signal is present in the decision state but not expressed by the readout: the decision-model analog of paper 3's represented-but-not-reported result, in a model that cannot refuse |
| **H-D1 FAIL**, fresh-probe AUROC >= 0.75 | the decision fine-tune re-encoded the axis | same reading |
| **H-D1 FAIL**, fresh-probe AUROC < 0.75 | no linearly recoverable KU signal at `<answer>` | same reading |

Any INCONCLUSIVE or NOT-ADJUDICABLE input leaves its cell unresolved. It is
never rounded to a neighbor.

## Secondary (descriptive only; no gate)

- Split-conformal LAC sets at alpha in {0.1, 0.2} (q-hat on CAL): coverage and
  mean set size on known vs unknown. Expectation: sets widen on unknowns at
  held coverage. Computed in-cell from per-row `probs_r1` and the engine's CAL
  q-hat for `choice`.
- Popularity (`s_pop`) quartiles (engine block).
- Recall vs recognition: "unknown" means the base model cannot *generate* the
  answer, but on a 4-way choice it may still *recognize* it or eliminate the
  wrong options. Unknown-row accuracy is reported with a Wilson CI against
  chance 0.25. Unknown-but-correct rows are reported, not hidden.
- Per-relation accuracy and mean R1, known vs unknown.
- Stage 0 dial direction: FIT layer surface and CAL AUROC.
- Gate calibration: Platt and isotonic CAL ECE.
- The secondary letter-logit arm: every gate above, labelled exploratory.
- Ambiguous-label counts overall and by relation.

## Rerun / launch policy

- Nothing here is launched from this draft. Every GPU stage (`label`,
  `stage0-extract`, `analyze`) needs explicit PI launch approval naming the
  stage and model. The harness also requires `--i-know-this-runs-on-gpu`.
- Order is enforced in code: build-pool -> stage-model -> label -> convert ->
  stage0-rows -> stage0-extract -> stage0-fit -> stage0-validate (freeze) ->
  stage-engine -> analyze -> collect -> score.
- GPU smoke before each full GPU stage (standing directive 2026-07-16):
  - a small-N vLLM generation smoke of the label path on an exclusive GPU
    (engine-observed prompt token IDs, repeat and reorder identity of greedy
    and seeded sampled completions, model load under vLLM 0.27.1 at the
    registered `gpu_memory_utilization` 0.90);
  - a one-shard extraction smoke (provenance line present, both families
    captured, layer count);
  - a `--dry-run` of `analyze_confidence.py` on the staged rows.
  Each is a tier-3 NOTEBOOK entry under this amendment. A smoke FAIL is a gate
  event for the lead, not a retry.
- No preflight data is reused. A crash is re-run as tier-3 recovery; the
  label and extraction stages resume from their append-log and shard markers.
- Out of scope: any write arm (erase-write / boundary push), training arms C
  and A from the original design, the strands state-ablation analysis, and
  TriviaQA / KUQ / CoCoNot. Each needs its own amendment.

## Pre-sign checklist (status 2026-10-04; the cell cannot be signed until each open item is closed or waived in writing by the PI)

Results and IDs for each check are in the NOTEBOOK and in
`analysis-committed/run_records/dmcc-presign-infra-20261004.json`.

1. **Engine capability gaps. CLOSED.** Repinned to `29f7af0c`; H-D1,
   conformal-by-knowledge and the H-D2 in-cell CI are computable end to end.
   The Stage 0 -> engine direction contract round-trips (schema, hidden size
   2048, layer resolution, loud failure on a size mismatch).
2. **Stage 0 runtime and layer convention. CLOSED.** Image built and pinned.
   Qwen3.5-2B-Base @ `b1485b2f` loads under MechInterp's loader. The
   extraction and the decision capture path (adapter disabled) agree index for
   index on all 25 states: max relative L2 0.023 on the diagonal, at least 0.30
   to a neighbouring index.
3. **vLLM. CLOSED for the probe.py regime, with a disclosed property**
   (exclusive GPU, registered 0.90 utilization, batch invariance off;
   `analysis-committed/run_records/dmcc-presign-exclusive-20261004.json`).
   - Engine-observed prompt token IDs equal the extraction render on 20 of 20
     rows.
   - Single-request greedy, the probe.py regime, repeats 20 of 20.
   - Batched vs single greedy differ on 2 of 20 rows. probe.py never batches
     across questions, so this does not apply to the label stage.
   - Seeded sampling (n = 8) repeats on 158 of 160 completions; two rows
     differ by one completion each.
   - Labels are therefore not bit-reproducible across reruns. A differing
     sample moves p_correct by 1/32, so only rows sitting at a band edge (0/32
     or 16/32) could change label. Disclosed; no gate depends on bit identity.
   - The first attempt failed on a Windows `nvcc` on the WSL PATH. cell.yaml now
     sets a Linux-only PATH for the label stage.
   - **Re-run under base-mode, 2026-10-05:** single-request and batched
     greedy repeat 20 of 20 (no batch-order effect), and seeded sampling
     repeats 160 of 160.
4. **Render identity. CLOSED**, at engine level. Re-run under base-mode on
   2026-10-05: the labeling prompts (vLLM engine `prompt_token_ids`) and the
   Stage 0 extraction render (runner image) are byte-identical, with identical
   token IDs, on 20 of 20 rows.
5. **Kill-resume drill. CLOSED.**
   - `stage0-extract` passes (earlier entry).
   - `label` passes on the real vLLM path: SIGKILL after the first
     append-log row, resume rc 0, 6 of 6 unique rows, the pre-kill row
     byte-identical. Re-run under base-mode on 2026-10-05: PASS (kill at
     499 s, resume rc 0, 6 of 6 unique rows, pre-kill row unchanged).
   - The drill surfaced, and the harness now fixes, a git-HEAD lookup failure
     under WSL. The WSL worktree's `.git` points to `F:/...`, so the harness now
     resolves HEAD in pure Python when the git CLI fails.
7. **Thinking-marker abort in the label stage. CLOSED by PI decision
   (2026-10-04, before any PopQA labeling or outcome): policy `count_wrong`.**
   Rationale, sanity bound and sensitivity analysis are under Design / Labels.
   - What happened: in the throughput run on synthetic arithmetic prompts, EH
     `probe.py` aborted at question 4 of 200 because a T = 1.0 sample
     contained `</think>`.
   - Options considered, with no recommendation from the orchestrator:
     - (i) a configurable generated-thinking policy in the shared EH
       instrument (chosen, as `count_wrong`);
     - (ii) a base-mode k-shot prompt instead of the chat template;
     - (iii) thinking ON, scored after the final `</think>`.
   - Prior-exposure note: the decision was informed only by marker frequency
     on synthetic prompts.
8. **Timing under the registered base-mode surface** (2026-10-05; synthetic
   non-PopQA prompts, so PopQA answer lengths may differ).
   - Labeling: 200 questions in about 152 s after a roughly 7 min engine init
     (328 s of it compile), or 0.76 s per question, giving about 3.1 h for
     14,267 questions.
   - Stage 0: 1.97 s per row on a 100-row spot check. The prompt is now about
     106 tokens, and extraction still decodes 64 greedy tokens. With about 90 s
     model load per 500-row shard, at most about 8,560 rows gives about 5 to
     5.3 h and about 3.4 GB.
   - The earlier chat-surface figures (1.53 s per question; 1.65 s per row)
     are kept in the NOTEBOOK.
9. **User prediction. CLOSED.** The PI's prediction was recorded verbatim on 2026-10-04 (Predictions scoreboard), and the PI confirmed the drafted thresholds the same day.
10. **Labeling prompt surface vs Amendment Y's base-model rule. CLOSED by PI
    decision (2026-10-04, before any PopQA labeling or outcome): base-mode
    5-shot, per Amendment Y.** Implemented as `prompt.surface: base_kshot`
    (Design / Labels). The affected pre-sign checks were re-run under the new
    surface (NOTEBOOK 2026-10-05, run record
    `dmcc-presign-base-surface-20261005`). What follows is the finding as it
    was recorded before the decision.
    - The rule: Amendment Y (`experiments/pretrain-only-base-readout/AMENDMENT.md`
      section 6) pre-states that all pretrain-only base cells use the
      base-mode k-shot surface, not the chat template. This cell labels a
      pretrain-only base (Qwen3.5-2B-Base) through EH's chat-template probe.
    - Evidence: the 2026-10-05 non-PopQA diagnostic (NOTEBOOK; run record
      `dmcc-presign-think-diagnostic-20261005`).
      - The chat surface (A) emits thinking markers in 1.9% of generations,
        after a first answer, and gives 17-word answers.
      - The base-mode surface (D) emits them in 0.11% of generations, gives
        1.2-word answers, and has higher greedy accuracy (0.75 vs 0.59).
      - Known/unknown labels differ between the two surfaces on 34% of
        questions.
    - Options:
      - (a) keep the chat surface with `count_wrong` (current), recording a
        named deviation from Amendment Y's rule;
      - (b) switch labeling and Stage 0 to the base-mode k-shot surface. This
        needs an opt-in base-mode render plus first-line parsing in the shared
        EH probe, a Stage 0 render/content_end change, new probe.yaml and
        stage0 configs, and a repeated render-identity, timing and
        kill-resume check.

## Predictions scoreboard

| Predictor | Call |
|-----------|------|
| orchestrator | S0-G1 PASS (~80%). H-A FAIL on a1: calibrated confidence on unknowns sits near pooled 4-way accuracy, gap about 0.15 to 0.20; a2 PASS (~60%). H-B INCONCLUSIVE or FAIL: a temperature fit on an unknown-dominated CAL compresses known-row confidence (~50%). H-C PASS or INCONCLUSIVE, point 0.75 to 0.85 (~55%). H-D1 PASS: entity familiarity survives LoRA r16 at the same layer index (~55%). H-D2 PASS (~70%). Matrix cell: "readout tracks the base KU axis", with residual signal left on the table. |
| user (PI, 2026-10-04) | Readout: "Blind to knowledge". H-C fails (AUROC < 0.75): calibrated confidence reflects option-format cues more than what the torso knows, even if it's calibrated on average. Internal signal: "Knows but doesn't say". D1 high (the frozen base KU direction reads known/unknown on the decision model's `<answer>` state at >= 0.75), but the readout lags: a probe beats the readout by >= 0.03 (H-D2 passes). This is the EH "knows but doesn't say" result in a model that can't refuse. |

Recording notes (PI prediction):

- The PI chose these two calls from a list of candidate outcomes the
  orchestrator wrote out. The orchestrator recommended neither call.
- The two calls are jointly consistent. Together they pick out one cell of the
  interpretation matrix: H-D1 PASS with H-C FAIL, read as "KU signal present in
  the decision state but not expressed by the readout". H-D2 PASS (probe beats
  readout by >= 0.03) fits a readout that lags the internal signal. Neither
  call constrains H-A or H-B.
- Falsifiers of the readout call ("Blind to knowledge"): H-C PASS (95% CI lower
  bound of AUROC(R1 -> known) >= 0.75) contradicts it. H-C INCONCLUSIVE leaves
  it unresolved.
- Falsifiers of the internal-signal call ("Knows but doesn't say"): H-D1 FAIL
  (CI upper bound < 0.75) contradicts its "D1 high" half. H-D2 FAIL (paired CI
  upper bound < +0.03) contradicts its "readout lags" half. Either is enough to
  score the call wrong. H-D1 NOT-ADJUDICABLE (Stage 0 validity failed) or
  INCONCLUSIVE in either gate leaves it unresolved, scored as a TIE per
  protocol-amendments.md.
- Both calls are scored on the PRIMARY pointer arm only. The secondary arm is
  reported, not scored.

Disclosure: the orchestrator call was recorded at first draft, before the
2026-10-04 pre-sign check showed the LoRA moving generic-prompt states by a
mean relative L2 of 0.10 to 0.50. That observation was not used to revise it.

Resolution (2026-10-05): each call is compared with the outcome in Outcome /
"Predictions vs outcome". The WIN / LOSS / TIE scores are the PI's to ratify
and are not assigned in this document.

## Outcome

Run executed 2026-10-05 under the signed instrument. This section was
transcribed on 2026-10-05 from the committed artifacts for PI review. The
terminal status and the one-sentence verdict are stamped by the PI with
`bin/exp resolve` and live in `experiment.yaml`. Exploratory tier-2 evidence,
single seed per arm, never pooled with the headline matrix. Confirmatory
claims rest on the primary pointer arm alone.

Proposed one-sentence summary (for the manifest `verdict:`; PI to confirm):
Readout-tracks-knowledge line falsified on its H-A leg as registered: on TEST
unknowns the pointer-arm calibrated confidence (R1) sits 0.1769
[0.1737, 0.1798] above chance against a 0.10 cap (confident-wrong 0.0007
passes), while H-B passes (0.0603), H-C passes (AUROC 0.9407
[0.9266, 0.9526]), H-D1 passes (frozen base gate 0.9762 [0.9718, 0.9805]) and
H-D2 passes (probe minus readout +0.0509 [0.0393, 0.0639]); matrix cell:
readout confidence tracks the base known-unknown axis; secondary letter-logit
arm shows the same pattern; exploratory, single seed.

### Run provenance

- Signed commit `1387e92d`, engine `29f7af0c`. All 15 sha256 pins were
  re-checked and matched before every stage (NOTEBOOK, 2026-10-05 night).
- Records: chain record `analysis-committed/run_records/dmcc-run-20261005.json`;
  Stage 1 records `dmcc-pointer-popqa.json` (primary) and
  `dmcc-letter-logits-popqa.json` (secondary). `outcome.verified` is `false` in
  all three and is left for the PI.
- Timeline (UTC, 2026-10-05): label 12:52-14:17; stage0-extract 14:18-21:24;
  Stage 0 freeze 21:44:25; pointer analyze 21:47-22:04, scored 22:05:05;
  letter-logit analyze 22:06-22:23, scored 22:23:51. Every stage exited rc 0
  apart from the two refused or failed first attempts under Anomalies.
- Number sources: `analysis-committed/dmcc-pointer-popqa_gate_summary.json`
  (primary), `analysis-committed/dmcc-letter-logits-popqa_gate_summary.json`
  (secondary), `analysis-committed/stage0_freeze.json` and
  `analysis-committed/label_and_split_counts.json`. Values are transcribed, not
  recomputed, and rounded to 4 decimal places; the files hold full precision.
  The H-A, H-B, H-C and H-D2 points, the H-D2 engine CI and the frozen-direction
  TEST AUROCs were checked equal to each arm's engine `confidence_report.json`,
  whose sha256 is in the Stage 1 run record.

### Labels, populations and G0

- 14,267 rows labeled: known 1,316, unknown 10,764, ambiguous 2,187. Thinking
  markers: 1 of 470,811 generations (rate 2.1e-6, bound 0.05, not flagged).
- 27 exemplar-collision rows excluded, as pre-registered (expected 27).
  Primary rows: 12,067.
- Known / unknown by split: FIT 525 / 4,304, CAL 268 / 2,142, TEST 514 / 4,314.
  The engine split (FIT 4,829, CAL 2,410, TEST 4,828) equals the harness split.
- G0 integrity: PASS on both arms (split identity, ambiguous excluded, engine
  commit, checkpoint digest). G0 floors: met (TEST known 514 against 150,
  unknown 4,314 against 300). The cell is adjudicable.

### Stage 0 (instrument validity; decides only H-D1 adjudicability)

- S0 floors met (FIT 525 / 4,304, CAL 268 / 2,142). Extraction integrity: OK
  (anchor CAL coverage 1.0, answer_end CAL coverage 0.9996 against the 0.95
  minimum).
- S0-G1: **PASS.** Frozen gate direction (anchor, layer 14) CAL AUROC 0.9792
  [0.9728, 0.9853]; FIT out-of-fold AUROC at layer 14 0.9838.
- S0-G2: **PASS.** Permuted gate FIT out-of-fold AUROC at the gate layer 14:
  0.4951. CAL AUROC of the frozen permuted projection (its own sweep layer 17):
  0.4901 [0.4486, 0.5337]. Both inside [0.40, 0.60].
- Descriptive: dial direction (answer_end, layer 12) CAL AUROC 0.9804
  [0.9741, 0.9860]. Gate CAL ECE: raw sigmoid 0.0159, Platt 0.0177, isotonic
  0.0190.
- H-D1 is adjudicable.

### Stage 1 gate results (TEST)

| Gate | Pointer (PRIMARY) | Letter-logit (SECONDARY, exploratory) |
|---|---|---|
| H-A a1: mean(R1 - 0.25), unknown | 0.1769 [0.1737, 0.1798]: **FAIL** | 0.1719 [0.1679, 0.1757]: **FAIL** |
| H-A a2: confident-wrong, all unknown | 3 / 4,314 = 0.0007, Wilson [0.0002, 0.0020]: **PASS** | 5 / 4,314 = 0.0012, Wilson [0.0005, 0.0027]: **PASS** |
| **H-A combined** | **FAIL** (a1 fails) | **FAIL** (a1 fails) |
| H-B: underconfident-right, all known | 31 / 514 = 0.0603, Wilson [0.0428, 0.0843]: **PASS** | 22 / 514 = 0.0428, Wilson [0.0284, 0.0640]: **PASS** |
| H-C: AUROC(R1 -> known) | 0.9407 [0.9266, 0.9526]: **PASS** | 0.9525 [0.9419, 0.9617]: **PASS** |
| H-D1: frozen base gate, layer 14 | 0.9762 [0.9718, 0.9805]: **PASS** | 0.9736 [0.9671, 0.9793]: **PASS** |
| H-D2: AUROC(KU probe) - AUROC(R1) | +0.0509 [0.0393, 0.0639]: **PASS** | +0.0408 [0.0322, 0.0500]: **PASS** |

- H-A companions: unknown accuracy 0.3832, Wilson [0.3688, 0.3978]; mean R1 on
  unknown 0.4269 (pointer). Letter-logit: 0.4077 [0.3932, 0.4225]; mean R1
  0.4219.
- H-B companions and precondition: known accuracy 0.9689 (pointer) and 0.9728
  (letter-logit), both above the 0.50 diagnosticity floor, so H-B is
  adjudicable. Mean R1 on known 0.7534 / 0.8441. Underconfident-right among
  right known rows 0.0622 / 0.0440.
- H-C: the in-cell point equals the engine point on both arms.
- H-D2 detail: KU probe at layer 15, TEST AUROC 0.9916 [0.9886, 0.9941]
  (pointer) and 0.9933 [0.9912, 0.9953] (letter-logit). Engine permuted-label
  CV AUROC 0.4776 / 0.4871, inside [0.40, 0.60], so the precondition holds.
  In-cell paired CI of the difference: [0.0397, 0.0647] / [0.0320, 0.0509].
- H-D1 registered comparison with the readout, AUROC(D1) - AUROC(R1): pointer
  +0.0355, engine CI [0.0245, 0.0482] (in-cell [0.0249, 0.0482]). That meets
  the registered reading "+0.03 with CI lower bound > 0", so on the primary arm
  the base axis carries more than the readout reports. Letter-logit +0.0211,
  engine CI [0.0125, 0.0300] (in-cell [0.0126, 0.0308]): the CI excludes 0 but
  the point is below +0.03, so the registered reading is not met on the
  secondary arm.

### Interpretation matrix

Both arms: H-D1 PASS and H-C PASS, so the registered cell is **"readout
confidence tracks the base known-unknown axis"**. The fresh probe reads
0.9916 (pointer) and 0.9933 (letter-logit), above the 0.75 d2-high point. H-D2
PASS adds that the decision state still carries more KU signal than R1
expresses; on the primary arm the frozen base axis does too, by the registered
margin. The matrix is indexed by H-D1 and H-C only. The H-A failure is a
separate leg of the line falsifier (next subsection) and does not move the
cell.

### Falsifier adjudication (registered text applied; PI to confirm)

- Readout-tracks-knowledge line ("falsified if H-C FAILS ... or H-A FAILS"):
  the H-A condition is met. The a1 gap CI lower bound is 0.1737, above 0.10.
  The H-C condition is not met. The line is therefore falsified on its
  calibration leg (unknown-row confidence is not near chance), not on its
  ranking leg: the readout separates known from unknown at AUROC 0.9407.
- Residual-signal prediction: not falsified (H-D2 PASS).
- Base-axis-transfer prediction: not falsified (H-D1 PASS, Stage 0 valid).
- The terminal status (`falsified` or `resolved`) is the PI's call at
  `bin/exp resolve`.

### Sensitivity analyses (registered, descriptive; no verdict changes)

- **Thinking-marker policy.** One TEST row (an unknown) had a marked
  generation. With it dropped, the pointer arm reads: gap 0.1768,
  confident-wrong 0.0007, underconfident-right 0.0603, H-C 0.9408, H-D1 0.9762.
  The letter-logit arm reads 0.1719, 0.0012, 0.0428, 0.9525 and 0.9736. With
  marker-affected questions dropped, the label counts are known 1,316, unknown
  10,763 and ambiguous 2,187: one unknown fewer.
- **Exemplar-collision rows.** The 27 excluded "AU" (Australia) rows are
  labeled 9 known, 4 unknown and 14 ambiguous. Exact "Au" echoes: 0 greedy and
  0 sampled. The rows were dropped before the split, so no gate population
  contains them.

### Secondary (registered descriptive; no gate)

- **Recall vs recognition.** Unknown-row 4-way accuracy against chance 0.25:
  pointer 0.3832 [0.3688, 0.3978]; letter-logit 0.4077 [0.3932, 0.4225].
- **Conformal by knowledge** (pointer; letter-logit in brackets). At alpha 0.1,
  known coverage is 0.9961 with mean set size 1.4397 [0.9981, 1.3035], and
  unknown coverage is 0.8927 with mean set size 3.1034 [0.8922, 3.0306]. At
  alpha 0.2, known is 0.9961 / 1.2840 [0.9903, 1.1537] and unknown is
  0.7976 / 2.6136 [0.7821, 2.4817]. Sets widen on unknowns, as expected.
  Unknown coverage sits slightly under nominal, and known coverage sits above
  it.
- **Popularity quartiles** (pointer, Q1 to Q4):
  - accuracy 0.4705, 0.3863, 0.3828, 0.5427;
  - mean confidence 0.4657, 0.4357, 0.4365, 0.5086;
  - known share 0.1062, 0.0397, 0.0456, 0.2345.

  The pattern is not monotone. The letter-logit block is in its summary.
- **Per relation.** Among relations with at least 25 unknown TEST rows,
  unknown-row accuracy runs from 0.2809 (director, n 776) to 0.8466 (father,
  n 163) on the pointer arm. On the letter-logit arm it runs from 0.2857
  (sport, n 28) to 0.8773 (father). Known TEST rows concentrate in capital
  (139), country (141), sport (73) and capital of (41).
- **Arms, all TEST rows** (pointer; letter-logit in brackets):
  - option accuracy 0.4455 [0.4679];
  - option ECE, R0 0.0891 vs R1 0.0814 [0.0943 vs 0.0500];
  - correctness AUROC, R0 0.7190, R1 0.7202, P-dial 0.7612, S 0.7568
    [0.7491, 0.7495, 0.7670, 0.7692].
- **Frozen base dial on TEST decision states.** Taken from the engine
  `directions.base_dial` block, not the committed summary: 0.9357 (pointer)
  and 0.9679 (letter-logit).

### Anomalies (run record and NOTEBOOK)

None of these changed a pinned file, a registered constant, a population or a
threshold.

1. **Operator handover.** The first operator agent launched build-pool through
   stage0-extract (12:52Z-14:18Z). Its session then ended while
   stage0-extract ran detached.
   - A second operator took over at about 16:37Z, with shards 000-004
     complete and shard 005 running.
   - It waited on the detached driver (Windows PIDs 8092 / 71556) without
     touching it, then ran every later stage.
   - Nothing was restarted or duplicated.
   - The first operator left no NOTEBOOK entry. Its facts were reconstructed
     from the logs and `label_run.json`.
2. **Extraction slowdown.** stage0-extract took about 7.1 h against the
   5-5.3 h estimate. Shard times climbed from 20 to 43 min for shards
   004-007, then fell back to 25-30 min.
   - This correlated with WSL CPU contention: a load average near 15 from
     another session's CPU-only node workloads.
   - The GPU held only the shard container.
   - All 15 shards completed: 7,239 of 7,239 rows with both families, and a
     provenance line in every shard log.
3. **Permission fix (chmod).** stage0-validate attempt 1 exited rc 1. The
   runner had written all 14,479 extraction files as `root:root` mode 600, so
   the WSL harness could not read them.
   - Remedy, per `local-runtime.md`: a throwaway container from the same
     pinned image ran `chmod -R a+rX`. Only permission bits changed, no
     content.
   - Attempt 2 exited rc 0. The attempt 1 logs are kept.
4. **Stage 1 run from Windows Python.** stage-engine (pointer) attempt 1 from
   WSL was refused fail-closed. The Windows `F:/` `source_checkpoint` path
   does not resolve from Linux Python, so the tree digest was the empty-tree
   hash, which did not match the pin, and nothing was staged.
   - Every Stage 1 stage then ran under Windows `py -3.11`, consistent with
     the cell's `py.exe` local-run launcher.
   - Both checkpoint digests verified (`e0cc616d...`, `3aef07e2...`).
5. **asciimatics install.** The tuner CLI in the runner containers installs
   asciimatics at start-up. It is an ephemeral install into a `--rm`
   container: a UI dependency, not a numerical one.
6. **Dry-run on host Python.** The host-Python engine dry-run failed on a
   missing `pandas`. It was re-run inside the pinned Stage 1 image (rc 0).
7. **Descriptive permuted-direction scores.** The frozen PERMUTED gate
   direction (layer 17) scores TEST decision `<answer>` states at AUROC 0.7632
   (pointer) and 0.8126 (letter-logit), against about 0.49 on base CAL.
   - It is a descriptive control and does not enter any gate.
   - H-D1 is registered against the 0.75 threshold and against R1, not against
     this control, so no verdict changes.
   - Post-hoc caution, not interpreted further: on decision-model states, a
     direction fit to shuffled labels reads known vs unknown well above 0.5.
     The H-D1 margin over arbitrary mid-depth directions is therefore smaller
     than its margin over chance.
8. **Minor Stage 0 notes.**
   - 8 rows have an empty first line.
   - 1 CAL row lacks a dial capture; answer_end coverage is 0.9996.
   - The layer-0 anchor reads AUROC 0.5 with PCA zero-variance warnings,
     because the anchor token is identical across rows.

### Post-hoc descriptive note on H-A (not pre-registered; does not change the FAIL verdict)

On TEST unknowns, the pointer model's accuracy is 0.383 (Wilson
[0.369, 0.398]) against 0.25 chance, and its mean calibrated confidence is
0.427. The accuracy figure is the registered recall-vs-recognition companion.
The reading below is post-hoc.

- **The H-A ideal conflates two failures.** H-A's pre-registered ideal, "near
  chance on unknowns", treats a base-model unknown (0 of 32 sampled answers
  correct) as a row the decision model should not be able to answer. But the
  label measures recall failure: the base model cannot generate the answer.
  On a 4-way choice the model can still recognize the answer or eliminate the
  distractors, and on these rows it is right well above chance.
- **Confidence against own accuracy.** Measured against its own unknown-row
  accuracy rather than against 1/N, mean confidence exceeds accuracy by 0.044
  (pointer). On the letter-logit arm, accuracy is 0.408 and mean R1 is 0.422.
  That is arithmetic on the two reported companions, not a registered
  statistic.
- **Status of the FAIL.** None of this rescues H-A. The registered gate
  compares confidence with chance, and it fails. The note only says what the
  failure measures.
- **Follow-up design.** A follow-up should separate the two: for example,
  gate on an unknown-and-unrecognized subset (unknown rows the base torso also
  fails to recognize under a recognition probe), or replace "near chance"
  with a recognition-controlled criterion (unknown-row confidence against the
  model's own unknown-row accuracy). Either needs its own registration.

### Predictions vs outcome (primary pointer arm; scores for the PI to ratify)

- **Orchestrator.** Frontmatter call: "S0 passes; H-C and H-D2 pass; H-A
  fails on the gap leg; H-D1 passes". Every element was realized.
  - Per-gate table:
    - S0-G1 PASS: realized.
    - H-A FAIL on a1 with a gap of about 0.15 to 0.20: realized, at 0.1769.
    - a2 PASS: realized.
    - H-B INCONCLUSIVE or FAIL: not realized; H-B PASSED at 0.0603, Wilson
      upper 0.0843.
    - H-C PASS or INCONCLUSIVE with a point of 0.75 to 0.85: PASS realized,
      but the point, 0.9407, is above the stated range.
    - H-D1 PASS and H-D2 PASS: realized.
    - Matrix cell "readout tracks the base KU axis": realized.
  - Mechanism: the call's basis was that a CAL-fit temperature would leave
    unknown-row confidence near pooled 4-way accuracy rather than near 0.25.
    That matches the companions, mean R1 0.4269 against unknown accuracy
    0.3832.
- **User (PI).** The call had two parts.
  - Readout, "Blind to knowledge" (H-C fails): not realized. H-C PASSED, with
    a CI lower bound of 0.9266 against 0.75. Under the recording notes'
    registered falsifier of this call, H-C PASS contradicts it.
  - Internal signal, "Knows but doesn't say": both halves realized. D1 is high
    (H-D1 PASS, 0.9762), and the readout lags (H-D2 PASS, +0.0509, CI lower
    bound 0.0393 > 0).
  - The matrix cell the user's calls picked out (H-D1 PASS with H-C FAIL) was
    not realized. The realized cell is H-D1 PASS with H-C PASS.
- **Scores and ledger.** WIN / LOSS / TIE scores are not assigned here. The
  PI ratifies them and records them in `docs/prediction-scoreboard.md`.
