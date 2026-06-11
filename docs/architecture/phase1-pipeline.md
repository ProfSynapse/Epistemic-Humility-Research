# Phase 1 Pipeline Architecture — paper 2 (SFT vs DPO vs KTO abstention)

**Author:** architect (PACT Architect, team pact-6d29f2e2)
**Date:** 2026-06-10 · **Worktree:** `.worktrees/phase1-pipeline`
**Status:** ARCHITECT deliverable for CODE phase. Companion pre-registration:
`experiment/protocol/PROTOCOL.md` (v0.2 DRAFT). Upstream PREPARE docs:
`docs/preparation/model-landscape.md`, `docs/preparation/infra-and-data.md`.

> **Scope note.** This document is the implementation blueprint. It specifies
> components, interface contracts, data schemas, directory layout, the new DPO
> trainer in the `synaptic-tuner/` submodule, and a file-level CODE-phase work
> breakdown with S2 ownership boundaries. It does NOT itself write code. All
> user decisions (model pin Qwen3, bridge arm in, build DPO, Phase-2 rideshare,
> KTO mapping congruence+correctness-safe, thinking-axis registration) are
> resolved upstream and are treated as fixed inputs here.

---

## 1. Executive summary

Phase 1 trains three abstention methods (SFT, DPO, KTO) plus a `base` control
on model-specific "I don't know" (IDK) data, on a pinned Qwen3 family
(Qwen3-4B-Instruct pilot / Qwen3-8B-Instruct confirm, thinking mode OFF), and
measures the full recall / over-refusal / truthful-rate / calibration
decomposition after each run, in-domain and OOD. A Llama-2-7b-chat bridge arm
(Idk-SFT + Idk-DPO) validates the pipeline against Cheng et al.'s published
numbers (42.71% / 23.27% over-refusal, n=11,313) before the novel arms are
trusted.

The pipeline is four components connected by file-on-disk contracts:

```
                         experiment/phase1/
  +-------------------+   probe/        +-------------------+
  | (A) Knowledge     |---------------->| (B) Dataset       |
  |     Probe         | per-question    |     Builders      |
  | Qwen3-4B base     | P_correct +     | known/unknown ->  |
  | vLLM, N samples   | sampled answers | SFT / DPO / KTO   |
  +-------------------+                 +---------+---------+
         ^                                        | JSONL (3 formats)
         | TriviaQA train split                   v
         | (disjoint from Cheng test)   +-------------------+
                                        | (C) Trainers      |
  +-------------------+   adapters      | SFT (exists)      |
  | (D) Eval Harness  |<----------------| KTO (exists,+pin) |
  | truthful/recall/  |                 | DPO (NEW)         |
  | over-ref/ECE/OOD  |                 | synaptic-tuner/   |
  | bootstrap+McNemar |                 +-------------------+
  +-------------------+
```

Two repos are in play. The **research repo** (this worktree) owns the probe,
the dataset builders, the eval harness, and the protocol. The **submodule**
(`synaptic-tuner/`, a separate git repo) owns the trainers; the only change
there is adding a DPO trainer and Qwen3 presets. The contract between them is
the on-disk JSONL training files plus the tuner CLI.

Design spine (the reasoning_chain in one line): the model pin (Qwen3, text-only,
Apache, thinking-off) was chosen to remove confounds, so every component pins
`enable_thinking=False`; the three-way needs a DPO path that does not exist, so
we mirror the existing TRL KTO trainer rather than invent a new stack; the
probe pool overlaps the Cheng test set, so we move probing/training to a
disjoint TriviaQA train split and pre-register a leakage-guard; identical data
and LoRA budget across arms is the core confound control, so "budget" is
defined as distinct source questions and enforced at build time.

---

## 2. System context (C4 L1) and external dependencies

```
   TriviaQA rc.nocontext        Cheng outputs +        OOD eval sets
   train split (FETCH)          gold (on disk)         (all on disk)
        |                            |                      |
        v                            v                      v
  +--------------------------------------------------------------+
  |              Phase 1 Pipeline (this design)                  |
  |   probe -> builders -> trainers(submodule) -> eval harness   |
  +--------------------------------------------------------------+
        |                            |                      |
        v                            v                      v
   HF Hub (adapters,          PROTOCOL.md v0.2        paper 2 figures +
   per-model labels,          (pre-registration,      committed analysis
   outputs released)          user sign-off gate)     CSVs
```

External dependencies and their status (from PREPARE):

| Dependency | Status | Action |
|---|---|---|
| Qwen3-4B/8B-Instruct (HF, Apache, ungated) | available | pin in configs |
| Llama-2-7b-chat (HF, gated) | gated, no tuner preset | bridge arm: `--model-name` override + license acceptance (gap #5) |
| TriviaQA rc.nocontext **train** split | NOT on disk | CODE prerequisite fetch (gaps #2, #3) |
| Cheng test gold + outputs | on disk | held-out in-domain test |
| OOD sets (KUQ, CoCoNot, AbstentionBench, MMLU, TruthfulQA, PopQA, SelfAware) | on disk | eval inputs |
| Cheng IDK **training** data (OpenMOSS) | NOT on disk | bridge-arm CODE prerequisite, license-gated (gap #4) |
| synaptic-tuner SFT, KTO trainers | exist | reuse; add Qwen3 preset to KTO |
| synaptic-tuner DPO trainer | ABSENT | BUILD (gap #1) |
| vLLM (probe + eval backend) | tuner default runtime | reuse |

---

## 3. Component A — Knowledge probe pipeline

### 3.1 Responsibility

One job: for every question in the probe/train pool, estimate this model's
P_correct under its own generation, and capture the model's own wrong answers
(needed downstream as KTO/DPO negatives). Single responsibility: produce a
per-question labeling artifact. It does not build training files (that is B).

### 3.2 Inputs and the disjoint-split decision (resolves gaps #2, #3)

The probe pool is **TriviaQA rc.nocontext train split**, NOT the on-disk
`validation.jsonl`. Rationale, decided with team-lead:

- The on-disk `validation.jsonl` (17,944 rows) is the source of Cheng's 11,313
  test questions. Probing/training on it would leak the test set into training.
- research-trajectory.md always intended a "train subset (~20k)" probe source;
  the validation pool was never the intended probe input. So using the train
  split is trajectory-faithful, not a deviation.
- **Decision (confirmed):** keep Cheng's 11,313 as the bridge-comparable
  in-domain held-out **test** set; probe and train on the disjoint train split.

**Leakage guard (pre-registered, builder-enforced).** A hard assertion that the
probe/train question set and the Cheng test question set are disjoint:
`normalized(probe_questions) ∩ normalized(cheng_test_questions) == ∅`. Use the
same normalization as the eval scorer (`re.sub(r"\s+", " ", s.strip().lower())`,
matching `cheng_test_gold.jsonl` keys and `reanalyze_idk_outputs.py:norm_question`).
The builder (Component B) MUST run this assertion and abort on any non-empty
intersection. The probe step also writes the normalized question set so the
guard is checkable independently.

**Contingency (documented fallback, gap #2).** If the train-split fetch is
infeasible at CODE time, fall back to carving the ~6,631 non-Cheng remainder of
the on-disk validation pool (17,944 − 11,313) as the probe/train pool, and
record the reduced n as a power caveat in PROTOCOL.md §power. The leakage guard
makes this fallback safe by construction.

**CODE prerequisite (record, do not execute this phase).** Add one spec row to
`datasets/scripts/fetch_datasets.py:SPECS`:
`("mandarjoshi/trivia_qa", "rc.nocontext", "train", "triviaqa-rc-nocontext", "train.jsonl")`,
then `python datasets/scripts/fetch_datasets.py --only triviaqa-rc-nocontext`,
and append a provenance stanza to `datasets/triviaqa-rc-nocontext/dataset.md`.
The fetch is idempotent and split-restricted, matching the script's existing
discipline.

### 3.3 Sampling plan (resolves "higher than Cheng's 10")

- **Pinned sample count: N = 32 stochastic samples at T = 1.0, top_p = 0.9,**
  **plus 1 greedy decode.** Rationale for 32: it is higher than Cheng's 10 (the
  trajectory's mandatory improvement), gives P_correct on a 1/32 ≈ 0.03
  granularity so the known/unknown threshold band can be swept finely in the
  label-noise sensitivity analysis, and is a power-of-two that batches cleanly
  on vLLM. This single number is pre-registered in PROTOCOL.md v0.2 and gets
  user eyes at the sign-off gate; it is cheap to correct there.
- **Generation config (pinned):** `enable_thinking=False` on the Qwen3 chat
  template (no `<think>` traces in probe outputs), `max_new_tokens` sized to the
  TriviaQA answer length (short-answer; 64 is ample), stop on the chat turn
  boundary. The greedy decode is the "Ik threshold 1.0" anchor used by Cheng.
- **Prompt:** the bare TriviaQA question in the Qwen3 instruct chat template,
  no context (rc.nocontext), no few-shot. One fixed system prompt, recorded in
  the protocol and emitted into the probe manifest for provenance.

### 3.4 P_correct and correctness scoring

Correctness reuses the Cheng-validated scorer mechanics (port from
`meta-analysis/analysis/reanalyze_idk_outputs.py`, read-only source):
word-bounded normalized gold-alias match. For each sample generation `g` and
the question's `normalized_aliases`, `is_correct(g) = any(" {alias} " in
" {normalize(g)} ")`. `P_correct = (# correct samples) / N`. The greedy decode's
correctness is recorded separately as `greedy_correct` (boolean).

Gold aliases for the **train** split are not yet on disk (only Cheng test gold
is). The probe step builds train-split aliases the same way `build_cheng_gold`
does: the TriviaQA train rows already carry `answer.normalized_aliases`, so the
probe reads them directly from the fetched `train.jsonl` (no separate gold
build needed; train rows are self-describing, unlike the Cheng re-index case).

### 3.5 Known / unknown / discard bands (pre-registered)

Mirrors v0.1 with the finer granularity N=32 enables:

- **known:** `greedy_correct AND P_correct >= 0.5`
- **unknown:** `P_correct == 0` (model never gets it right in 32 tries)
- **discard (ambiguous middle):** everything else, dropped from the primary
  split for a clean contrast. The discard band is retained on disk (flagged) so
  the sensitivity analysis can re-include it.

### 3.6 Label-noise sensitivity analysis (resolves the 43-51% finding)

Paper 1 measured that 43-51% of Cheng's "unknown"-labeled questions were in
fact answerable, because their 10-sample probe was too coarse. Our analysis,
pre-registered as a secondary result:

- Recompute known/unknown splits across a **threshold grid** on P_correct:
  unknown-cutoff ∈ {0.0, ≤1/32, ≤2/32, ≤0.1} and known-cutoff ∈ {0.5, 0.7, 0.9}.
- For each grid cell, report the fraction of "unknown"-labeled questions that
  the greedy decode actually answered correctly (the direct analogue of the
  43-51% number), and the resulting split sizes.
- The grid may subsample questions if the full cross-product is needlessly
  expensive (team-lead approved subsampling). The point estimate at the
  pre-registered band (§3.5) is the headline; the grid is the robustness check.

### 3.7 Inference backend

**vLLM, local on the RTX 3090** for the 4B pilot probe. Rationale: it is the
tuner's default eval runtime (`evaluation.runtime: vllm`, `image_profile:
fast_vllm`), supports batched N-sample generation efficiently, and keeps the
probe on the same engine as the eval harness for consistency. The 4B model fits
the 3090 comfortably for inference. The probe is **checkpointed and resumable**
(team-lead requirement): write per-question results to a JSONL append log keyed
by `question_id`; on restart, skip question_ids already present. Linear cost is
≈ (train-split size) × 33 generations on a 4B model; resumability makes the run
interruptible without losing work.

### 3.8 Output artifact (interface contract A -> B)

`experiment/phase1/probe/<model_tag>/probe_results.jsonl`, one object per
question:

```json
{
  "question_id": "tqa_train_000123",
  "question": "Who wrote Paradise Lost?",
  "question_norm": "who wrote paradise lost",
  "normalized_aliases": ["john milton", "milton"],
  "n_samples": 32,
  "greedy_answer": "John Milton wrote Paradise Lost.",
  "greedy_correct": true,
  "p_correct": 0.97,
  "sampled_answers": ["John Milton.", "Milton", "...", "Dante (WRONG)"],
  "sampled_correct": [true, true, "...", false],
  "label": "known",
  "model_tag": "qwen3-4b-instruct",
  "probe_config_sha": "<hash of the pinned sampling config>"
}
```

`sampled_answers` retains the actual generations because the **wrong** ones are
the KTO/DPO negatives downstream (a model-unknown question with a confidently
wrong sample is exactly the hallucination the undesirable label targets). A
sidecar `probe_manifest.json` records the model, sampling config, prompt
template, split source, fetch SHA, and the disjointness check result.

---

## 4. Component B — Dataset builders

### 4.1 Responsibility

Convert one `probe_results.jsonl` into the three method-native training files
(SFT, DPO, KTO) plus a held-out dev file, under one identical question budget,
config-driven. Single responsibility: labeling-to-training-format transform.
It owns the leakage guard, the budget equalization, and the abstention-template
generation.

### 4.2 The shared-budget definition (resolves A4, pre-registered proactively)

Method-native formats expand the same questions into different example counts
(SFT positives-only vs DPO pairs vs KTO interleaved binary). To keep the data
budget a genuine confound control rather than an accident of format:

> **Budget = the set of distinct source QUESTIONS.** All three arms are built
> from the *same* frozen question set (same known set K, same unknown set U,
> same seed). The per-method example-count expansion (SFT emits 1 row/question,
> DPO emits 1 pair/question, KTO emits multiple labeled rows/question) is an
> expected, documented consequence of each method's format, NOT a confound. The
> builder pins and logs the K/U question IDs once and derives all three files
> from that frozen set.

This definition is registered in PROTOCOL.md §design so it is fixed before
training, not negotiated after a result.

### 4.3 Abstention template (style-varied, anti-overfitting)

The unknown-target abstention string must not be a single fixed template (Cheng
over-refused partly from template overfitting). Generate a **style-varied bank**
of abstention phrasings (SynthChat-style paraphrase, or a checked-in static
bank of N paraphrases of "I don't know the answer to that"), sampled per
example with a fixed seed. CRITICAL CONSTRAINT: every paraphrase MUST contain
one of the eval harness refusal markers (§6.3) so that refusal detection at eval
time is reliable. The builder validates this invariant: each generated
abstention string is checked against the refusal-marker set and rejected if it
matches none. The marker-bearing phrasings are the bank's backbone; stylistic
variation rides on top.

### 4.4 SFT builder (positives only)

R-Tuning / Cheng style: every K and U question becomes one positive example.

- known -> assistant target = gold short answer in a fixed response template.
- unknown -> assistant target = a sampled abstention phrasing (§4.3).

Output schema (per `dataset-formats.md` SFT, conversations form, no tool calls):

```jsonl
{"conversations":[{"role":"system","content":"<fixed system prompt>"},{"role":"user","content":"<question>"},{"role":"assistant","content":"<gold answer | abstention>"}]}
```

### 4.5 DPO builder (preference pairs)

One chosen/rejected pair per question (chosen = the desirable completion,
rejected = the undesirable one):

- known -> chosen = gold answer; rejected = an abstention phrasing
  (the over-refusal we train against).
- unknown -> chosen = abstention; rejected = the model's own hallucinated
  sample (a wrong `sampled_answers` entry; if none wrong, fall back to a
  plausible distractor or drop the question, logged).

On-disk DPO schema (chosen/rejected as message lists, the TRL DPO convention
the new trainer's data_loader consumes; see §5.4):

```jsonl
{"prompt":[{"role":"system","content":"..."},{"role":"user","content":"<question>"}],"chosen":[{"role":"assistant","content":"<desirable>"}],"rejected":[{"role":"assistant","content":"<undesirable>"}]}
```

### 4.6 KTO builder (interleaved unpaired binary)

The same questions, zero extra labeling, mapped to binary desirable/undesirable
per `rewardcal-kto-recipe.md` and v0.1 §3.2. **Congruence mapping (primary):**

| Source | Completion | KTO label |
|---|---|---|
| known | gold answer | true (desirable) |
| unknown | abstention | true (desirable) |
| unknown | model's own hallucinated sample | false (undesirable) |
| known | abstention | false (undesirable, anti-over-refusal signal) |

**Correctness-safe mapping (ablation, Phase-2 rideshare seed).** Per the recipe
§4 design tension: dropping the `known+gold` desirable that could reward a
verbatim wrong answer is not the concern here (our known answers are
gold-verified), so the correctness-safe variant for THIS dataset instead drops
the riskiest desirable and rebalances via `desirable_weight`/`undesirable_weight`.
The builder emits BOTH mappings as separate files behind a config flag; the
primary is the congruence mapping. (The CRM-derived mapping table in the recipe
is the precedent; our IDK mapping is the analogue documented inline in the
builder config.)

On-disk KTO schema (per `dataset-formats.md`, conversations + boolean label,
**interleaved T/F/T/F**):

```jsonl
{"conversations":[{"role":"system","content":"..."},{"role":"user","content":"<question>"},{"role":"assistant","content":"<good>"}],"label":true}
{"conversations":[{"role":"user","content":"<question>"},{"role":"assistant","content":"<bad>"}],"label":false}
```

Interleaving: the tuner's `interleave_dataset` (`Trainers/kto/src/data_loader.py`)
already enforces T/F/T/F and balances by truncating the majority class. The
builder SHOULD pre-interleave on write (fixed seed) so the on-disk file is
training-ready and human-inspectable, AND rely on the trainer's interleave as a
safety net. With the congruence mapping the set is ~50/50 by construction; with
correctness-safe it is imbalanced and uses weights, matching the recipe.

### 4.7 Dev split for early stopping (Gekhman)

The builder carves a held-out dev split (fixed fraction, fixed seed) from the
SAME question set, format-matched per arm, for dev-loss early stopping. The dev
questions are excluded from the train files of all arms (same held-out set
across arms, so early-stopping is comparable). Dev is disjoint from the Cheng
test set by construction (it is drawn from the train split).

### 4.8 Output artifact (interface contract B -> C)

```
experiment/phase1/data/<model_tag>/
  questions_frozen.json        # K/U question IDs + seed (the budget anchor)
  sft_train.jsonl  sft_dev.jsonl
  dpo_train.jsonl  dpo_dev.jsonl
  kto_congruence_train.jsonl  kto_congruence_dev.jsonl
  kto_correctness_safe_train.jsonl  kto_correctness_safe_dev.jsonl
  build_manifest.json          # mapping config, budget, leakage-guard result, counts per arm
```

`build_manifest.json` records the leakage-guard pass, the frozen question count
(the budget), and per-arm row counts (the documented expansion). This is the
provenance artifact that satisfies HANDOFF §5 for the training data.

---

## 5. Component C — Trainers (synaptic-tuner submodule)

### 5.1 What exists vs what is built

| Arm | Trainer | Status | Change needed |
|---|---|---|---|
| base | none (eval the untrained model) | n/a | none |
| SFT | `Trainers/sft/train_sft.py` | exists, `--method sft` | add Qwen3 model presets (family branch already handles `qwen`) |
| KTO | `Trainers/kto/train_kto.py` | exists, `--method kto` | **add Qwen3 preset** (hardcodes Qwen2.5) |
| DPO | none | **ABSENT** | **BUILD `Trainers/dpo/`** + register method |

### 5.2 Identical LoRA budget across arms (confound control)

All arms pin the SAME LoRA config explicitly (do not rely on `--tier`, per
PREPARE A.3). Pinned from the KTO config precedent:
`r=32, lora_alpha=64, lora_dropout=0.05` at 4B pilot;
`r=64, lora_alpha=128` at 8B confirm; identical `target_modules`
(q/k/v/o/gate/up/down). The run matrix (seed counts, sensitivity panel) is
pre-registered in PROTOCOL.md §3.1 / §3.1a (3 headline seeds per arm at 4B, a
19-run 4B matrix including the LR/beta panel, and 3 seeds at 8B pending user
veto); LoRA budget is held identical across arms and across panel cells, varying
only the named panel hyperparameter. These live in the per-arm recipe YAMLs
(§5.6) so they are visible and identical across SFT/DPO/KTO.

**The recipe `lora:` block is the SSOT for the budget -- not the trainer's sibling
`config.yaml`.** The DPO/KTO trainers natively read LoRA from `config.lora.*`
(no `--lora-*` argparse originally), so the local lane MUST forward the recipe's
LoRA scalars to the trainer via flag parity (`--lora-*` added to `train_dpo.py` /
`train_kto.py`, §9.2(b)); otherwise the trainer silently falls back to its sibling
`config.yaml` default. This is load-bearing precisely because the budgets DIVERGE
from that default at 8B (recipe r=64/alpha=128 vs config.yaml r=32/alpha=64); a
silent fallback would mistrain every 8B DPO/KTO arm at the wrong budget while the
recipe and run record both claim the pinned one. The 4B recipe happening to match
the config.yaml default is a coincidence that would mask the bug.

### 5.3 Qwen3 presets (resolves gap, both KTO and DPO)

The KTO `model_map` (`train_kto.py` ~L420) hardcodes Qwen2.5. Add:

```python
'qwen3_4b': ('3b', 'unsloth/Qwen3-4B-bnb-4bit'),
'qwen3_8b': ('7b', 'unsloth/Qwen3-8B-bnb-4bit'),
```

with matching `--qwen3-4b` / `--qwen3-8b` argparse flags. (CODE verifies the
exact `unsloth/...` repo names against live HF before pinning; the
model-landscape doc confirms Qwen3-4B/8B exist, Apache, ungated.) The SFT
trainer needs no family-branch change (`"qwen"` arm exists, §745 chooses
`chatml`), only a config `model_name` override per recipe. The new DPO trainer
gets the same `qwen3_4b`/`qwen3_8b` entries in its own `model_map`.

**enable_thinking=False.** Qwen3 supports a thinking toggle. The pin is OFF for
all training and eval. Where the chat template is applied (SFT/KTO use Unsloth
`get_chat_template` -> `chatml` for `qwen`), CODE must ensure no `<think>`
scaffolding is injected; for Qwen3 specifically, verify the tokenizer's chat
template default and pass `enable_thinking=False` if the template honors it.
This is a CODE verification item flagged in §9, not a guess to hardcode.

### 5.4 DPO trainer design (NEW — `Trainers/dpo/`, mirrors `Trainers/kto/`)

Mirror the KTO trainer's structure exactly so it inherits the tuner's
callbacks, cloud-artifact sync, and model-loading. KTO already uses TRL
(`from trl import KTOConfig, KTOTrainer`); DPO swaps to `DPOConfig, DPOTrainer`.

```
Trainers/dpo/
  train_dpo.py            # mirror train_kto.py: argparse, env bootstrap, orchestration
  configs/
    config.yaml           # mirror kto config.yaml; DPOTrainingConfig fields (see below)
    config_loader.py      # mirror kto config_loader.py; DPOTrainingConfig dataclass
  src/
    data_loader.py        # NEW logic: load prompt/chosen/rejected (NOT interleaved binary)
    model_loader.py       # REUSE kto/src/model_loader.py (LoRA + create_reference_model)
    training_callbacks.py # REUSE kto/src/training_callbacks.py (or shared/)
  README.md  requirements.txt  setup.sh   # mirror kto/
```

Key differences from KTO, by file:

- **`train_dpo.py`:** `from trl import DPOConfig, DPOTrainer`. DPO needs a
  reference model exactly as KTO does (`create_reference_model` already exists
  in `kto/src/model_loader.py` and is reusable). No custom `KTOSTrainer`
  sign-correction analogue is needed (that is KTO-specific); use stock
  `DPOTrainer`.
- **`src/data_loader.py`:** consumes the DPO on-disk schema (§4.5). Produces a
  HF Dataset with columns `prompt`, `chosen`, `rejected` (TRL DPO convention),
  rather than KTO's `prompt`/`completion`/`label`. No interleaving (DPO has no
  homogeneous-batch constraint). Reuse KTO's chat-format extraction helper
  shape but map to chosen/rejected. Add a `validate_dpo_dataset` mirroring
  `validate_kto_dataset` (required columns present, no empty chosen/rejected).
- **`configs/config_loader.py`:** replace `KTOTrainingConfig` with
  `DPOTrainingConfig`. Drop `desirable_weight`/`undesirable_weight`/`use_kto_s`;
  keep `beta` (DPO has its own beta), add `loss_type` (default `"sigmoid"` =
  vanilla DPO). All other fields (LoRA, optim, lr, scheduler, early-stop eval
  fields) carry over unchanged.
- **`configs/config.yaml`:** mirror KTO's with DPO training block; defaults are
  overridden per recipe anyway.

### 5.5 Registering DPO as a method (sibling-pin enumeration — IMPORTANT)

`"dpo"` is NOT a single-line addition. The method set is enumerated across
roughly ten sibling sites spanning ~16 files (verified by grep during CODE
pre-work; this table was corrected from an earlier 4-site estimate). ALL must be
updated in the same commit or DPO partially registers and fails at a later layer.

**Central site (the SSOT, update FIRST):**
`shared/utilities/paths.py:11` defines `TRAINING_METHODS = ("sft", "kto", "grpo")`,
from which it AUTO-DERIVES `CANONICAL_TRAINER_DIRS`, `LEGACY_TRAINER_DIRS`,
`CANONICAL_OUTPUT_DIRS`, `LEGACY_OUTPUT_DIRS`, and the `get_trainer_root()`
dispatch (line 88). Adding `"dpo"` here propagates the trainer-dir and
output-dir mapping automatically (so `dpo -> Trainers/dpo` and `dpo_output/`
come for free), which is why it is the effective 5th-and-central registration
site, not just one of the leaf enumerations. Verify the derived
`CANONICAL_TRAINER_DIRS["dpo"]` resolves to the new `Trainers/dpo/` dir.

**Leaf / independent enumeration sites (sweep ALL, same commit):**

| Site | What it is | Change |
|---|---|---|
| `shared/utilities/paths.py:11` | `TRAINING_METHODS` SSOT (auto-derives dirs + dispatch) | add `"dpo"` — do this first |
| `tuner/cli/parser.py:222` | `--method` argparse `choices` | add `"dpo"` |
| `tuner/backends/training/cloud/base_cloud.py:110` | `SUPPORTED_METHODS` tuple | add `"dpo"` |
| `tuner/backends/training/cloud/hf_jobs_backend.py:125` | returns method list | add `"dpo"` |
| `tuner/backends/training/rtx_backend.py:106` | returns method list | add `"dpo"` |
| `tuner/backends/evaluation/{mlc,unsloth,llamacpp}_backend.py` | eval-backend method handling | sweep + add if enumerated |
| `tuner/discovery/{training_runs,base_models}.py` | run/model discovery by method | sweep + add if enumerated |
| `tuner/cloud/hardware_planner.py` | per-method hardware planning | sweep + add if enumerated |
| `tuner/handlers/{train,merge,doctor}_handler.py` | method dispatch in handlers | sweep + add if enumerated |
| `shared/experiment_tracking/{experiment_spec,schema}.py` | experiment-spec method field | sweep + add if enumerated |
| parser help strings ("SFT, KTO, GRPO") | cosmetic | update for accuracy |

CODE MUST grep `TRAINING_METHODS`, `SUPPORTED_METHODS`, and the literal
`"sft", "kto", "grpo"` / `'sft', 'kto', 'grpo'` triples across `tuner/`,
`Trainers/`, and `shared/` before finishing, and confirm no site is missed (the
discipline that caught the under-count). The grep hit-set is the full pin
universe; triage each hit (does it gate DPO, or is it derived from `paths.py`?).
Because `paths.py` auto-derives the dir/output/dispatch maps, several leaf sites
need NO change once the SSOT is updated; the sweep confirms which are derived vs
independent.

For the **pilot (local 3B)**, the DPO arm can run via the direct trainer
(`cd Trainers/dpo && python train_dpo.py --qwen3-4b --local-file <dpo.jsonl>`)
independent of cloud-method registration, so dataset+trainer work can land and
be smoke-tested before the full cloud wiring is complete. Cloud registration is
required for the **8B confirm** arm on HF Jobs.

### 5.6 Training config conventions (recipes)

Per-arm recipe YAMLs under the submodule's `Trainers/recipes/` (the established
config-driven home), one per (method × size), e.g.:

```
Trainers/recipes/eh_phase1_qwen3_4b_sft.yaml
Trainers/recipes/eh_phase1_qwen3_4b_dpo.yaml
Trainers/recipes/eh_phase1_qwen3_4b_kto_congruence.yaml
Trainers/recipes/eh_phase1_qwen3_4b_kto_correctness_safe.yaml
Trainers/recipes/eh_phase1_qwen3_8b_{sft,dpo,kto_congruence}.yaml
Trainers/recipes/eh_bridge_llama2_7b_chat_{sft,dpo}.yaml
```

Each pins: `model_name`, identical LoRA budget (§5.2), `enable_thinking` off
where applicable, early stopping on dev loss (`eval_strategy`, `eval_steps`,
load-best-on-dev), the local-file path to the matching builder output, and the
run output dir. The recipe above is the per-arm DEFAULT config; the full
pre-registered run matrix (PROTOCOL.md §3.1 / §3.1a) expands each default into 3
seeds plus the LR / beta sensitivity-panel cells. That seed-and-panel expansion
is driven by a run-matrix / sweep config layered over these default recipes, NOT
by hand-writing 19 recipe files; see the scoped CODE follow-up in §9.1. The
bridge recipes use `--model-name`
overrides for the gated Llama-2-7b-chat (gap #5) and consume Cheng's IDK
training data (gap #4 prerequisite).

### 5.7 Submodule git workflow (CODE-phase note)

`synaptic-tuner/` is a SEPARATE git repo. DPO-trainer + preset work is committed
THERE on its own feature branch (e.g. `feat/dpo-trainer-eh-phase1`), pushed,
and then the research-repo worktree's submodule pointer is bumped to that commit
in a research-repo commit. HF Jobs checks out the exact pushed submodule SHA, so
the cloud (8B) arm cannot run until the submodule branch is pushed and the
pointer bumped. CODE sequences: land+push submodule DPO work first, bump pointer,
then cloud runs. The local 4B pilot can run against the working-tree submodule
before the pointer bump.

---

## 6. Component D — Eval harness

### 6.1 Responsibility

Score every trained adapter (and `base`) on the in-domain held-out set and the
OOD sets, emit the full metric decomposition with paired CIs, deterministically
and committed. Single responsibility: adapter-in, metrics-CSV-out. Reuses the
Cheng-validated scorer so bridge-arm numbers are directly comparable.

### 6.2 Where it lives

The metric suite (over-refusal decomposition, token ECE, OOD scorers) is NOT
pre-built in the tuner's `Evaluator/` (PREPARE gap #6). Decision: build the
Phase-1 scorers as **checked-in scripts in the research repo** under
`experiment/phase1/eval/`, generating responses via vLLM (same backend as the
probe) loading each adapter. This keeps the novel metrics in the repo that owns
the paper and its provenance discipline, rather than forcing them into the
tuner's YAML-assertion harness. The tuner `Evaluator/` is used only if a quick
smoke scenario is wanted (the existing
`labkit_epistemic_humility_smoke.yaml` can be a sanity check). Gap #7
(`Evaluator/recipes/` doc drift) is dispositioned as: do not rely on that path;
use `Evaluator/config/` if the tuner harness is touched at all. The Phase-1
suite does not depend on it.

### 6.3 Core scorers (ported from `reanalyze_idk_outputs.py`, read-only source)

The refusal-detection and correctness primitives are lifted verbatim
(re-implemented in the new eval module, NOT imported from meta-analysis which is
read-only):

- `REFUSAL_MARKERS` = the 4 markers ("beyond the scope of my knowledge", "i am
  not sure what the answer is", "i don't know the answer", "i do not know the
  answer"). The abstention-template bank (§4.3) is constrained to contain these.
- `normalize(text)` = `" ".join(re.findall(r"[a-z0-9]+", text.lower()))`.
- `is_correct(gen, aliases)` = word-bounded alias membership.
- known/unknown labels for in-domain test come from OUR probe of the test
  questions' answerability (the model-specific labeling), NOT from a training
  target. (The bridge arm is the exception: it uses Cheng's IDK-target encoding
  exactly as `reanalyze_idk_outputs.py` does, for apples-to-apples replication.)

### 6.4 Metric suite (per arm, in-domain and per OOD set)

1. **Truthful rate + 4-quadrant matrix** (Cheng): quadrants Ik-Ik (known,
   answered correct), Ik-Idk (unknown, refused), and the two error cells.
   `truthful = (refuse_on_unknown + correct_on_known) / n`. Primary metric.
2. **Refusal recall** on unknowns and **over-refusal** on knowns (the
   decomposition the field omits). These are the bridge-arm comparison targets
   (Idk-SFT 42.71%, Idk-DPO 23.27%).
3. **AP** over confidence-ranked answers (R-Tuning comparability). Confidence =
   P_correct-style self-consistency from N eval samples, or sequence logprob.
4. **Token-level ECE on MMLU** MCQ. MMLU schema is `question/subject/choices/answer`
   (answer = correct choice index). ECE from the model's per-choice token
   probabilities (probability mass on each option letter), binned, vs accuracy.
   This is the abstention-calibration tension measured on the same run (first
   time for KTO). Pinned: 15 equal-width bins, standard ECE.
5. **TruthfulQA** MC1/MC2 + over-refusal on its informativeness axis.
6. **Accuracy retention** on answered questions (capability tax): accuracy among
   answered known questions vs the `base` arm.

### 6.5 OOD sets (all on disk)

| Set | File | Probe |
|---|---|---|
| KUQ | `kuq/knowns_unknowns.jsonl` (`unknown` bool) | unanswerable detection |
| CoCoNot | `coconot/contrast_test.jsonl` | over-refusal headline |
| AbstentionBench | `abstentionbench-repo/` (loader + indices) | abstention transfer |
| MMLU | `mmlu/test.jsonl` | token ECE + far-OOD accuracy |
| TruthfulQA | `truthfulqa/TruthfulQA.csv` | truthful rate |
| PopQA | `popqa/test.jsonl` | near-OOD long-tail |
| SelfAware | `selfaware/SelfAware.json` | answerable/unanswerable |

OOD sets share NO questions with training (they are different corpora; the
in-domain leakage guard does not apply to them, but the eval harness asserts the
trained question set does not appear in any OOD set as a cheap defensive check).

### 6.6 Statistics

Two-layer uncertainty treatment (pre-registered in PROTOCOL.md §3.6; the
protocol is the SSOT, this is the implementation view):

- **Layer 1, within-run / eval-question:** paired bootstrap CIs over eval
  questions for every metric (resample questions with replacement, recompute,
  percentile CI). Paired = same questions across arms.
- **Layer 2, across-seed / training stochasticity:** each headline arm is
  trained at 3 seeds; every headline metric is reported as mean and CI across
  those 3 seeds. This is the training-procedure error bar the field omits. The
  eval harness must therefore aggregate per-seed metric outputs into a
  per-arm mean+CI (the `stats.py` consumer reads N seed-level `metrics.json`
  files per arm).
- **Between-arm significance:** McNemar on the binary outcomes (refused-or-not,
  correct-or-not), computed on MATCHED seeds (seed i of arm A vs seed i of arm B
  on identical questions) so it is not confounded by cross-seed pairing.
- **Sensitivity panel:** reported as a robustness figure (headline metric per
  panel cell, 1 seed each), explicitly WITHOUT seed-level CIs and never as a
  headline source (PROTOCOL.md §3.1a headline-only rule).
- Power: at n≈11k in-domain, a 3pp truthful-rate difference has power > 0.95;
  the across-seed CI (layer 2) is now estimated from 3 points per arm.
- All scorers deterministic; eval generations use fixed seeds; outputs (raw
  generations + metric CSVs) committed, same provenance discipline as paper 1.

### 6.7 Output artifact

```
experiment/phase1/eval/results/<arm>__<eval_set>/
  generations.jsonl     # raw model outputs (released)
  metrics.json          # the 6-metric suite + 4-quadrant counts
  bootstrap_ci.json     # per-metric CIs
experiment/phase1/eval/results/comparisons/
  mcnemar.csv           # pairwise arm comparisons
  summary_table.csv     # the paper's headline table (all arms x all metrics)
```

---

## 7. Directory layout (research repo)

```
experiment/
  protocol/                         # exists; PROTOCOL.md -> v0.2, trajectory edit
  phase1/                           # NEW
    README.md                       # how to run the pipeline end to end
    probe/
      probe.py                      # Component A
      config/probe.yaml             # pinned sampling config (N=32, T, thinking off)
      <model_tag>/probe_results.jsonl  probe_manifest.json
    data/
      build_datasets.py             # Component B (all 3 formats from probe_results)
      config/build.yaml             # mapping flags, budget, abstention bank ref
      abstention_bank.json          # style-varied marker-bearing phrasings
      <model_tag>/...               # outputs (§4.8)
    eval/
      run_eval.py                   # Component D driver (adapter -> generations)
      scorers.py                    # ported refusal/correctness/ECE/AP scorers
      stats.py                      # bootstrap + McNemar
      config/eval.yaml              # eval sets, sampling, bins
      results/...                   # outputs (§6.7)
    configs/                        # optional: top-level run manifests tying arms together
docs/
  architecture/phase1-pipeline.md   # this doc
  preparation/...                   # PREPARE docs
datasets/
  scripts/fetch_datasets.py         # +1 spec row (train split) — CODE prerequisite
  triviaqa-rc-nocontext/train.jsonl # fetched (CODE prerequisite)
```

Submodule (`synaptic-tuner/`) additions: `Trainers/dpo/` (§5.4), KTO Qwen3
preset, method registration (§5.5), Phase-1 recipes (§5.6).

Config convention: every component reads a checked-in YAML (`config/*.yaml`),
no one-off scripts, no hardcoded paths or sample counts. Each writes a manifest
recording the exact config SHA used. This is what makes the pipeline re-runnable
on any model (Phase 4) by swapping `model_tag` + `model_name`.

---

## 8. Data schemas / interface contracts (summary)

| Boundary | Artifact | Producer | Consumer | Key fields |
|---|---|---|---|---|
| fetch -> A | `triviaqa-rc-nocontext/train.jsonl` | fetch script | probe | `question`, `question_id`, `answer.normalized_aliases` |
| A -> B | `probe_results.jsonl` | probe.py | build_datasets.py | `question_id`, `p_correct`, `greedy_correct`, `sampled_answers`, `sampled_correct`, `label` |
| B -> C | `{sft,dpo,kto_*}_{train,dev}.jsonl` | build_datasets.py | trainers | per-format (§4.4-4.6); `build_manifest.json` carries budget+leakage proof |
| C -> D | LoRA adapters | trainers | run_eval.py | adapter dir per arm/seed |
| D -> paper | `metrics.json`, `summary_table.csv`, `mcnemar.csv` | eval | paper 2 | full metric suite |

Contracts are file-on-disk JSONL/JSON, language-agnostic, inspectable, and
provenance-stamped. This decouples the four components: each can be implemented
and tested against a fixture of the upstream artifact without the upstream
component existing yet.

---

## 9. CODE-phase work breakdown with S2 boundaries

Six workstreams (WS-0..WS-4 below; WS-5, the experiment-runner skill package, was
promoted from the §9.1 follow-up by user directive and is designed in full in
§9.2). File-level
ownership keeps coders from colliding. WS-0 is the prerequisite fetch; WS-1 and
WS-2 are independent and parallelizable; WS-3 depends on WS-2's schema (not its
data, which can be fixtured); WS-4 depends on the DPO schema only; WS-5 sits above
the recipe + trainer surface and consumes WS-2 outputs read-only.

### WS-0 (prerequisite, fast): dataset fetch + provenance

- Owns: `datasets/scripts/fetch_datasets.py` (+1 SPEC row),
  `datasets/triviaqa-rc-nocontext/dataset.md` (provenance stanza).
- Deliverable: `train.jsonl` on disk, disjointness spot-checked.
- Gap disposition: #2, #3. Records (does not block) the OpenMOSS Cheng IDK
  training-data fetch for the bridge arm (#4), which is license-gated and needs
  user sign-off before fetching.

### WS-1: knowledge probe (research repo)

- Owns: `experiment/phase1/probe/` (probe.py, config, outputs).
- Depends on: WS-0 output (or the documented validation-remainder fallback).
- Contract out: `probe_results.jsonl` (§3.8). Can be developed against a
  small hand-made `train.jsonl` fixture.
- Includes the label-noise sensitivity analysis (§3.6).

### WS-2: dataset builders (research repo)

- Owns: `experiment/phase1/data/` (build_datasets.py, config, abstention_bank).
- Depends on: `probe_results.jsonl` SCHEMA (fixture, not real data).
- Contract out: the 4 arms' train/dev JSONL + `build_manifest.json`.
- Owns the leakage guard (§3.2), budget equalization (§4.2), abstention bank
  (§4.3), both KTO mappings (§4.6).

### WS-3: DPO trainer + method registration (SUBMODULE — separate git repo)

- Owns (submodule): `Trainers/dpo/` (new), KTO Qwen3 preset in
  `Trainers/kto/train_kto.py`, the 4 method-registration sites (§5.5), Phase-1
  recipe YAMLs (§5.6).
- Depends on: DPO on-disk SCHEMA (§4.5) from WS-2 (fixture).
- S2 boundary: this is the ONLY workstream touching the submodule. It commits
  on a submodule feature branch, pushes, and the research-repo pointer bump is a
  separate research-repo commit (§5.7). Other workstreams MUST NOT touch
  `synaptic-tuner/`.
- Gap disposition: #1 (DPO), Qwen3 preset, #5 (bridge `--model-name` override
  in the bridge recipes).
- VERIFY items: exact `unsloth/Qwen3-*` repo names against live HF; that
  `enable_thinking=False` is honored by the Qwen3 chat template path (§5.3);
  the cloud-method dispatch maps `dpo -> Trainers/dpo`; grep-sweep that no
  `("sft","kto","grpo")` enumeration site is missed.

### WS-4: eval harness + stats (research repo)

- Owns: `experiment/phase1/eval/` (run_eval.py, scorers.py, stats.py, config,
  results).
- Depends on: trained adapters (C) for real runs; scorer logic depends only on
  the generations schema (fixture) and `cheng_test_gold.jsonl` (on disk).
- Contract out: `metrics.json`, `summary_table.csv`, `mcnemar.csv` (§6.7).
- Gap disposition: #6 (build the scorers), #7 (do not rely on
  `Evaluator/recipes/`). Ports (re-implements) the read-only
  `reanalyze_idk_outputs.py` primitives.

### Parallelism and ordering

```
WS-0 ---> WS-1 ---> WS-2 ---+--> (real training) ---> WS-4 (real eval)
                            |
   WS-3 (submodule) <-- schema only (fixture), parallel with WS-1/WS-2
   WS-4 scorers <-- schema only (fixture), parallel with everything
```

Schemas in §8 are the synchronization points. As long as WS-2 freezes the DPO
on-disk schema (§4.5) and the eval generations schema (§6.7) early, WS-3 and
WS-4 proceed in parallel against fixtures. Real end-to-end runs gate on the
PROTOCOL.md (currently v0.3 DRAFT) user sign-off (no training before sign-off).

### 9.1 Scoped follow-up: run-matrix / sweep orchestration (post-v0.3)

The v0.3 run matrix (PROTOCOL.md §3.1 / §3.1a: 3 headline seeds per arm + the
LR/beta sensitivity panel = 19 runs at 4B, plus 3 seeds at 8B pending veto)
implies one new CODE artifact NOT covered by WS-0..WS-4: a run-matrix / sweep
orchestration config + runner that layers seed and panel-cell variation over the
per-arm DEFAULT recipes (§5.6), launches the cells in parallel on HF Jobs, and
tags each run with its (arm, seed, panel-cell) coordinate so the eval harness can
aggregate by arm (the layer-2 mean+CI in §6.6) and isolate the panel cells. This
is NAMED here as a scoped follow-up, not designed in depth: it does not change
any WS-1/WS-2/WS-3/WS-4 interface contract (it sits ABOVE the existing per-arm
recipe + trainer surface, reusing `tuner.py cloud-pipeline` per cell).

**Promoted to WS-5 (2026-06-10, user directive; deliverable shape revised
same day).** This follow-up is now a CODE-phase workstream, designed in full in
§9.2. Two design questions are RESOLVED:

1. *Reuse the tuner's `experiment_spec` vs a research-repo driver* -> a
   research-repo driver. The user directed that the experiment runner live in the
   Epistemic-Humility-Research repo and that nothing experiment-specific be added
   to the tuner; the tuner's `experiment_spec` surface has no seed-matrix or
   hyperparameter-sweep concept anyway (it models a single train -> eval -> loss
   -> analysis bundle). The driver owns the matrix and invokes the tuner only
   through its existing public CLI verbs.
2. *What FORM the deliverable takes* -> a Claude Code SKILL package in the
   research repo at `.claude/skills/experiment-runner/`, modeled structurally on
   the tuner's `synaptic-tuner/.claude/skills/fine-tuning/` skill (SKILL.md
   runbook + skill-local `scripts/` + `reference/` + example config). The
   matrix-expansion logic is a skill-local executable script; the runbook lives in
   SKILL.md. This mirrors how the tuner packages an operational workflow (the
   fine-tuning skill carries `scripts/launch_experiment_batch.py` next to a
   SKILL.md runbook) rather than scattering a bare driver under `experiment/`.

### 9.2 WS-5: experiment runner (research-repo skill package)

**Goal and boundary.** A Claude Code SKILL in the research repo that packages the
operational workflow for expanding the PROTOCOL v0.3 (SIGNED OFF) run matrix into
per-run tuner invocations, on two execution lanes, with full provenance and
prerequisite gating. It is orchestration GLUE packaged as a skill, not a
framework. Hard boundary (user directive): the skill lives at
`.claude/skills/experiment-runner/` in THIS repo, and the recipes + run records it
operates on are repo content under `experiment/phase1/`. It adds NOTHING
experiment-specific to the `synaptic-tuner/` submodule, which stays a clean general
dependency invoked only through its existing public CLI (`tuner.py local-run`,
`tuner.py cloud-pipeline` / `run-experiment`). The skill reads the tuner's patterns
(recipe schema, CLI verbs) as reference; it does not modify them.

**Why a skill, modeled on the tuner's fine-tuning skill.** The user directed that
the experiment-running deliverable be a Claude Code skill in the research repo,
structurally like `synaptic-tuner/.claude/skills/fine-tuning/` (the local/cloud
training-run skill). That skill's shape is the template: a SKILL.md runbook
(frontmatter `name`/`description`/`allowed-tools`, a Quick Reference command table,
a CLI Discipline section, Common Patterns, and a Progressive Reference table) plus
skill-local `scripts/` (executable helpers like `launch_experiment_batch.py`),
`reference/` deep-dive docs loaded on demand, and example `configs/`. WS-5 adopts
the same shape so that an agent (or the user) loads ONE skill and has the full
runbook + the executable matrix logic + the provenance discipline in one place.

**Why a driver, not the tuner's experiment_spec.** The tuner's
`shared/experiment_tracking/experiment_spec.py` models a single experiment bundle
(dataset + one training stage + eval/loss/analysis); it has no notion of a seed
sweep or a one-hyperparameter sensitivity grid, and extending it would mean editing
the tuner (forbidden) or contorting the research code around a tuner dataclass. A
skill-local script that generates per-cell recipes from a base recipe and a matrix
config, then shells out to the tuner CLI per cell, is both simpler and keeps the
tuner generic. The recipe (the tuner's native, self-describing unit: `name /
target / method / model / dataset.local_file / training / lora / artifacts`, see
§5.6) is the contract surface between the two repos.

**Recipes and run records are repo content, not skill internals.** Following the
tuner's own convention (recipes live in `Trainers/recipes/` as repo content; the
skill documents the workflow and carries only executable helpers), the per-arm
DEFAULT recipes stay at `experiment/phase1/recipes/` (already relocated there by
task #24) and the provenance run records are written to
`experiment/phase1/run_records/` as committed artifacts the paper releases. The
skill folder holds the runbook, the matrix-expansion script, the matrix config,
and reference docs -- NOT the recipes or the run records. This keeps the
provenance spine (records) and the run inputs (recipes) as first-class,
version-controlled research artifacts independent of the skill packaging.

**Directory layout (research repo).**

```
.claude/skills/experiment-runner/        # WS-5 skill package (new)
  SKILL.md                               # runbook: frontmatter + Quick Reference +
                                         #   CLI Discipline + Common Patterns +
                                         #   Progressive Reference (models fine-tuning/SKILL.md)
  scripts/
    run_matrix.py                        # the driver: expand matrix -> per-cell recipes -> invoke tuner
    check_prereqs.py                     # standalone prerequisite gate (also importable by run_matrix)
  config/
    matrix.yaml                          # the run-matrix definition (committed; the SSOT for runs)
  reference/
    run-records.md                       # run-record schema + provenance discipline (HANDOFF.md §5)
    lanes.md                             # local 3090 vs HF Jobs parallel lane deep-dive
    matrix-expansion.md                  # how matrix.yaml maps to PROTOCOL v0.3 cells + count assertions

experiment/phase1/                       # repo content the skill operates on (NOT under the skill)
  recipes/                               # per-arm DEFAULT recipes (relocated here by task #24)
    eh_phase1_qwen3_4b_{sft,dpo,kto_congruence,kto_correctness_safe}.yaml
    eh_phase1_qwen3_8b_{sft,dpo,kto_congruence}.yaml
    eh_bridge_llama2_7b_chat_{sft,dpo}.yaml
  run_records/                           # one JSON run record per launched cell (provenance; committed)
```

**SKILL.md content split (what the runbook holds vs what the scripts hold).** The
SKILL.md is the human/agent-facing runbook and carries NO matrix logic itself; it
documents how to invoke the skill-local scripts. Its sections mirror the
fine-tuning skill: (1) frontmatter `name: experiment-runner`, a `description`
naming the PROTOCOL v0.3 matrix + two lanes + provenance, and
`allowed-tools: Read, Bash, Write, Grep, Glob`; (2) a **Quick Reference** table
(dry-run the matrix, check prereqs, launch local smoke cell, launch cloud matrix,
resume, inspect a run record); (3) a **CLI Discipline** section that inherits the
tuner skill's non-negotiables verbatim in spirit -- never relaunch a cost-incurring
cloud run or cancel a job without explicit user approval; never guess tuner CLI
flags (check `tuner.py --help`); prefer the checked-in `run_matrix.py` over ad hoc
loops; (4) **Common Patterns** (the canonical launch sequence: check prereqs ->
dry-run -> local smoke -> cloud matrix); (5) a **Progressive Reference** table
pointing at the three `reference/*.md` deep-dives. The executable behavior --
matrix expansion, count assertions, recipe materialization, lane dispatch, record
emission, gating -- lives in `scripts/run_matrix.py` + `scripts/check_prereqs.py`,
so the runbook stays a runbook and the logic stays testable.

#### (a) Run-matrix definition and expansion

`.claude/skills/experiment-runner/config/matrix.yaml` is the committed SSOT that
encodes PROTOCOL v0.3 §3.1 / §3.1a as data (the expansion script enforces
conformance, it does not re-decide it):

```yaml
# Conforms to PROTOCOL.md v0.3 (LOCKED). Counts are asserted at load time.
matrix_version: "phase1-v0.3"
seeds_headline: [1, 2, 3]          # 3 seeds per arm (4B and 8B headline)
arms_4b:
  - {recipe: eh_phase1_qwen3_4b_sft, method: sft, has_beta: false}
  - {recipe: eh_phase1_qwen3_4b_dpo, method: dpo, has_beta: true}
  - {recipe: eh_phase1_qwen3_4b_kto_congruence, method: kto, has_beta: true}
arms_8b:
  - {recipe: eh_phase1_qwen3_8b_sft, method: sft}
  - {recipe: eh_phase1_qwen3_8b_dpo, method: dpo}
  - {recipe: eh_phase1_qwen3_8b_kto_congruence, method: kto}
panel_4b:
  lr_multipliers: [3.0, 0.3333333]   # each arm x its OWN default LR (per-arm-relative)
  beta_values: [0.05, 0.5]            # DPO + KTO only; SFT skipped
  panel_seed: 1                       # 1 seed per panel cell
bridge:
  - {recipe: eh_bridge_llama2_7b_chat_sft, method: sft}
  - {recipe: eh_bridge_llama2_7b_chat_dpo, method: dpo}
confirm_8b_seeds: 3                   # FLAG: pending-veto bump (PROTOCOL 3.1); set 1 if vetoed
```

Expansion logic (the matrix x seeds product):

- **Headline 4B:** for each of 3 arms x 3 seeds = 9 cells, base recipe with
  `training.seed` overridden, default LR/beta untouched.
- **LR panel 4B:** for each of 3 arms x 2 multipliers = 6 cells, base recipe at
  `panel_seed`, `training.learning_rate = default_lr * multiplier` (per-arm
  default read FROM the recipe, so the per-arm-relative rule is structural).
- **beta panel 4B:** for DPO + KTO (2 arms) x 2 beta values = 4 cells at
  `panel_seed`, `training.beta` overridden. SFT skipped (`has_beta: false`).
- **Confirm 8B:** 3 arms x `confirm_8b_seeds` (default 3) = 9 cells, default
  config.
- **Bridge:** 2 cells, default config, 1 seed.

`scripts/run_matrix.py` asserts the resulting counts match PROTOCOL v0.3 (19 at
4B, 9 at 8B, 2 bridge) and ABORTS on mismatch, so a typo in matrix.yaml cannot
silently change the pre-registered design. Each cell carries a deterministic
coordinate `(arm, size, cell_type, seed, hyperparam_override)` that becomes its
run id and its tag for eval-side aggregation (§6.6 layer-2 mean+CI by arm; panel
cells isolated). (`reference/matrix-expansion.md` documents the full
matrix.yaml -> cell mapping and the count-assertion table.)

Per-cell recipe generation: the script deep-copies the base recipe from
`experiment/phase1/recipes/`, applies the single override (seed, or one of
LR/beta), rewrites `name` and `artifacts.output_root` to embed the coordinate, and
writes the materialized recipe to a work dir. It does NOT hand-maintain 30 recipe
files; the 9 base recipes (repo content) plus matrix.yaml (skill config) are the
only committed run inputs.

#### (b) Two execution lanes

The recipe's `target` field (`local` vs `cloud`) and the script's `--lane` flag
select the invocation. `run_matrix.py` does not reimplement training or cloud
mechanics; it shells out to the tuner CLI (`reference/lanes.md` holds the
per-lane deep-dive):

- **Local RTX 3090 lane** (`--lane local`): development, pilot, and smoke runs.
  Invokes `python tuner.py local-run --job-config <materialized-recipe>.yaml
  --yes` per cell, serially (one local GPU). Used for fast iteration and a single
  smoke cell before committing the matrix to the cloud lane. **Method-dispatch
  resolution (HANDLER EXTENSION, lead-ratified 2026-06-10; supersedes both the
  inject-`run.command` idea and the Option-A trainer-`--config` idea after a
  ground-truth re-read of local_run_handler.py):** the handler's command builder
  (`_build_trainer_command`, :478 -- renamed from `_build_sft_command` as part of
  the CODE close since it is no longer SFT-bound, and now takes `method` as a
  parameter) is method-generic in its CORE (it reads the trainer path from the
  recipe's `run.trainer` field (:494, defaulting to `Trainers/sft/train_sft.py` but
  configurable) and assembles the command from the
  `model`/`dataset`/`training`/`lora` blocks); `seed` is ALREADY in its forwarded
  training-key list. The dispatch was blocked by two ARTIFICIAL gates -- the
  `elif method == "sft"` dispatch guard (:585) and a deliberately-skipped `beta`
  forward whose in-code comment skips it *because* the path was assumed SFT-only.
  **Governing principle (the §(b.2) flag-set finding, coder-cloud #34):** the
  builder is NOT uniformly method-agnostic -- some flags it emits are SFT-only and
  the DPO/KTO trainers' argparse REJECTS them (would crash). The fix splits those
  flags by whether they are LOAD-BEARING for the experiment:
  - **Run-control flags** (`--quiet`/`--no-dashboard`/`--save-steps`/
    `--save-total-limit`/`--load-in-4bit`): pure ergonomics, ZERO experimental
    meaning. METHOD-GATE them in the builder (dpo/kto skip them). No provenance
    risk -- nothing load-bearing is substituted.
  - **LoRA scalars** (`--lora-r`/`--lora-alpha`/`--lora-dropout`/
    `--lora-target-modules`/`--init-lora-weights`): LOAD-BEARING (§5.2 "identical
    LoRA budget across arms" is the core confound control). The DPO/KTO trainers
    read LoRA ONLY from `config.lora.*` (no `--lora-*` argparse exists). Gating
    these + falling back to sibling `config.yaml` would SILENTLY corrupt the
    budget: the 8B recipes pin r=64/alpha=128 but the trainer `config.yaml` default
    is r=32/alpha=64, so 8B DPO/KTO would train at the WRONG budget (the 4B
    coincidence-match masks it). Resolution: FLAG PARITY -- add `--lora-*` to
    `train_dpo.py` + `train_kto.py` so the builder's emissions are accepted and the
    recipe stays the SSOT. (`--use-dora`/`--use-rslora` already have parity across
    all three trainers.)
  The hyperparameter subset the trainers already accept
  (`--local-file`/`--model-name`/`--learning-rate`/`--batch-size`/`--num-epochs`/
  `--seed`/`--beta`, `train_dpo.py:195-226`, `train_kto.py:244/324/329/334/339`;
  the builder's `_flag_name` maps `local_file -> --local-file`) flows unchanged. So
  the fix is the handler extension (widen the dispatch guard to
  `method in {"sft","dpo","kto"}`, forward `beta` method-gated, method-gate the
  run-control flags) PLUS narrowly-scoped LoRA flag parity in the two trainers
  (lead-ratified trainer-edit reopening for THIS load-bearing subset only). NO
  `run.command` synthesis or trainer-`--config` arg is needed. local-run becomes
  UNIFORM across all four registered methods (the user's "tuner stays generally
  useful" principle),
  and the runner stays purely declarative: per local cell WS-5 materializes one
  declarative recipe (staging data via §(b.1), setting `run.trainer:
  Trainers/{method}/train_{method}.py` and the per-cell `training.seed`/
  `training.beta`), and `tuner.py local-run` forwards everything through its typed
  surface. The full invocation the tuner builds is recorded in the run record's
  `tuner_invocation`. (The pre-existing regression test that pinned local-run as
  SFT-only pinned the ARTIFICIAL limit, not a design invariant; it is updated to
  assert the handler dispatches all registered methods.)
- **HF Jobs parallel lane** (`--lane cloud`): the matrix execution lane.
  Invokes `python tuner.py cloud-pipeline --method <m> ...` (or `run-experiment`
  with the materialized recipe) per cell. Cells launch in PARALLEL across HF
  Jobs (the script submits and records job handles; it does not block serially),
  which is what makes the 19+9 matrix affordable in wall-clock (PROTOCOL §3.6).
  Precondition (carried from §5.7): HF Jobs checks out the pinned submodule SHA,
  so the submodule must be pushed and the pointer bumped before the cloud lane
  runs; the script verifies this in prerequisite gating (below).

The script is lane-agnostic above the invocation: matrix expansion, provenance,
and gating are identical; only the per-cell command differs. A `--dry-run` prints
the materialized recipes and the commands without launching.

#### (b.1) Data-locality contract (the tuner container sees only the tuner repo)

A constraint surfaced during CODE (coder-dpo, verified against the tuner source)
shapes how WS-5 feeds data to the tuner: the tuner container mounts/clones ONLY
the tuner repo root. Local Docker bind-mounts `{tuner_repo_root}:/workspace/repo`
(`tuner/handlers/local_run_handler.py:391`); HF Jobs clones ONLY the tuner repo
into `/workspace/repo` (`tuner/cloud/hf_jobs.py`). And `dataset.local_file` is
resolved tuner-repo-relative inside the container -- `local_run_handler.py:502`
hardcodes `container_dataset_path = /workspace/repo / local_file`. The research
repo's `experiment/phase1/data/` is therefore NEVER visible to the tuner
container. A recipe whose `dataset.local_file` points at a research-repo-relative
data path does NOT resolve. This makes data-feeding a WS-5 responsibility, handled
differently per lane:

- **Recipes are purely declarative.** The relocated recipes carry
  `model / dataset / training / lora / artifacts + method / provider` only; the
  `run.command` blocks (which previously hardcoded `/workspace/repo/...` absolutes
  and `cd /workspace/repo/Trainers/<method>`) are STRIPPED. WS-5 owns container
  wiring (staging + path rewrite) only; under the handler-extension resolution
  (§(b) lane bullet) the materialized declarative recipe is handed to
  `tuner.py local-run`, which forwards every field through its own typed builder
  for all methods, so WS-5 NEVER hand-assembles a flag list or synthesizes a
  `run.command` -- the recipe stays the sole contract surface (it sets
  `run.trainer` + `method` + the per-cell `training.*` overrides). No WS-5
  placeholder vocabulary
  (e.g. `{tuner_dir}` / `{data_root}`) leaks into committed recipes -- they stay
  valid, tuner-runnable job-configs; WS-5 supplies the final `dataset.local_file`
  value at materialization time. (Recipe `dataset.local_file` in the committed
  files is a staging placeholder the README documents as WS-5-rewritten.)
- **Local lane: stage into the tuner working tree.** Per cell, `run_matrix.py`
  copies the resolved research-repo data file
  (`experiment/phase1/data/<model_tag>/<method>_{train,dev}.jsonl`) into an
  EPHEMERAL gitignored scratch dir under the tuner working tree
  (`synaptic-tuner/.eh_staging/<run_id>/`), then sets the materialized recipe's
  `dataset.local_file` to that tuner-repo-relative staged path (so the
  `/workspace/repo` join at `:502` resolves). The staging dir is never committed
  and is NOT a tuner source addition, so the no-pollution boundary holds (it is
  scratch under the submodule checkout, the way any build artifact would be). A
  `.gitignore` entry for `.eh_staging/` is the only tuner-tree touch, and it is a
  gitignore line, not code.
- **Cloud lane: reference data by HF-hub name, not a local file.** HF Jobs checks
  out a pushed tuner COMMIT, so ephemeral staged scratch is not in the container.
  The cloud lane therefore references the dataset by its HF-hub `dataset.name`,
  NOT by `local_file`. **User ruling (2026-06-10):** the Phase-1 SFT/DPO/KTO
  training datasets are published PUBLICLY to the HF hub (via the tuner's
  dataset-publishing skill workflow), and cloud cells reference them by hub
  `dataset.name`. This makes "Phase-1 datasets published to the hub" a cloud-lane
  launch prerequisite, enforced by the prerequisite gate (§(d)) with the SAME
  skip-vs-abort semantics as the bridge cells: if the hub datasets for a cloud
  cell's arm are not yet available, the CLOUD cells skip (recorded SKIPPED), the
  local-lane 4B pilot runs first, and the rest of the matrix is not aborted. The
  local lane is unaffected by hub availability (it stages from local builder
  output). Cloud-cell run records additionally carry the hub dataset REVISION SHA
  (§(c)), so referencing data by name does not weaken provenance -- it pins the
  exact published revision, strengthening HANDOFF.md §5 compliance.
- **Bridge cells are LOCAL-LANE ONLY (user ruling 2026-06-10, blocker #30).** The
  OpenMOSS Cheng IDK training data is VENDORED under a DO-NOT-REDISTRIBUTE
  containment rail: the user accepted the license risk for USE, but the data is
  never committed to git and never published to the HF hub. Because the cloud lane
  requires data to be hub-published (bullet above), the 2 bridge cells CANNOT use
  the cloud lane -- they run LOCAL-lane only, staging the vendored data through
  `.eh_staging/` like any other local cell. (Implementation consequence: the two
  `eh_bridge_llama2_7b_chat_{sft,dpo}` recipes currently carry `target: both`;
  the #27 recipe revision changes them to `target: local` so the matrix expander
  never emits a bridge cloud cell.) The hub-availability gate (§(d) item
  3a) therefore scopes to the Qwen3 CLOUD cells only and never applies to the
  bridge. This is a license-containment constraint, not a capability gap.

The staging copy is recorded in the run record (`source_data_file` ->
`staged_data_file` for local; `hf_dataset_name` + `hf_dataset_revision` for
cloud) so provenance still
ties each run to the exact bytes it trained on.

#### (b.2) Tuner-capability dependency: per-cell seed and beta forwarding

A second constraint surfaced during CODE (coder-dpo, verified against the tuner
source): the matrix's per-cell SEED (3-seed headline sweep) and BETA (DPO/KTO beta
panel, PROTOCOL v0.3 §3.1a) could NOT be expressed through the tuner as originally
found, on EITHER lane. The tuner forwards training args through an explicit typed
CLI surface, and at discovery neither `seed` nor `beta` was wired. The original
state and its remediation:
- LOCAL: `local_run_handler.py` forwarded a fixed key list (batch_size,
  gradient_accumulation, learning_rate, num_epochs, max_steps, save_steps,
  save_total_limit, tier, resume_from_checkpoint) -- `seed`/`beta` absent, so a
  recipe's `training.seed`/`training.beta` were SILENTLY dropped and the trainer
  fell back to its `config.yaml` default (seed 42 / beta 0.1). **Now:** `seed` is
  forwarded (coder-cloud #32); the remaining piece is widening the method-dispatch
  guard and forwarding `beta` (the handler-extension fix, §(b) lane bullet).
- CLOUD: `CloudTrainingConfig` had no `seed`/`beta` field and
  `_hf_command_builder.py` emitted no `--seed`/`--beta`; same silent default.
  **Now RESOLVED** (coder-cloud #32: cloud config + builder forward both).
- TRAINERS accepted `--beta` but NOT `--seed` (they read `config.seed` from YAML).
  **Now RESOLVED** (coder-cloud #32 added `--seed` to the trainers,
  `train_dpo.py:223`, with an `is not None` guard so seed=0 is honored).

This is provenance-critical: a run record would claim the intended seed/beta while
the trainer used defaults -- invisible matrix corruption (every headline seed
identical; every beta-panel cell at 0.1), a direct violation of the SACROSANCT
provenance rule. The FIX is a TUNER-SIDE general capability (NOT a WS-5 workaround,
NOT an experiment-specific hack): forward seed+beta mirroring the existing typed
`learning_rate` flow at every layer (handler forwarding list;
`CloudTrainingConfig` + command-builder emission, beta method-gated to DPO/KTO; the
`--seed` trainer arg). A generic key/value overrides passthrough was explicitly
REJECTED -- it bypasses the typed CLI surface and validation the tuner has kept
throughout. This work lands in the synaptic-tuner submodule as a generic capability,
keeping the tuner a clean general dependency that GAINS a capability rather than
absorbing EH-specifics. Status: the cloud config + builder and the `--seed` trainer
arg LANDED (coder-cloud #32); the remaining piece is the handler-extension fix
(widen the local-run method guard to all registered methods + forward `beta` +
method-gate the SFT-only run-control flags) PLUS narrowly-scoped LoRA flag parity in
the two trainers (the §(b) load-bearing-flag split), which ALSO removes the
local-run "SFT-only" wart generically (§(b) lane bullet).

WS-5 sequencing consequence: the experiment runner is built lane-agnostic first
(matrix expansion, count assertions, run-record emission, prerequisite gate,
`--dry-run`, recipe revision), and the seed/beta overrides are not RELIED ON for a
real launch until the tuner-side capability fully lands (cloud done; local handler
extension pending). The prerequisite gate (§(d)) probes for the capability on each
cell's lane (asserts the resolved tuner forwards seed/beta on the path that cell
uses) so a runner built against an un-upgraded tuner ABORTS rather than silently
launching the corrupt-default matrix. WS-5 itself is unchanged in shape -- it only
materializes declarative recipes and shells out to `tuner.py`; it is the tuner's
own arg surface that carries the seed/beta sink.

**Per-lane dependency on the tuner seed/beta fix (SIMPLIFIED under the
handler-extension resolution, §(b) lane bullet; the earlier per-method split is
withdrawn):** every cell, every lane, every method forwards seed/beta through the
tuner's own typed surface, so the dependency is now UNIFORM per lane and the
runner is purely declarative.
- LOCAL (all methods sft/dpo/kto) depend on the handler fix: widen the dispatch
  guard to `method in {"sft","dpo","kto"}`, add `beta` to the forwarded training
  keys (method-gated to dpo/kto), and method-gate the SFT-only run-control flags
  (§(b)). `seed` is already forwarded. PLUS narrowly-scoped LoRA flag parity in the
  two trainers (`--lora-*`, §(b)): the DPO/KTO trainers accept the hyperparameter
  flags the builder emits (`train_dpo.py:195-226`) but NOT the LoRA scalars, which
  are load-bearing for the §5.2 budget control and must therefore be added rather
  than gated. (Seed=0 is honored because the trainer `--seed` guard is `is not
  None`; the trainer `--beta` guards were ALSO hardened from truthy to `is not
  None` in a rev2 ruling -- `train_dpo.py:329`, `train_kto.py:612` -- so an
  explicit beta=0 is forwarded, not silently swapped for the config default. The
  matrix uses beta in {0.05, 0.5} so 0 never arises here, but the hardening keeps
  the no-silent-override provenance discipline uniform with `--seed`.)
- CLOUD (all methods) depend on the cloud config + command-builder fix (coder-cloud
  #32, landed).
The §(d) capability probe is correspondingly symmetric: for a LOCAL cell it checks
the handler dispatches the cell's method and forwards seed (+ beta for dpo/kto);
for a CLOUD cell it checks the cloud config + builder emit `--seed`/`--beta`. There
is no longer any local-DPO/KTO trainer-`--config` path to probe -- that mechanism
is withdrawn.

#### (c) Provenance: per-run records (HANDOFF.md §5 SACROSANCT)

Every launched cell emits a JSON run record to
`experiment/phase1/run_records/<run_id>.json` (repo content, committed) BEFORE the
tuner is invoked (so a crashed run still leaves a record), updated with the outcome
after. (`reference/run-records.md` holds the full schema + the HANDOFF.md §5
provenance discipline.)

```json
{
  "run_id": "qwen3-4b__kto_congruence__lrpanel__lr2.0e-6__seed1",
  "matrix_version": "phase1-v0.3",
  "coordinate": {"arm": "kto_congruence", "size": "4b", "cell_type": "lr_panel",
                 "seed": 1, "override": {"learning_rate": 2.0e-6}},
  "source_recipe": "experiment/phase1/recipes/eh_phase1_qwen3_4b_kto_congruence.yaml",
  "materialized_recipe_sha": "<sha256 of the generated recipe>",
  "method": "kto", "model": "unsloth/Qwen3-4B-bnb-4bit",
  "lane": "cloud",
  "data": {"source_data_file": "experiment/phase1/data/qwen3-4b-instruct/kto_train.jsonl",
           "staged_data_file": null,
           "hf_dataset_name": "<org>/eh-phase1-qwen3-4b-kto",
           "hf_dataset_revision": "<hub commit SHA of the published dataset; cloud cells>"},
  "data_sha256": "<sha256 of the exact training file; local cells>",
  "research_repo_commit": "<git rev-parse HEAD of this repo>",
  "submodule_commit": "<git rev-parse HEAD of synaptic-tuner>",
  "prereq_check": {"datasets_present": true, "leakage_guard_passed": true},
  "launched_at": "<iso8601 utc>",
  "tuner_invocation": ["python","tuner.py","cloud-pipeline","--method","kto","..."],
  "outcome": {"status": "launched|completed|failed", "job_handle": "...",
              "adapter_path": "...", "metrics_path": "...", "verified": false}
}
```

The run record is the provenance spine the paper needs: it ties a result back to
the exact recipe, the exact seed/override, and BOTH commit SHAs (research repo +
submodule), so any run is deterministic and re-runnable. The `verified` flag
follows the paper-1 discipline (set true only when the outcome is checked against
its metrics artifact). `metrics_path` points at the eval harness output (§6.7;
the WS-4 harness is `--config`-driven, so the config materialized per arm points
at the adapter + metrics paths the record references), closing the loop from run
to metric. The records are committed repo content; they are the run manifest for
the released artifacts, independent of the skill packaging.

#### (d) Prerequisite gating (refuse to launch on unmet PROTOCOL §5 prereqs)

Before launching ANY cell, `scripts/check_prereqs.py` (invoked by `run_matrix.py`
and also runnable standalone) asserts the PROTOCOL §5 prerequisites are verifiably
present, and ABORTS the whole matrix (not just the cell) on any failure, with a
clear message naming the missing prereq:

1. **Datasets fetched:** the builder outputs for the cell's arm exist on disk
   (`experiment/phase1/data/<model_tag>/<method>_train.jsonl` and `_dev.jsonl`),
   and the TriviaQA train split that fed the probe is present.
2. **Leakage guard passed:** the `build_manifest.json` (§4.8) records the
   leakage-guard PASS (probe/train set disjoint from Cheng test). The gate
   reads the manifest and refuses to launch if the guard did not pass or is
   absent. This makes the pre-registered leakage invariant a launch-time
   precondition, not just a build-time check.
3. **Cloud lane only:** the submodule is pushed and the research-repo submodule
   pointer matches a pushed SHA (so HF Jobs can check it out); `HF_TOKEN` is
   present in the environment (never written to a recipe or record).
3a. **Cloud cells only -- hub dataset availability (user ruling 2026-06-10):**
   the cloud cell's arm dataset is published and resolvable on the HF hub by
   `dataset.name`. The gate performs a REAL hub query (not a locally-recorded
   "published" flag, which would be an unverifiable provenance assertion the gate
   exists to reject -- mirroring item 2, which reads a real manifest) and pins the
   returned revision SHA. The query goes behind a single mockable resolver seam
   (`check_prereqs.hub_dataset_revision(dataset_name) -> revision_sha | None`, the
   accepted #27 symbol; a real `HfApi().dataset_info(name)` query with
   `huggingface_hub` LAZY-imported INSIDE the function, not at module load) so
   `--check-only` stays import-light and tests monkeypatch that one seam with no
   network. The SAME call serves both
   the skip decision AND provenance: per the user ruling, Phase-1 datasets are
   published publicly via the tuner's dataset-publishing skill; until an arm's
   dataset resolves on the hub, its CLOUD cells SKIP (recorded SKIPPED) -- SAME
   skip-vs-abort semantics as the bridge cells (item 4), NOT a whole-matrix abort.
   The LOCAL lane is unaffected (it stages from local builder output, item 1).
   Item 3a applies ONLY to the Qwen3 cloud cells; the bridge cells are local-only
   (item 4) and never reach this gate. The resolved revision SHA is written into
   the cloud cell's run record (§(c) `hf_dataset_revision`).
4. **Bridge arm only -- LOCAL-LANE ONLY (user ruling 2026-06-10, blocker #30):**
   the vendored Cheng IDK training data (DO-NOT-REDISTRIBUTE: never committed,
   never hub-published per the accepted license-risk containment) and the gated
   Llama-2-7b-chat access are present (the §2 / §9 bridge prerequisites). Because
   the data cannot be hub-published, the bridge cells run on the LOCAL lane only
   (staging the vendored data through `.eh_staging/`) and are NEVER cloud cells, so
   item 3a does not apply to them. If a bridge prerequisite is absent, only the
   bridge cells are skipped (recorded SKIPPED), not the whole matrix, since the
   bridge is validation rather than a core arm.
5. **Per-lane tuner capability probe (§(b.2)):** before launching any cell that
   carries a non-default seed or beta override (i.e. every headline and beta-panel
   cell), the gate asserts the resolved tuner forwards the override on the EXACT
   path that cell will use. Under the handler-extension resolution the probe is
   SYMMETRIC across methods within a lane:
   - **LOCAL cell (any method sft/dpo/kto):** `tuner.py local-run` dispatches the
     cell's `run.method` (the guard was widened past SFT-only) and its command
     builder forwards `seed` for all methods and `beta` for dpo/kto. The probe
     checks the resolved handler accepts the cell's method and forwards seed
     (+ beta for dpo/kto) -- e.g. by inspecting the handler's dispatch + forwarding
     surface in the pinned submodule. **For a LOCAL DPO/KTO cell the probe ALSO
     asserts LoRA flag parity** (`train_dpo.py` / `train_kto.py` accept `--lora-r`/
     `--lora-alpha`/`--lora-dropout`/`--lora-target-modules`/`--init-lora-weights`,
     the §(b) load-bearing-flag fix). Without parity the builder's LoRA emissions
     would crash argparse, or (if the builder gated them instead) the recipe's
     `lora:` block would be silently ignored in favor of the trainer's sibling
     `config.yaml` -- corrupting the §5.2 budget control at 8B. This is the same
     whole-matrix-abort class as the seed/beta sink: a missing LoRA sink silently
     mistrains every local DPO/KTO arm.
   - **CLOUD cell (any method):** `CloudTrainingConfig` + the command-builder emit
     `--seed`/`--beta` (coder-cloud #32, landed).
   If the path a cell needs has NOT landed in the pinned submodule, the gate
   ABORTS the whole matrix with a message naming the missing capability and the
   lane it gates, rather than silently launching cells at the default seed/beta.
   This is a whole-matrix abort (not a cell skip), because a missing seed/beta
   sink corrupts the ENTIRE headline + panel design (every headline seed identical,
   every beta-panel cell at the 0.1 default), not one arm.

Gating is deterministic and side-effect-free (it reads, it does not fetch). A
`--check-only` flag runs the gate and reports without launching.

#### (e) Invoking the tuner without polluting it

The single rule: the skill's scripts communicate with the tuner ONLY through
(1) the recipe YAML they materialize (the tuner's own native job-config schema)
and (2) the tuner's existing public CLI verbs. They import NO tuner internals, add
NO COMMITTED SOURCE file under `synaptic-tuner/`, and register NO
experiment-specific method or config there. The DPO method registration (WS-3)
already lives in the tuner as a GENERAL capability (the tuner now supports DPO for
any user), not as anything Epistemic-Humility-specific; the skill merely uses it.
If the skill needs a tuner behavior the CLI does not expose, the correct move is to
flag it (it likely indicates the tuner is missing a general capability), NOT to
reach into tuner internals from the research repo. This keeps the dependency
boundary clean and the tuner reusable by other projects, per the user directive.
SKILL.md's CLI Discipline section encodes this rule as a runbook non-negotiable so
any agent loading the skill inherits it.

The one permitted touch of the submodule working tree is the EPHEMERAL local-lane
data staging (§(b.1)): `run_matrix.py` copies per-cell training data into a
gitignored `synaptic-tuner/.eh_staging/<run_id>/` scratch dir so the tuner
container (which mounts only the tuner repo root) can see it. This is scratch, not
source: it is never committed, adds no behavior to the tuner, and is the same class
of artifact as any build output under a checkout. The single committed tuner-tree
change WS-5 implies is one `.gitignore` line for `.eh_staging/` -- a gitignore
entry, not code, and arguably belongs in the tuner's own ignore rules as generic
scratch hygiene. If even that gitignore line is judged out of bounds, the
fallback is to stage into a tuner-root-relative path the tuner already ignores
(e.g. under an existing scratch/output dir); the implementer should confirm the
exact staging location against the tuner's `.gitignore` at CODE time.

#### S2 boundary and contract impact

WS-5 is a research-repo-only workstream. Its owned surfaces are the skill package
`.claude/skills/experiment-runner/` (runbook + scripts + config + reference) and
the repo content it operates on: `experiment/phase1/recipes/` (relocated by
task #24, now completed) and `experiment/phase1/run_records/` (provenance, new).
It changes NO WS-1/WS-2/WS-3/WS-4 interface contract: it consumes the WS-2 builder
outputs and `build_manifest.json` (read-only), produces materialized recipes + run
records, and its run-id tagging is the coordinate the WS-4 eval harness already
needs for layer-2 aggregation (§6.6). The only cross-workstream dependency is
ordering: WS-5 real launches gate on WS-2 data present, WS-3 DPO pushed (cloud
lane), and PROTOCOL v0.3 user sign-off (already obtained). The matrix-expansion
and gate scripts are testable against fixtures (a tiny matrix.yaml + a stub recipe
+ `--dry-run` / `--check-only`) without any real training, so the skill's logic is
unit-testable independent of the runbook prose.

### 9.3 ADR: `enable_thinking=False` enforcement map (hybrid Qwen3 pin)

PROTOCOL.md:193 pins thinking mode OFF for the Phase-1 model pair. The pin became
load-bearing when the model names were repointed (task #42) from the dead
`unsloth/Qwen3-{4B,8B}-Instruct-bnb-4bit` repos to the hybrid
`unsloth/Qwen3-{4B,8B}-bnb-4bit` pair: the `-Instruct` variants defaulted thinking
OFF, whereas the hybrid models default thinking ON, so `enable_thinking=False` now
has to be actively enforced rather than inherited. This ADR records the enforcement
disposition per method, verified by EXECUTION against the live Qwen3-0.6B chat
template (tester #49, `RUN_LIVE_HUB=1`, the same template family as the 4B/8B
hybrids; this supersedes the architect's earlier cached-template reading in #43,
which was empirically refuted on one mechanism point — see below).

Template mechanism (the fact the disposition rests on — CORRECTED against the live
template): the live Qwen3 template injects the empty think-off marker
`<think>\n\n</think>\n\n` (inner content literally `\n\n`, NOT populated reasoning)
into the assistant turn UNCONDITIONALLY at the generation-prompt position — the
render is byte-identical for `enable_thinking=False`, `=True`, and the no-kwarg
default. (The cached-template reading that a completed assistant turn "renders clean
unless it carries `reasoning_content` or `</think>`" does NOT hold live; the marker
is always present.) The disposition SURVIVES this correction because, on every
template-invoking method, the marker is the empty thinking-OFF SIGNATURE (not
reasoning content) and lands in a **non-loss-bearing** position — and on the one
method that never invokes the template (KTO), no marker is emitted at all:

- For SFT, the marker sits in the MASKED prompt prefix. `materialize_sft_example`
  computes the prompt-only render (`add_generation_prompt=True`, carrying the same
  marker at the same position) and masks the matching prefix to `-100`
  (`shared/sft_preprocessing.py:158-162`). The unmasked training target decodes to
  exactly `I don't know.<|im_end|>\n` (tester-verified by execution) — the marker is
  NEVER a training target, so the model is never trained to emit reasoning.
- For DPO, TRL templates the conversational prompt and the marker lands at the
  prompt boundary, never in the `chosen`/`rejected` completions the preference loss
  shapes (see the per-method map below).
- For KTO, the trainer is fed raw strings and never invokes the chat template, so
  no marker exists on either the train or eval side of the KTO path.
- For SFT and DPO, the train-time prompt and the eval-time prompt both carry the
  identical marker at the identical position, so there is no train/eval prompt
  mismatch; for KTO neither side carries a marker, so there is likewise nothing to
  mismatch.

The empty marker being present (where the template is invoked) is therefore the
EXPECTED thinking-off signature, not contamination; its absence on the KTO
raw-string path is equally benign.

Enforcement map per method:

| Surface | Disposition | Mechanism |
|---------|-------------|-----------|
| **SFT** (train) | Generic config-driven passthrough | `chat_template_kwargs: {enable_thinking: false}` carried by the SFT recipes, threaded through `shared/sft_preprocessing.py` into both `apply_chat_template` calls (coder-cloud #45). No Qwen3 string in shared infra; the kwarg is model-agnostic. |
| **DPO** (train) | **Document-and-accept, no code change** | The DPO loader feeds TRL the CONVERSATIONAL `prompt`/`chosen`/`rejected` message-list schema (`Trainers/dpo/src/data_loader.py:6-16,:24`). TRL templates the prompt with `add_generation_prompt=True`, so the unconditional empty marker lands at the PROMPT/completion boundary (the generation-prompt position), NOT inside `chosen`/`rejected`. The completions — the text the DPO preference loss actually shapes — are the clean IDK strings (gold answer / abstention), carrying no reasoning. The marker is the empty thinking-OFF signature (`\n\n` inner), so no thinking *behavior* is ever trained; train and eval prompts carry it identically. Thinking-free by construction. |
| **KTO** (train) | **Document-and-accept, no code change** | Distinct from DPO: the implemented KTO loader transforms the WS-2 ChatML (`conversations` + `label`) into RAW-STRING `prompt`/`completion`, extracted directly from message `content` (`Trainers/kto/src/data_loader.py:185-189`), and hands those raw strings to TRL. TRL never applies `tokenizer.chat_template` to raw strings, so for KTO **no Qwen3 template is invoked at train time and NO marker is injected anywhere** — the empty-marker question is N/A for KTO. The only `apply_chat_template` calls on the KTO path are inference-only (`Trainers/kto/src/inference.py:82,142`), not training. The trained completion is therefore the literal IDK target string the WS-2 builder placed in the assistant `content` (`experiment/phase1/data/build_datasets.py:421-429`), consistent with the SFT/DPO targets; with no marker on either side of the KTO train path, there is no train/eval marker mismatch to reconcile. |
| **Eval / probe** (inference) | Already pinned | `experiment/phase1/eval/config/eval.yaml:18` and `experiment/phase1/probe/config/probe.yaml:28` pin `enable_thinking: false`; the probe has a runtime self-check (`test_probe_smoke.py:109` raises if not honored). |

Why KTO/DPO is document-and-accept rather than code: forcing think-off at the
tokenizer-template level (wrapping `chat_template` / `get_chat_template`) is the
**rejected alternative** — it would require Qwen3-specific logic in shared
model-load infra (violating tuner generality), risk altering the template for
non-Qwen models, and (for DPO) suppress an empty marker that is HARMLESS where it
lands. The contamination that would actually matter — populated reasoning in the
trained completion — does not exist on either path, for two DIFFERENT reasons:
for **DPO**, TRL does template the prompt (the empty `\n\n` thinking-OFF marker
lands at the prompt boundary, never in the `chosen`/`rejected` completions, which
are clean IDK strings); for **KTO**, TRL never templates at all (raw-string
`prompt`/`completion`), so no marker is emitted anywhere and the trained completion
is the clean IDK string verbatim. PROTOCOL.md:193 is satisfied for both because the
train-time behavior is thinking-off by construction *and* eval-time is thinking-off
by the eval-config pin — no template surgery, no protocol revision. The per-recipe
note in the four dpo/kto recipes records this as a deliberate, evidenced disposition
(not an omission) and cites this ADR.

Forward obligation (eval consistency): the post-sign-off `VLLMGenerator` real
path in `experiment/phase1/eval/run_eval.py` (currently a stub, ~:111) MUST pass
`enable_thinking=False` (or `chat_template_kwargs={enable_thinking: false}`) into
its `apply_chat_template` / vLLM chat call when implemented, with a self-check test
mirroring the probe's so eval cannot silently regress. This obligation is tracked
as pending task #47 (owner coder-eval). Train-side (the SFT prompt-prefix marker,
masked to `-100` at `shared/sft_preprocessing.py:158-162`) and eval-side (the marker
at the generation prompt) both carry the identical think-off marker at the same
position, so there is no train/eval prompt mismatch.

**Scope limit:** this ruling holds for the **hybrid pair only**. A future
Qwen3-Thinking-only variant always thinks, so document-and-accept for KTO/DPO
would no longer hold and the enforcement map would have to be revisited — at which
point PROTOCOL.md:193's pin would need an explicit code-level enforcement decision
for those trainers.

---

## 10. Non-functional requirements

- **Provenance (SACROSANCT, HANDOFF §5):** every artifact carries a manifest
  with config SHA, source, and (for data) a `dataset.md`-style stanza. Scorers
  deterministic; no hand-edited results; outputs committed.
- **Reproducibility / Phase 4:** the config-driven design means a new model is a
  `model_tag` + `model_name` swap. Release adapters, per-model labels
  (`probe_results.jsonl`), and outputs to HF Hub (the field's documented gap).
- **Resumability:** probe and eval are checkpointed/resumable (append-log keyed
  by question_id) so long local runs survive interruption.
- **Cost:** probe ≈ train-split-size × 33 gens on 4B local; eval ≈ adapters ×
  eval-set-size gens. Both batched on vLLM. The 8B confirm arm is the cloud
  cost; the 4B pilot is the local-iteration loop.
- **Determinism vs sampling:** the probe is intentionally stochastic (P_correct
  needs samples) but seeded; eval generations are seeded; all statistics are
  computed from committed raw generations so re-running stats is deterministic.
- **Security:** no credentials in configs; `HF_TOKEN` passed via env for gated
  Llama-2 and HF Jobs, never written to a recipe. Llama-2 license acceptance is
  a user action recorded in the bridge recipe's provenance note.

---

## 11. Gap disposition table (PREPARE gaps #1-#7)

| # | Gap | Disposition |
|---|---|---|
| 1 | No DPO trainer | BUILD `Trainers/dpo/` mirroring KTO (TRL DPOTrainer) + register method at 4 sites — WS-3 (§5.4, §5.5) |
| 2 | TriviaQA pool < 20k | Use the rc.nocontext **train** split (fetch) as probe/train; documented validation-remainder fallback — WS-0/WS-1 (§3.2) |
| 3 | Probe/Cheng-test leakage | Disjoint train-split design + pre-registered, builder-enforced leakage guard — WS-2 (§3.2, §4.2) |
| 4 | Cheng IDK training data not on disk | Recorded CODE prerequisite: fetch OpenMOSS Say-I-Dont-Know training data (license-gated, user sign-off) — WS-0 note (§2, §9) |
| 5 | Llama-2-7b-chat gated + no preset | Bridge recipes use `--model-name` override + recorded license acceptance; HF_TOKEN via env — WS-3 (§5.6) |
| 6 | Metric scorers not pre-built | Build Phase-1 scorers in research repo `experiment/phase1/eval/`, ported from Cheng reanalysis — WS-4 (§6.2, §6.3) |
| 7 | `Evaluator/recipes/` doc drift | Do not depend on it; use `Evaluator/config/` only if the tuner harness is touched; Phase-1 suite is research-repo native — WS-4 (§6.2) |

---

## 12. Risk assessment

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| DPO method registration misses an enumeration site | Medium | Med (silent cloud failure) | §5.5 names the `paths.py` SSOT + ~10 leaf sites + a mandatory grep-sweep CODE check (the under-count this risk warns about was itself caught by that sweep in CODE) |
| Qwen3 chat template injects `<think>` despite thinking-off intent | Medium | Med (parsing confound) | §5.3 CODE-verify the template path; eval scorer strips any `<think>` defensively |
| Train-split fetch infeasible at CODE time | Low | Med (reduced n) | documented validation-remainder fallback + power caveat (§3.2) |
| Cheng IDK training data license blocks bridge arm | Medium | Med (bridge arm slips) | recorded prerequisite + user sign-off; bridge arm is validation, not a core arm |
| Unknown set too small (Qwen3-4B knows most of TriviaQA) | Medium | Med (thin contrast) | N=32 probe gives a real frontier; if U too small, widen threshold band (sensitivity grid already computes this) or add PopQA long-tail to the probe pool (documented option) |
| Budget cannot equalize across formats | Low | Low | resolved pre-registration: budget = distinct questions, expansion documented (§4.2) |
| Submodule pointer bump forgotten before cloud run | Medium | Low | §5.7 sequencing; HF Jobs checks out the pinned SHA so a stale pointer fails loudly, not silently |

---

## 13. Reasoning chain (key decisions, connected)

1. **Qwen3 pin (text-only, Apache, thinking-off) -> every component pins
   `enable_thinking=False`.** The pin's whole value is removing the
   vision/reasoning confounds; honoring it half-way (e.g. letting the chat
   template inject `<think>`) would reintroduce exactly the parsing confound the
   pin avoids. So thinking-off propagates from probe to builder-templates to
   trainer chat-template to eval-scorer, and is a CODE-verify item where the
   template path is non-obvious.
2. **Three-way requires a DPO path that does not exist -> mirror the TRL KTO
   trainer rather than build a new stack.** KTO already proves TRL + Unsloth +
   the tuner's callbacks/cloud-sync compose; cloning that structure and swapping
   `KTOTrainer/KTOConfig -> DPOTrainer/DPOConfig` (plus a chosen/rejected
   data_loader) is the lowest-risk closure of gap #1 and inherits all the
   operational plumbing for free.
3. **DPO registration is multi-site -> enumerate the sibling pins, do not
   single-line it.** The method set lives at a `paths.py` SSOT plus ~10 leaf
   sites across ~16 files; a single-line add registers DPO for the CLI but fails
   at the cloud backend (or, conversely, updating leaf sites while missing the
   `paths.py` SSOT leaves the trainer-dir/output-dir dispatch wrong). Updating
   the SSOT first (it auto-derives the dir maps) and grep-sweeping the leaves
   prevents a mid-implementation surprise where the 8B cloud arm fails after the
   local arm worked. The CODE-phase grep sweep corrected this section's original
   4-site estimate to the true surface, which is exactly the failure mode the
   sweep mandate exists to catch.
4. **Probe pool overlaps the Cheng test set -> move probing/training to a
   disjoint train split and pre-register a builder-enforced leakage guard.**
   Keeping Cheng's 11,313 as the held-out test makes the bridge arm directly
   comparable to published numbers; probing/training on the disjoint train split
   removes leakage; the guard makes the invariant checkable and the
   validation-remainder fallback makes the design robust to a failed fetch.
5. **Method-native formats expand questions differently -> define budget as
   distinct source questions and freeze the question set once.** This keeps
   "identical data budget across arms" a real confound control (same questions,
   same seed) instead of an illusion that breaks the moment SFT and KTO emit
   different row counts; the expansion is documented, not hidden.
6. **Novel metrics are not in the tuner harness -> build them in the research
   repo, ported from the Cheng-validated reanalysis.** This puts the paper's
   metrics under the paper's provenance discipline and guarantees bridge-arm
   numbers use the exact scorer that already reproduces 42.71% / 23.27%, so a
   bridge mismatch indicts the training pipeline, not the metric.
7. **Style-varied abstention bank must still be machine-detectable -> constrain
   every paraphrase to carry a refusal marker.** This squares the
   anti-overfitting goal (vary the surface form) with the eval requirement
   (detect refusals reliably), so the two requirements do not silently fight.
```
