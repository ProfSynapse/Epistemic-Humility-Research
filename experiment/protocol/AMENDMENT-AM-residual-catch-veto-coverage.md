---
amendment: AM
slug: residual-catch-veto-coverage
status: >-
  DRAFT (this file signs when the user records a prediction and says proceed;
  gates in section 4 lock at signing). Run stays gated on user signing plus
  dual predictions; no launch, no PR yet; PR merge order serialized behind AL.
question: >-
  Of the residual confabulations the pre-generation radial controller cannot
  reach (the gate-miss set the answerability gate misreads as answerable, 43
  rows on the A0 raw-base surface, ambiguous-flavor concentrated), does a
  post-generation correctness veto refit on the A0 generation surface separate
  those residual confabs from good answers, or is the veto blind exactly where
  the pre-gen gate is blind?
predictions:
  orchestrator:
    calls:
      AM-G1: PASS (~70%)
      AM-G2: PASS (~60%)
    recorded: 2026-07-05
    basis: >-
      The veto reads post-generation content and the residual confabs are
      answered fabrications, so the content signal the S/W/U veto keys on
      should be present regardless of why the pre-gen gate missed the question
      (the gate reads pre-generation answerability; the veto reads the emitted
      answer, a different object). The raw-base transfer AUROC is 0.768 on the
      full W population and a same-surface refit should meet or beat that, so
      an AUROC floor of 0.62 has real headroom (AM-G1 ~70%). The bet that is
      genuinely open is whether the ambiguous-flavor residual specifically
      still reads low-trust; ambiguous questions may produce plausible-sounding
      confabs whose content looks answerable, which is the exact failure mode
      that could pull AM-G2 down (only ~60%). The whole point of the residual
      is that it is the hard tail the pre-gen controller could not carve out.
  user:
    calls:
      AM-G1: null
      AM-G2: null
    recorded: null
    quote: null
outcome: null
scoreboard: pending
---

# Amendment AM: Post-generation veto coverage of the radial-unreachable residual confabs

**Status:** DRAFT (this file signs when the user records a prediction and
says proceed; gates in section 4 lock at signing).
**Tier:** A (new evidence cell; new post-generation readout with a behavioral
discrimination claim; gates pre-stated; reported separately from PROTOCOL v0.3
headline and from the PR #205 veto operating characteristics).
**Branch:** `amendment-am-residual-catch` (this branch; one amendment, one
branch, one PR). PR merge order serialized behind AL.
**Depends on:** the PR #205 veto-warning-policy characterization
(`experiment/phase1/probe/analysis/veto_warning_policy_20260704/`), which
marked this exact measurement GPU-BLOCKED (its report Section 6); the radial
ceiling simulation (`experiment/phase1/probe/analysis/radial_ceiling_sim_20260704/`),
which defines the unreachable residual; and the Amendment W raw-base
generation + dual-position extraction instrument
(`experiment/phase1/probe/amendment_w_base_model_extract.py`).
**Relation to AL:** AL writes against the propensity direction to convert
confabs to refusals (a pre-generation steering intervention). AM is the
complementary post-generation question: for the confabs the pre-generation
controller leaves standing, can a post-generation veto flag them. AM and AL do
not consume each other; AM runs on Modal (cloud, cost-capped), AL on the local
GPU, so they do not contend for hardware.

## 1. Motivation and strategic position

PR #205 characterized a post-generation "community notes" veto: after the model
answers, a negated correctness dial (post-L20) attaches a warning label. It
established the operating characteristics per checkpoint (raw base, grpo-v2) and
then hit one wall. Its Section 6 ("AH residual-catch feasibility: GPU-BLOCKED")
states the open question verbatim: of the confabs the pre-generation radial
controller cannot reach, what fraction does the post-generation veto catch. That
step was blocked because it needs post-generation activations for the A0 rows,
and the `ah_main/gen_A0` tree holds only pre-generation scalars (`score_L24`,
`caution_dist_z`) plus `answer_text`; there are zero activation tensors anywhere
in that tree. Computing the veto requires a fresh GPU generation plus
post-generation hidden-state extraction pass on the raw base. This amendment
runs that pass on Modal and answers the residual-catch question.

Why this is a new cell and not an analysis-only completion of PR #205: the two
generation surfaces are incompatible. The A0 rows were generated under the AH
abstention-affording baseline system prompt (greedy, 96 new tokens; see
`ah_main/manifest.json`). The raw-base veto in PR #205 (Amendment W) was fit on
post-L20 activations generated under Amendment S's answer-encouraging system
prompt (48 new tokens, SelfAware pool; `amendment_w_base_model_extract.py`
imports S's `SYSTEM_PROMPT` verbatim). The correctness direction cold-transfers
across surfaces at only about 0.679 (Amendment T lesson, restated as PR #205
report caveat 2: "the veto must be refit on each deployed checkpoint"). So the
existing veto cannot simply be applied to freshly-extracted A0 activations; a
valid number requires refitting the veto on the A0 generation surface and
labeling A0 answered rows by correctness. That is new evidence with a
behavioral-readout claim, which per
`.skills/experiment-runner/reference/amendment-vs-lab-notebook.md` is Tier 2, not
a Tier 3 lab-notebook pass, and its results must never be pooled with the
published PR #205 veto numbers.

If AM passes, the two-signal escape hatch has a documented backstop for the exact
tail the pre-generation controller leaves standing (the ambiguous-flavor gate
weakness), and the AL steering line and the AM veto line become complementary
fabrication controls. If it fails, the finding is that the veto is blind where
the gate is blind: the residual confabs read answerable to the pre-gen gate and
low-content-trust nowhere, which is a real, publishable boundary on the
post-generation readout.

## 2. Hypotheses

- H-catch: the post-generation correctness veto, refit on the A0 surface,
  separates the residual gate-miss confabs from good answered rows above chance,
  because the veto reads the emitted answer content (a different object from the
  pre-generation answerability the gate reads), so the residual being
  gate-unreachable does not imply it is veto-unreachable.
- H-null (falsifier hypothesis): the residual confabs are gate-unreachable
  precisely because they read as ordinary answerable content, so the
  post-generation content signal is also flat on them and the veto separates them
  from good answers no better than a permuted assignment.
- H-flavor (descriptive, not gated): if there is a catch, it is weakest on the
  ambiguous flavor (33 of the 43 residual rows), because that is the flavor the
  pre-gen gate already misreads as answerable.

## 3. Design

### 3.1 Surface, checkpoint, and the residual set

- Checkpoint: the raw `unsloth/Qwen3-4B-bnb-4bit` instruct base, no adapter,
  identical to the A0 arm of `ah_main` (`ah_main/manifest.json`,
  `base_model: unsloth/Qwen3-4B-bnb-4bit`, `adapter: NONE-raw-instruct-base`).
- Generation surface: same prompt/decode contract as the A0 cell. The AH
  baseline abstention-affording system prompt, `enable_thinking=false`, greedy
  decode, `max_new_tokens=96`, seed matched to the A0 config
  (`config_sha: 68847c8396f688d4`). The A0 answered-row grades reproduce from
  regeneration on the same grader; any regeneration drift is absorbed by
  comparing the veto against a permutation null computed on the same regenerated
  rows.
- Batched generation config (registered from the start; AM is a new surface,
  not parity-locked to the batch-1 A0 run, so it registers an efficient config
  rather than inheriting batch-1): HuggingFace `generate` with left-padding,
  `batch_size = 12` for the 4B base on the A10G (a middle-of-range value in the
  8 to 16 window that fits the A10G comfortably at 96 new tokens; if the chosen
  GPU is smaller, the numerics smoke in section 5 sets the largest batch that
  agrees and that value is recorded here at launch). Greedy decode is
  deterministic, so batching must not change token output; the section 5
  precondition enforces token-level agreement with batch-1 before the full run.
  Batch size is part of the frozen config: the value that passes the smoke is
  recorded and does not change mid-run. Left-padding with the batch is the only
  deviation from the A0 batch-1 mechanics, and it is validated, not assumed.
- The residual set (frozen, deterministic, pre-registered from cached A0
  behavior): the gate-miss confabs are the confabulations on unanswerable
  questions that read as answerable to the answerability gate at the balanced
  operating point, i.e. `score_L24 >= 6.559` (the radial balanced `gate_cut`).
  On the cached A0 rows this is exactly 43 confabs (33 ambiguous, 5
  controversial, 2 unsolved_problem, 1 each false_assumption / none /
  future_unknown). This deterministic set is the object the veto is scored on.

  Relationship to the report's "56": the radial report's 56 (mean 55.7, CI
  [42, 70]) is the oracle/Bernoulli-simulated stochastic residual at the balanced
  point. The deterministic gate-miss set (43 rows) is the actual, reproducible
  set of confabs the pre-gen controller leaves standing, and matches the report's
  "33 of the unreachable confabs are ambiguous rows the gate misreads." AM uses
  the deterministic 43-row set as the scored residual and reports the
  relationship to the oracle 56 for continuity. If regeneration changes which
  rows confabulate, the residual is recomputed on the regenerated rows by the
  same `score_L24 >= 6.559` rule and the count is reported; the rule, not the
  count, is frozen.

### 3.2 The veto, refit on the A0 surface

- Generate + extract: run `amendment_w_base_model_extract.py` (raw base,
  forced-answer generation, dual-position `__pre` / `__post` safetensors per
  answered row, L0..L36) on the A0 question pool, ported into the Modal harness
  pattern of `scratchpad/modal_al_true_a0.py` (Unsloth image, `entrypoint([])`,
  `HF_HUB_DISABLE_XET=1` and `HF_HUB_ENABLE_HF_TRANSFER=0` baked into the image
  env plus re-exported in the function, `UNSLOTH_COMPILE_DISABLE=1` if on T4).
  The generation surface is pinned to the AH baseline prompt / 96 tokens, not
  Amendment S's prompt, so the extracted activations lie on the A0 surface.
- Correctness labeling of A0 answered rows: class 1 (hallucination /
  low-trust) = confab on an unanswerable question OR a wrong answer on an
  answerable question; class 0 (good) = a correct answer on an answerable
  question. On the cached A0 answered population this is 395 hallucination vs 89
  good (base rate 0.816). Grades come from the A0 grader, byte-pinned.
- Veto fit: the correctness dial is a post-L20 logistic readout (PCA-128
  randomized + saga LR, the project-standard CPU probe recipe), fit out-of-fold
  on the A0 answered population, class-weighted to correct for the 0.816 base
  rate. The veto score is the negated dial (higher = more likely hallucination),
  identical convention to PR #205. The residual confabs are scored by the
  out-of-fold veto (a residual confab is in the hallucination class, so its
  score is a genuine held-out prediction, not an in-fold fit).

### 3.3 Primary statistic and null

- Primary statistic (AM-G1): the veto AUROC separating the 43 residual gate-miss
  confabs (positives) from the 89 good answered rows (negatives), using
  out-of-fold veto scores. This is the same discrimination object the S / W / U
  veto claims are stated in, restricted to the residual tail.
- Catch-fraction (descriptive, reported not gated): at a pre-registered
  operating point (the aim-small precision-floor point, precision >= 0.80 with
  bootstrap CI lower bound >= 0.70, chosen exactly as PR #205 selects it), the
  fraction of the 43 residual confabs the veto warns. Reported with its binomial
  spread; see section 4 for why this is descriptive and not a gate.
- Null (AM-G2): a permutation null on the residual-vs-good discrimination.
  Permute the veto scores across the residual-plus-good pool within the answered
  population (1,000 permutations, seed 20260705), recompute AUROC each time,
  report the observed AUROC's permutation p and the null mean / p95. This is the
  causal analog of the PR #205 permutation null and of the radial sim's p=0.005
  gate/commitment permutation.

## 4. Gates (LOCK at signing)

Aim-small derivation (thresholds set from the expected effect size and its
uncertainty, not round defaults; the AJ cautionary tale is a gate sitting inside
the estimate's error bars, which cannot adjudicate). Inputs: PR #205 raw-base
veto operating characteristics (report Section 2), residual N = 43, good N = 89.

Why the gate is on discrimination (AUROC), not on the raw catch count. At the
raw-base max-recall operating point the expected catch on 43 rows under H-catch
(recall 0.483) is 20.8 confabs with binomial sd 3.3 (2sd-low 14.2), while the
permuted null at that threshold's warn fraction (0.330) catches 14.2 with sd 3.1
(2sd-high 20.4). The H-catch and null distributions overlap almost entirely on
43 rows: an absolute catch-count floor would sit inside both error bars and
could not separate signal from null. That is exactly the AJ trap. The AUROC of
the residual-vs-good separation is far better powered: the expected raw-base
transfer AUROC 0.768 has Hanley-McNeil SE 0.047 on these class sizes (CI [0.676,
0.860]), which clears 0.5 at z = 5.7, and a same-surface refit is expected to
meet or beat the cross-dataset transfer number. So the primary gate is the
AUROC, with the catch count reported descriptively.

- AM-G1 (discrimination floor): the out-of-fold veto AUROC separating the 43
  residual gate-miss confabs from the 89 good answered rows is at least **0.62**.
  Derivation: 0.62 sits below the expected 0.768 lower error bar (CI-low 0.676)
  and above the 0.5 null upper error bar (approximately 0.60 by Hanley-McNeil at
  these class sizes), i.e. inside the aim-small gap between "no better than
  chance" and "as good as the honest transfer prior." A pass at 0.62 says the
  residual is meaningfully separable; it does not require matching the full-
  population number. Additionally the bootstrap 95% CI lower bound on this AUROC
  (1,000 row resamples, seed 20260705) must exceed **0.55** (the CI must clear
  chance with margin, not merely touch it).
- AM-G2 (specificity against the null): the observed residual-vs-good AUROC
  exceeds the permutation null with permutation p <= **0.01** (that is, at most 1
  of the 1,000 permutations reaches the observed AUROC; the resampling floor is
  1/1001, so p <= 0.01 demands the observed value sit essentially outside the
  null cloud). This mirrors the p=0.005-class nulls the radial and PR #205
  analyses already clear.

FALSIFIER: AM-G1 or AM-G2 failing means the post-generation veto does not
separate the radial-unreachable residual from good answers on this surface: the
veto is blind where the pre-gen gate is blind. The result is recorded as a
post-generation-readout boundary (a use-the-signal null localized to the residual
tail); no goalposts move. AM-G1 passing with the catch-fraction descriptively
low (the veto discriminates but no single threshold warns a useful share of the
residual at the precision floor) is a PARTIAL outcome: mechanism present,
operating point not deployable, claimable only as such.

Do not move the goalposts. If the regenerated residual count differs from 43,
the gates apply to the recomputed deterministic set (by the frozen
`score_L24 >= 6.559` rule) with class sizes reported; the AUROC floor 0.62 and
permutation p 0.01 do not change. If the result is ambiguous at these gates,
report it as ambiguous and let the user adjudicate.

## 5. Preconditions and approvals

1. User sign-off on this document and a recorded user prediction
   (dual-prediction practice; scoreboard `docs/prediction-scoreboard.md`). The
   YAML frontmatter `predictions.user` is a placeholder until then.
2. Modal only; the local GPU is off limits (live experiment). Wait for any
   in-flight Modal app (currently `eh-al-true-a0`) to finish before launching so
   the run does not contend.
3. Numerics smoke before the full run (protects the surface definition without
   burning the cell): on a fixed 20-row subset of the A0 pool, generate greedy
   at batch-1 and at the registered `batch_size = 12` (left-padded) in the same
   container, and require **token-level agreement** on all 20 rows (identical
   generated token ids, hence identical `answer_text` and identical grades). If
   greedy outputs agree, proceed to the full batched run at the registered
   batch. If they diverge on any row, fall back to the **largest batch that
   agrees** (bisect downward: 8, then 4, then 2, then 1), record that value as
   the frozen batch in section 3.1, and run at it. The smoke is a few seconds of
   generation and is part of the same container as the full run, so it does not
   add a separate spend. Rationale: greedy decode is deterministic and batching
   with left-padding must not change token output; the smoke turns that
   invariant into a checked precondition rather than an assumption, so the
   surface the veto is fit on is provably the same surface batch-1 would have
   produced.
4. Pre-registered cost cap: **$5 of Modal credit**. The run is one container:
   generate + post-L20 extract on 484 answered rows of the 4-bit base
   (T4 if it fits, else L4 / A10G). Batched generation (registered
   `batch_size = 12`, left-padded) is expected to cut the generation wall time
   by roughly 4x to 8x versus the A0 batch-1 run, so the cap gains margin;
   post-generation extraction is a single forward per answered row and is the
   same cost as batch-1. If the pre-launch estimate still exceeds $5, stop and
   report rather than launch.
5. Container env (mandatory): `HF_HUB_DISABLE_XET=1` and
   `HF_HUB_ENABLE_HF_TRANSFER=0` (hf_xet hangs multi-GB downloads);
   `UNSLOTH_COMPILE_DISABLE=1` if on T4. Secrets via environment, never printed;
   logs redacted through `sed 's/hf_[A-Za-z0-9]*/hf_[REDACTED]/g'`.
6. Grader identical to the A0 cell; grading config byte-pinned. Correctness
   labeling of answered rows uses that grader's `correct` field.

## 6. Instrumentation (descriptive, gate-free)

- Catch-fraction at the aim-small precision-floor operating point, on the 43
  residual confabs, with binomial CI, plus the calibrated isotonic
  P(hallucination | warned).
- Flavor breakdown of catches and escapes on the residual set (the H-flavor
  prediction: ambiguous rows are the hardest catch).
- Full-population veto AUROC on all A0 answered rows (395 hallucination vs 89
  good), for continuity with PR #205's per-checkpoint AUROC table and to show the
  residual tail against the whole population.
- Relationship of the deterministic 43-row residual to the oracle 56 (report the
  overlap and the count under regeneration).
- Post-L20 layer sweep of the veto AUROC on the residual (did L20 remain the
  peak layer on this surface, or does the residual read better at another
  depth).
- Map-territory exhaust: per-row provenance (question, flavor, gold_class,
  score_L24, gate-miss flag, answer_text, correctness label, out-of-fold veto
  score, warned flag) packaged for publication with approval. Not pooled with the
  PR #205 veto artifacts.

## 7. Interpretive caveats (pre-stated)

- Surface transfer motivates the refit, not a reuse: the correctness direction
  cold-transfers across surfaces at about 0.679 (Amendment T; PR #205 caveat 2),
  so the existing raw-base veto is not applied to A0; a fresh on-surface fit is
  the whole point. The refit AUROC is therefore an on-surface, out-of-fold
  number, not a cross-dataset transfer number, and is reported as such.
- Single checkpoint, single seed. A pass licenses a readout claim on this raw-
  base surface only; multi-seed replication is required before any headline, and
  the number is never pooled with the PR #205 published veto operating
  characteristics.
- The good class is small (89 correct answered rows on the raw-base A0 surface;
  the base is a heavy over-answerer, so most answered rows are hallucinations).
  The AUROC CI is correspondingly wide (Hanley-McNeil SE about 0.05); the gate
  floors are set with that width in mind, and the bootstrap CI lower bound is the
  operative teeth on AM-G1.
- The residual is defined by the balanced radial operating point
  (`gate_cut = 6.559`). A different operating point defines a different residual;
  AM answers the balanced-point residual, matching the report's Section 6
  framing. The conservative and aggressive points are out of scope here.
- Regeneration noise: the A0 baseline grades come from one generation pass;
  regenerating on Modal may shift which rows confabulate. The residual is
  recomputed on the regenerated rows by the frozen rule, and the permutation null
  shares any regeneration drift, so the specificity gate is robust to it. The
  absolute catch count is reported with this caveat.
