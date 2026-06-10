# Experiment Protocol (pre-registration draft v0.3)

**Working title:** *Loss-Averse Humility: Comparing SFT, DPO, and Kahneman-Tversky
Optimization for Teaching Small Language Models to Say "I Don't Know"*

**Status:** DRAFT v0.3. User sign-off required BEFORE any training run. This
version reconciles the stale v0.1 (2-arm, Qwen2.5, wrong tuner path) with the
finalized Phase 1 design: a three-way comparison plus a replication bridge arm,
pinned on Qwen3, with the data leakage and trainer gaps resolved, and (v0.3) a
full run matrix with seed-level confidence intervals and a pre-registered
sensitivity panel. Companion implementation blueprint:
`docs/architecture/phase1-pipeline.md`. Derived from gaps verified in
`../../meta-analysis/`.

**What changed in v0.3 (provenance):**

1. Run design upgraded from a single config per arm to a full matrix, to
   directly answer the field's one-config / no-error-bars problem that paper 1
   documents (the explicit goal: set the tone to differentiate against prior
   work). 4B headline = 3 seeds per arm at the pre-registered default config (9
   runs); a pre-registered sensitivity panel (learning-rate and beta) adds 10
   runs, for 19 runs at 4B. See the new run matrix in 3.1 and the panel in 3.1a.
2. Statistics upgraded to a two-layer uncertainty treatment (3.6): paired
   bootstrap over eval questions within a run, plus mean and CI across seeds for
   training stochasticity, plus McNemar on matched seeds.
3. Execution reframed (3.4): the RTX 3090 is the development, pilot, and
   smoke-run lane; HF Jobs is the parallel execution lane for the matrix (both
   paths supported by the existing tuner). Compute is not a binding constraint.
4. 8B confirm seed count raised from 1 to 2 up to 3 seeds at the default config
   (no panel at 8B). FLAGGED: this 8B bump is lead-proposed and PENDING USER VETO
   at the v0.3 sign-off; the user enabled cheap parallel compute but did not
   explicitly order three seeds at 8B.

**What changed from v0.1 (provenance), carried forward:**

1. Training methods upgraded from 2-arm (SFT vs KTO, DPO optional) to a full
   three-way (SFT vs DPO vs KTO) plus a Llama-2-7b-chat replication bridge arm.
2. Model pin moved from Qwen2.5-3B/7B to Qwen3-4B/8B-Instruct (text-only,
   Apache 2.0, ungated), thinking mode pinned OFF.
3. Tuner entry point corrected: `Trainers/kto/train_kto.py` (the v0.1 path
   `Trainers/rtx3090_kto/train_kto.py` no longer exists). A DPO trainer does not
   exist in the tuner and will be built.
4. Probe pool corrected: the on-disk TriviaQA pool is 17,944 rows and overlaps
   Cheng's 11,313-question test set. Probing and training move to a disjoint
   TriviaQA rc.nocontext train split to remove leakage.
5. Phase-2 rideshare added: a KTO desirable/undesirable mapping ablation
   (congruence vs correctness-safe) is registered in paper 2.

---

## 1. Motivation (one paragraph)

The literature establishes: (a) SFT-based IDK-training works but over-refuses
(our exact reanalysis: 42.71% over-refusal for Idk-SFT on Llama-2-7b-chat,
n=11,313); (b) preference optimization (DPO/PPO) roughly halves over-refusal
(our reanalysis: 23.27% for Idk-DPO) but needs paired preference data and
damages token-level calibration in other settings; (c) KTO, which takes exactly
the unpaired binary desirable/undesirable data that IDK splits naturally
produce, and whose asymmetric loss-aversion weighting mirrors the asymmetric
real-world cost of hallucination vs abstention, has never been applied to
abstention or calibration training (verified gap, 2026-06). KTO also requires no
reward model and no pair construction, making it the cheapest preference-class
method to deploy. Paper 2 runs all three on the same base model and the same
data budget and measures the full recall, over-refusal, truthful-rate, and
calibration decomposition after each run, in-domain and out-of-domain.

## 2. Hypotheses (carried from v0.1, adapted to the three-way)

- **H1 (primary):** On model-specific IDK data, KTO achieves a truthful rate
  (Ik-Ik + Ik-Idk) at least equal to Idk-SFT while reducing over-refusal by at
  least 25% relative to SFT, matching or approaching DPO's over-refusal
  advantage without preference pairs.
- **H2 (transfer):** KTO-trained abstention transfers out-of-domain at least as
  well as SFT-trained abstention. No prior OOD evidence exists for any
  preference-trained abstention.
- **H3 (calibration tension, newly central):** The three methods separate on
  token-level ECE measured on the same run. We pre-register the directional
  prediction that preference-class methods (DPO, KTO) improve abstention while
  degrading token-level calibration relative to SFT, and we measure whether KTO,
  via its loss-aversion weighting, degrades calibration less than DPO. This is
  the first measurement of the abstention-calibration tension across SFT, DPO,
  and KTO on a single training run.
- **H4 (loss-aversion dose-response):** KTO's loss-aversion weighting (its beta
  and its desirable/undesirable balance knob, the latter via the congruence vs
  correctness-safe mapping and the desirable_weight/undesirable_weight setting)
  gives control over the abstention/over-refusal trade-off that no other method
  offers natively. The beta arm of the sensitivity panel (3.1a) operationalizes
  the beta half of H4 directly: the panel measures whether moving beta moves the
  over-refusal operating point, separately for KTO and DPO. The
  desirable/undesirable balance half rides on the Phase-2 rideshare (the
  congruence vs correctness-safe mapping ablation).
- **Falsifiers:** H1 fails if KTO truthful rate is below SFT, or over-refusal
  reduction is below 10% relative. H2 fails if the OOD truthful-rate drop for
  KTO exceeds SFT's drop by more than 5 percentage points. H3 fails if no method
  separates on ECE beyond bootstrap CI overlap, or if the preference-class
  methods do not degrade calibration relative to SFT. H4 fails if the balance
  knob does not move the over-refusal operating point monotonically.

## 3. Design

### 3.1 Factors

| Factor | Levels |
|---|---|
| Training method | base (no fine-tune), Idk-SFT, Idk-DPO, Idk-KTO |
| KTO mapping (within the KTO arm) | congruence (primary), correctness-safe (ablation, Phase-2 rideshare) |
| Model | Qwen3-4B-Instruct (pilot, local RTX 3090), Qwen3-8B-Instruct (confirm, HF Jobs); thinking mode OFF (enable_thinking=False) |
| Bridge arm (validation) | Idk-SFT + Idk-DPO on Llama-2-7b-chat, compared to Cheng et al. published numbers |
| Eval domain | in-domain (TriviaQA held-out = Cheng test set), OOD-near (PopQA), OOD-far (MMLU, SelfAware, KUQ, CoCoNot, AbstentionBench), TruthfulQA |

**Run matrix.** The design answers the field's one-config / no-error-bars
problem head-on: the headline numbers carry seed-level confidence intervals, and
a pre-registered sensitivity panel demonstrates robustness without ever feeding
the headline. The full 4B matrix:

| Layer | Arms | Config | Seeds | Runs |
|---|---|---|---|---|
| Headline (4B) | SFT, DPO, KTO | pre-registered default (3.1a) | 3 | 9 |
| LR panel (4B) | SFT, DPO, KTO | default with learning-rate x3 and learning-rate /3 (2 cells per arm) | 1 | 6 |
| beta panel (4B) | DPO, KTO only | default with beta low and beta high (2 cells per arm) | 1 | 4 |
| **Total 4B** | | | | **19** |
| Confirm (8B) | SFT, DPO, KTO | pre-registered default only (no panel) | 3 (see note) | 9 |
| Bridge | Idk-SFT, Idk-DPO on Llama-2-7b-chat | Cheng replication | 1 | 2 |

**8B seed-count note (FLAG: lead-proposed, pending user veto at sign-off).** v0.2
ran 1 seed at 8B. Because the user confirmed compute is not a binding constraint
(small-model runs are cheap and the matrix executes in parallel on HF Jobs),
this draft raises the 8B confirm to 3 seeds at the default config to match the
headline rigor at confirm scale. The sensitivity panel stays 4B-only. This bump
was enabled but not explicitly ordered by the user, so it is marked for veto at
the v0.3 sign-off; if vetoed, the 8B confirm reverts to 1 to 2 seeds with no
other change.

**Headline-only rule (pre-registered, non-negotiable).** All headline claims and
the paper's primary tables come ONLY from the pre-registered default config. The
sensitivity panel is a robustness figure: it shows the headline conclusions do
not hinge on the exact learning rate or beta. The panel is NEVER a source of a
headline number, and no result is reported by selecting the best-looking panel
cell. This rule is what makes the panel a credibility gain rather than a
forking-paths liability.

### 3.1a Pre-registered defaults and sensitivity panel

The default config per arm, and the panel grid around it. Defaults are taken
from the trainers' shipped configs (verified in the submodule) and TRL
conventions; the panel brackets are pre-registered so no cell is cherry-picked.

| Arm | Default learning rate | Default beta | LR panel (x3, /3) | beta panel (lo, hi) |
|---|---|---|---|---|
| SFT | 2e-4 | n/a (SFT has no beta) | 6e-4, 6.7e-5 | n/a |
| DPO | 5e-6 | 0.1 (loss_type sigmoid) | 1.5e-5, 1.7e-6 | 0.05, 0.5 |
| KTO | 1e-6 | 0.1 | 3e-6, 3.3e-7 | 0.05, 0.5 |

Rationale:

- **Defaults are the shipped trainer values**, not invented: SFT learning rate
  2e-4 (the standard tier), DPO beta 0.1 / learning rate 5e-6 / loss_type
  sigmoid (vanilla DPO), KTO beta 0.1 / learning rate 1e-6. Using the shipped
  defaults keeps the headline config honest and reproducible.
- **The LR panel is per-arm-relative**, each arm sweeping its OWN default times
  3 and divided by 3. The arms have learning rates two orders of magnitude apart
  (SFT 2e-4 vs KTO 1e-6) because preference-class methods need much smaller
  steps; a single shared absolute learning rate across methods would be
  meaningless. "Shared" means the same x3 / /3 ladder SHAPE, applied to each
  arm's own default, so the robustness question ("is the result stable to a 3x
  learning-rate change?") is asked identically of every arm.
- **The beta panel is {0.05, 0.5} around the 0.1 default**, a deliberately wide
  bracket (half the default and five times the default). H4 needs the panel to
  visibly move the abstention / over-refusal operating point; a narrow bracket
  such as {0.05, 0.2} risks a flat, unreadable panel. Because the panel is
  pre-registered robustness and never a headline source, the wide bracket costs
  nothing scientifically and buys a clearer dose-response signal. The beta panel
  applies only to DPO and KTO (SFT has no beta), which is why the panel totals 6
  LR runs plus 4 beta runs, not 12.
- **LoRA budget is held identical across every run** (r=32, alpha=64,
  dropout=0.05 at 4B; identical target_modules). The panel varies ONLY the named
  hyperparameter (learning rate or beta); everything else, including the frozen
  question set and the data budget, is the default. This isolates the panel as a
  clean sensitivity probe rather than a confounded second experiment.

### 3.2 Model pin and rationale

Qwen3-4B-Instruct (pilot) and Qwen3-8B-Instruct (confirm), both Apache 2.0,
ungated, text-only. Selected because it is the only current open-weights family
that is simultaneously text-only (no vision-encoder confound for a text-QA
study), uniformly Apache and ungated (cleanly satisfying the
release-everything requirement), and sized at a near-exact 4B-pilot / 8B-confirm
pairing. Thinking mode is pinned OFF (enable_thinking=False) so the abstention
study runs on clean non-reasoning generations with no `<think>` traces to
complicate truthful-rate and token-ECE parsing. Full survey:
`docs/preparation/model-landscape.md`.

### 3.3 Data construction (the model-specific part)

The known/unknown split is model-specific by construction (Gekhman: training on
facts THIS model does not know causally drives hallucination), so labels are
regenerated for our model with a correctness-probing method, reusing Cheng's
recipe but not Cheng's labels.

**Probe pool and the leakage fix.** The on-disk TriviaQA validation pool (17,944
rows) is the source of Cheng's 11,313-question test set. Probing or training on
it would leak the test set into training. We therefore probe and train on the
disjoint TriviaQA rc.nocontext **train** split, and keep Cheng's 11,313 as the
held-out in-domain test set (which also makes the bridge arm directly comparable
to published numbers). research-trajectory.md always intended a train subset as
the probe source, so this is trajectory-faithful.

**Leakage guard (pre-registered, enforced at build time).** The probe/train
question set and the Cheng test question set MUST be disjoint under normalized
question text. The dataset builder asserts
`normalized(probe_questions) ∩ normalized(cheng_test_questions) == ∅` and aborts
on any non-empty intersection. Normalization matches the eval scorer and the
`cheng_test_gold.jsonl` keys.

**Contingency.** If the train-split fetch is infeasible, fall back to the 6,631
non-Cheng remainder of the validation pool (17,944 minus 11,313) as the
probe/train pool, recording the reduced n as a power caveat in §3.6. The leakage
guard keeps this fallback safe by construction.

**Probe (pinned).**

1. Probe the Qwen3-4B base on the TriviaQA train split: **32 stochastic samples
   at T=1.0, top_p=0.9, plus 1 greedy decode**, enable_thinking=False, no
   context, no few-shot, one fixed system prompt. The sample count is higher
   than Cheng's 10 (the trajectory's mandatory improvement) and gives P_correct
   on a 1/32 granularity for a fine threshold sweep. The probe is checkpointed
   and resumable.
2. Correctness per sample is the word-bounded normalized gold-alias match
   (Cheng-validated scorer). P_correct = (correct samples) / 32.
3. Split: **known** = greedy-correct AND P_correct >= 0.5; **unknown** =
   P_correct == 0; **discard** the ambiguous middle for a clean contrast (the
   discard band is retained on disk for the sensitivity analysis).

**Label-noise sensitivity analysis (pre-registered secondary result).** Paper 1
measured that 43-51% of Cheng's "unknown"-labeled questions were in fact
answerable, because their 10-sample probe was too coarse. We recompute the
known/unknown split across a threshold grid on P_correct (unknown-cutoff in
{0.0, <=1/32, <=2/32, <=0.1}, known-cutoff in {0.5, 0.7, 0.9}) and report, per
cell, the fraction of "unknown"-labeled questions the greedy decode actually
answered correctly, and the resulting split sizes. The point estimate at the
pre-registered band is the headline; the grid is the robustness check and may
subsample questions if the full cross-product is needlessly expensive.

**Targets and the three training files (same frozen question set, same seed).**

- **Shared budget definition (pre-registered):** the data budget is the set of
  distinct source QUESTIONS. All arms are built from the same frozen known set K
  and unknown set U. The per-method example-count expansion (SFT 1 row/question,
  DPO 1 pair/question, KTO multiple labeled rows/question) is an expected,
  documented consequence of each format, not a confound.
- **SFT set:** all K and U as positives. known target = gold short answer in a
  fixed template; unknown target = a style-varied abstention phrasing.
- **DPO set:** one chosen/rejected pair per question. known: chosen = gold
  answer, rejected = abstention. unknown: chosen = abstention, rejected = the
  model's own hallucinated probe sample.
- **KTO set (congruence mapping, primary):** desirable = {known+gold answer,
  unknown+abstention}; undesirable = {unknown+model's own hallucinated sample,
  known+abstention (the anti-over-refusal signal)}. Interleaved true/false per
  `synaptic-tuner/.skills/fine-tuning/reference/dataset-formats.md`.
- **KTO set (correctness-safe mapping, ablation):** the rebalanced variant per
  `rewardcal-kto-recipe.md` design tension, handled via desirable_weight /
  undesirable_weight. Emitted as a separate file behind a config flag.
- **Abstention template:** a style-varied bank (anti-overfitting) where every
  phrasing contains one of the eval refusal markers so refusal detection stays
  reliable. The builder validates this invariant.

Eval sets are never touched during training; OOD sets share no questions with
training, and the builder asserts the trained question set does not appear in
any OOD set.

### 3.4 Training (Synaptic Tuner)

- Trainers: `Trainers/sft/train_sft.py` (exists), `Trainers/kto/train_kto.py`
  (exists; a Qwen3 preset is added since it currently hardcodes Qwen2.5), and a
  new `Trainers/dpo/train_dpo.py` (built in the submodule, mirroring the KTO
  trainer, using TRL DPOTrainer). The `dpo` method is registered across all
  tuner enumeration sites.
- Identical LoRA budget across arms (confound control): r=32, alpha=64,
  dropout=0.05 at 4B; r=64, alpha=128 at 8B; identical target_modules; pinned
  explicitly per arm, not via tier presets.
- Early stopping on dev loss (Gekhman: prolonged training on unknowns drives
  hallucination; the dynamics are logged as a secondary analysis). The dev split
  is the same held-out set across arms.
- Execution lanes (compute is not a binding constraint): the RTX 3090 is the
  development, pilot, and smoke-run lane for fast local iteration; HF Jobs is the
  parallel execution lane for the run matrix, since small-model LoRA runs are
  cheap and the 19-run 4B matrix plus the 8B confirm execute in parallel across
  HF Jobs rather than serially on one local GPU. Both paths use the existing
  tuner (`train_*.py` direct or `tuner.py local-run` locally; `tuner.py
  cloud-pipeline` on HF Jobs). HF Jobs checks out the pinned submodule SHA, so
  the DPO trainer must be committed and pushed in the submodule before any cloud
  run.
- Bridge arm: Idk-SFT + Idk-DPO on Llama-2-7b-chat (HF-gated, no tuner preset)
  via a `--model-name` override and accepted Meta license; consumes Cheng's IDK
  training data (fetched from OpenMOSS, license-gated, user sign-off required).

### 3.5 Metrics (joint reporting, fixing the field's incommensurability)

Scorers are research-repo native (the tuner's eval harness does not pre-build
them), ported from the Cheng-validated `reanalyze_idk_outputs.py` so bridge-arm
numbers use the exact scorer that already reproduces 42.71% / 23.27%.

1. Truthful rate + 4-quadrant matrix (Cheng). Primary.
2. Refusal recall on unknowns + over-refusal on knowns (the decomposition the
   field omits; the bridge-arm comparison targets).
3. AP over confidence-ranked answers (R-Tuning comparability).
4. Token-level ECE on MMLU multiple-choice (15 bins): does the preference-class
   method damage calibration the way RLHF/DPO do, measured for the first time
   across SFT, DPO, and KTO on the same run.
5. TruthfulQA MC1/MC2 + over-refusal on its informativeness axis.
6. Accuracy retention on answered questions (capability tax), vs the base arm.

OOD transfer is reported on KUQ, CoCoNot, AbstentionBench, MMLU, SelfAware, and
PopQA (all local).

Analysis is the two-layer uncertainty treatment in §3.6. All scorers
deterministic; raw generations and metric CSVs committed.

### 3.6 Statistics, power, and compute

**Two-layer uncertainty treatment.** Phase 1 reports two distinct sources of
uncertainty, because conflating them is part of the field's incommensurability
problem:

1. **Within-run, eval-question uncertainty:** paired bootstrap CIs over eval
   questions for every metric, resampling questions with replacement and
   recomputing. Paired because all arms are scored on identical question sets.
   This captures sampling noise over the evaluation set for a single trained
   model.
2. **Across-seed, training-stochasticity uncertainty:** each headline arm is
   trained at 3 seeds (4B; also 3 at 8B pending the veto in §3.1), and every
   headline metric is reported as the mean and CI ACROSS those seeds. This
   captures the run-to-run variance of the training procedure itself, which is
   the error bar the field almost never reports and which paper 1 documents as
   missing.
3. **Between-arm significance:** McNemar tests on the binary outcomes
   (refused-or-not, correct-or-not) between arms, computed on matched seeds (seed
   i of arm A vs seed i of arm B on the same questions) so the test is not
   confounded by cross-seed pairing.

The sensitivity panel (§3.1a) is reported as a robustness figure (the headline
metric per panel cell, 1 seed each) and explicitly NOT with seed-level CIs,
because the panel's job is to show direction-of-effect stability, not to estimate
a precise operating point. Headline significance claims never come from the
panel.

**Power.** The in-domain test set (Cheng's 11,313 questions) gives power > 0.95
to detect a 3 percentage-point truthful-rate difference at alpha = .05
(two-proportion, n approximately 11k). With the move to 3 seeds at 4B, the
across-seed CI (layer 2) is now estimated from 3 points per arm rather than 2,
tightening the training-stochasticity error bar that is the binding constraint.
If the validation-remainder fallback (§3.3) is used for the probe/train pool, the
in-domain TEST set is unaffected (it remains Cheng's 11,313), so test power is
unchanged; only the training-set size shrinks, which is recorded as a caveat.

**Compute (order-of-magnitude, stated assumptions).** Assumptions: each 4B LoRA
run is a small-rank (r=32) fine-tune on roughly 10k to 15k examples with early
stopping on dev loss, which on a single RTX 3090 is on the order of 1 to 3 GPU
hours per run (to be confirmed against the first pilot run; this is an
order-of-magnitude planning figure, not a measured number). The 19-run 4B matrix
is therefore on the order of 20 to 60 GPU-hours of WORK. Crucially, this is not
serial wall-clock: the matrix executes in PARALLEL across HF Jobs, so the
wall-clock-to-results is governed by HF Jobs concurrency, not by the sum. On the
local 3090 the same matrix would be serial (tens of hours), which is why the 3090
is scoped as the dev / smoke lane and HF Jobs as the matrix execution lane
(§3.4). The 8B confirm runs (3 seeds x 3 arms = 9 runs at default config) are
each larger but still cheap relative to the parallel budget; they add no
sensitivity panel. The probe (§3.3) is a separate one-time cost (roughly
train-split-size x 33 generations on the 4B model, batched on vLLM, checkpointed
and resumable). The headline conclusion: at the user-confirmed cheap-and-parallel
compute regime, the binding constraint is HF Jobs concurrency and orchestration,
not GPU-hours, so the run matrix is affordable and the 9-run headline (the
error-bar story) is non-negotiable scope.

### 3.7 Bridge arm (pipeline validation)

Before the novel arms are trusted, replicate Idk-SFT + Idk-DPO on
Llama-2-7b-chat and confirm the pipeline reproduces Cheng's published over-refusal
(42.71% SFT, 23.27% DPO, n=11,313). A bridge mismatch indicts the training or
eval pipeline rather than the metric, because the scorer is the one already
validated against Cheng's released outputs. The bridge arm uses Cheng's IDK
training data and the gated Llama-2-7b-chat model (both recorded as CODE
prerequisites with user sign-off, in `docs/architecture/phase1-pipeline.md` §9).

## 4. Deliverable

arXiv paper #2: introduction motivated by the meta-analysis findings; methods as
above; the three-way calibration-tension result (H3) as a headline, and the
loss-aversion dose-response (H4), now operationalized by the beta sensitivity
panel, as a headline if it pans out. Seed-level confidence intervals on every
headline metric and the pre-registered sensitivity panel are themselves part of
the contribution (the error-bar and robustness rigor paper 1 documents the field
lacking). All data-construction and analysis scripts in this repo; datasets,
adapters, and per-model labels released to HF Hub.

## 5. Blockers / needs (before any training run)

- **User sign-off on this v0.3 pre-registration**, including the pinned probe
  sample count (32), the hypothesis set, the run matrix (§3.1) with its pinned
  default LR / beta and sensitivity-panel brackets (§3.1a), and a veto decision
  on the lead-proposed 8B 3-seed bump (§3.1).
- TriviaQA rc.nocontext **train** split fetch (CODE prerequisite; one spec row
  in `datasets/scripts/fetch_datasets.py`).
- Cheng IDK **training** data fetch from OpenMOSS (license-gated; user sign-off)
  for the bridge arm.
- Llama-2-7b-chat gated access (Meta license acceptance + HF_TOKEN) for the
  bridge arm.
- DPO trainer built and pushed in the `synaptic-tuner/` submodule, submodule
  pointer bumped, before the 8B cloud arm runs.
- Local inference backend for the knowledge probe (vLLM on the RTX 3090).

## 6. Reference

Implementation blueprint, component contracts, directory layout, and the
CODE-phase work breakdown: `docs/architecture/phase1-pipeline.md`. KTO mapping
recipe and design tensions: `experiment/protocol/rewardcal-kto-recipe.md`. Staged
program: `experiment/protocol/research-trajectory.md`.
