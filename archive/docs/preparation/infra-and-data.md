# Phase 1 Infrastructure & Data Verification

**Prepared by:** preparer-infra (team pact-6d29f2e2) · **Date:** 2026-06-10
**Scope:** PREPARE phase for Phase 1 (paper 2: SFT vs DPO vs KTO abstention).
**Companion doc:** `docs/preparation/model-landscape.md` (preparer-models — which model to pin). This doc covers whether the *machinery* works.

Every claim below was verified against actual files in the worktree
(`/Users/jrosenbaum/Documents/Code/Epistemic-Humility-Research/.worktrees/phase1-pipeline`);
paths are quoted and row counts / sizes were measured with `wc -l` / `du`.

---

## Executive summary

1. **The three-way design has a hard infra gap: there is no DPO trainer.**
   The synaptic-tuner submodule supports SFT, KTO, and GRPO only. The CLI
   `--method` choices are literally `["sft", "kto", "grpo"]`
   (`synaptic-tuner/tuner/cli/parser.py:222`). There is no `Trainers/dpo/`
   directory, no `train_dpo.py`, no DPO recipe, and no `DPOTrainer` import
   anywhere in the submodule. **Phase 1's SFT/DPO/KTO three-way cannot run
   on the tuner as-is.** This is an ARCHITECT-level decision: build a DPO
   trainer, or drop DPO to a two-way (SFT vs KTO). Flagged prominently in
   §A.4.

2. **The PROTOCOL.md drift is resolved.** `Trainers/rtx3090_kto/train_kto.py`
   (cited by PROTOCOL.md v0.1) no longer exists. The current KTO entry point
   is `synaptic-tuner/Trainers/kto/train_kto.py`. The legacy RTX3090 trainers
   are gone from this submodule snapshot (no `Trainers/rtx3090*`, no
   `Trainers/archive/`).

3. **The local dataset inventory is in good shape for Phase 1.** All ten
   relevant dirs under `datasets/` carry a verified `dataset.md` provenance
   file with source, license, fetch date, and schema. The Cheng gold aliases
   (`datasets/triviaqa-rc-nocontext/cheng_test_gold.jsonl`, **11,313 rows**)
   exactly match the say-i-dont-know test outputs (also 11,313 rows). The OOD
   eval sets (KUQ, CoCoNot, AbstentionBench, MMLU, TruthfulQA, PopQA,
   SelfAware) are all on disk with usable schemas. **One soft gap:** the
   TriviaQA probe pool is `validation.jsonl` at **17,944 rows** — slightly
   below the "~20k probe train subset" target, so the full 20k cannot come
   from this single split alone (see §B).

4. **The Cheng bridge arm is replicable on the eval side now, but needs a
   training-data fetch.** We have Cheng's per-method *test outputs* and gold
   aliases, and `meta-analysis/analysis/reanalyze_idk_outputs.py` already
   reproduces the published over-refusal numbers exactly (Idk-SFT 42.71%,
   Idk-DPO 23.27%, n=11313). But the bridge arm must also *train* Idk-SFT +
   Idk-DPO, and we do **not** have Cheng's IDK *training* set on disk — only
   test outputs. That training data must be fetched from the OpenMOSS repo
   (or regenerated via their recipe). Llama-2-7b-chat is **HF-gated** and has
   no tuner preset (see §C).

---

## A. synaptic-tuner training/eval entry points

Submodule root: `synaptic-tuner/`. Verified against the actual file tree and
`synaptic-tuner/tuner/cli/parser.py`, not from memory. The mandatory skill
`synaptic-tuner/.skills/fine-tuning/SKILL.md` and
`synaptic-tuner/.skills/fine-tuning/reference/dataset-formats.md` were loaded
first per HANDOFF §1.

### A.1 Supported training methods (measured)

| Method | Trainer dir | Entry point | CLI status |
|--------|-------------|-------------|------------|
| **SFT** | `Trainers/sft/` | `Trainers/sft/train_sft.py` (50.8K) | Supported. `--method sft` |
| **KTO** | `Trainers/kto/` | `Trainers/kto/train_kto.py` (42.6K) | Supported. `--method kto` |
| **GRPO** | `Trainers/grpo/` | `Trainers/grpo/train_grpo.py`, `train_env_grpo.py` | Supported. `--method grpo` |
| **DPO** | — | — | **ABSENT — see §A.4** |

Also present: `Trainers/ml/` (LightGBM/tabular, not a fine-tuning method) and
`Trainers/mlx_sft_mac/` (Apple-MLX SFT path).

### A.2 CLI invocations (verified in `tuner/cli/parser.py`)

The top-level command set (`parser.py:144`) includes `train`, `local-run`,
`cloud-run`, `cloud-pipeline`, `cloud-eval`, `cloud-gym`, `run-experiment`,
`plan-hardware`, `cloud-jobs`, `bucket`, `analyze-experiment`, `experiment-loop`,
`surgery`, `eval`, `status`, `doctor`, `list`, and others.

**Local (RTX 3090) paths — the 3B pilot home:**
```bash
# Direct trainer (fast iteration)
cd synaptic-tuner/Trainers/sft && python train_sft.py --model-size 3b --tier quick --dry-run
cd synaptic-tuner/Trainers/kto && python train_kto.py --model-size 7b --local-file ../../Datasets/my_kto.jsonl

# Config-driven local Docker run (repeatable, preferred for GPU)
python tuner.py local-run --job-config Trainers/recipes/<recipe>.yaml --yes
```

**Cloud (HF Jobs) paths — the 7-8B confirm home:**
```bash
python tuner.py cloud-pipeline --method sft --preset full   # train then eval, two HF jobs
python tuner.py run-experiment --experiment-spec Trainers/cloud/experiments/<spec>.yaml --yes  # train -> eval -> loss -> analysis
python tuner.py cloud-eval --run latest --preset full
```
Note: `cloud-pipeline` is a **two-job orchestration** on HF Jobs (train job +
eval job), not a single composite job (SKILL.md "HF Jobs Notes"). HF Jobs
requires launching from a clean tracked worktree on a pushed commit; the remote
container checks out that exact SHA. `HF_TOKEN` must be passed explicitly.

`./run.sh` (18K) is the interactive menu wrapper (`./run.sh status`, `./run.sh
doctor`, `./run.sh list datasets|models|runs`).

### A.3 Model presets and LoRA configs (measured)

**SFT** (`Trainers/sft/train_sft.py:357`): `--model-size` choices
`["3b","7b","13b","20b"]`. The default `model_name` in
`Trainers/sft/configs/config.yaml:14` is currently `unsloth/LFM2.5-1.2B-Instruct`
(a smoke-test default — override per run). Comments document the tier menu:
3B → `unsloth/Qwen2.5-3B-Instruct-bnb-4bit` / `unsloth/Llama-3.2-3B-Instruct-bnb-4bit`;
7B → `unsloth/mistral-7b-v0.3-bnb-4bit` / `unsloth/llama-3.1-8b-instruct-bnb-4bit`.

**KTO** (`Trainers/kto/train_kto.py`): both `--model-size` (`["3b","7b","13b","20b",None]`,
line 190) and named flags. The flag→HF-repo map (lines 420-441) includes the
Phase-1-relevant entries:

| Flag | Size | HF repo |
|------|------|---------|
| `--qwen-3b` | 3b | `unsloth/Qwen2.5-3B-Instruct-bnb-4bit` |
| `--qwen-7b` | 7b | `unsloth/Qwen2.5-7B-Instruct-bnb-4bit` |
| `--llama-3b` | 3b | `unsloth/Llama-3.2-3B-Instruct-bnb-4bit` |
| `--llama-8b` | 7b | `unsloth/llama-3.1-8b-instruct-bnb-4bit` |
| `--mistral-7b` | 7b | `unsloth/mistral-7b-v0.3-bnb-4bit` |
| `--llama-13b` | 13b | `unsloth/llama-2-13b-bnb-4bit` (base, not chat) |

`--model-name` overrides with any HF repo (e.g. for the bridge arm). Note the
repo tooling currently targets **Qwen2.5-3B/7B**, matching research-trajectory.md
§Model strategy; preparer-models owns whether to substitute a newer generation.

**LoRA / complexity tiers** (SKILL.md "Complexity Tiers"): `--tier quick`
(r=8, lr=5e-4), `standard` (r=64, lr=2e-4), `thorough` (r=128, lr=1e-4). Both
local trainers also expose `--lora-r`, `--lora-alpha`, `--lora-dropout`,
`--use-dora`, `--use-rslora`, `--init-lora-weights` for hand-tuning. The cloud
surface forwards these as `--train-lora-*`. For an identical LoRA budget across
arms (required by the Phase-1 design), pin r/alpha/dropout explicitly rather
than relying on `--tier`.

### A.4 ⚠️ DPO support status: ABSENT (prominent gap)

**There is no DPO training path in the tuner.** Verified:
- CLI `--method` choices are exactly `["sft", "kto", "grpo"]`
  (`tuner/cli/parser.py:222`); parser help strings throughout say
  "Training workflows (SFT, KTO, GRPO)".
- No `Trainers/dpo/` directory; trainer dirs are `sft`, `kto`, `grpo`, `ml`,
  `mlx_sft_mac`, `cloud`.
- No `train_dpo.py` anywhere in the submodule.
- No recipe declares `method: dpo` (`Trainers/recipes/*.yaml` use sft/kto/grpo/gguf).
- The only whole-word "dpo" hit in tracked code is
  `tests/cloud/test_hf_jobs_backend.py:160` (`backend.load_config("dpo")`),
  which is a test exercising an *unknown* method, not a trainer.
- The SKILL.md "Training Methods at a Glance" and recommended pipeline are
  SFT → KTO → GRPO; DPO is never mentioned.

**Implication for Phase 1:** research-trajectory.md §"Phase 1 — the three-way"
requires SFT vs DPO vs KTO on the same base model and data budget. **The DPO
arm has no runnable path today.** Two options for ARCHITECT/the user:
- **(a) Build a DPO trainer.** TRL ships `DPOTrainer`; KTO already uses TRL
  (`Trainers/kto/`), so a `Trainers/dpo/train_dpo.py` modeled on the KTO
  trainer is feasible new scope. The DPO dataset is preference *pairs*
  (chosen/rejected), distinct from KTO's interleaved binary labels.
- **(b) Drop to a two-way** (SFT vs KTO), making DPO a bridge-arm-only
  replication (Cheng's Idk-DPO) rather than a novel modern-model arm.

This is a design/scope decision, not something this PREPARE doc resolves. PROTOCOL.md
v0.1 already treated DPO as "optional" — the trajectory upgraded it to required,
and the machinery has not caught up.

### A.5 Evaluation capabilities (`Evaluator/`)

`synaptic-tuner/Evaluator/` is a config-first eval harness (CLI in
`Evaluator/cli.py`, 40K). Scenarios are YAML under `Evaluator/config/scenarios/`;
presets live in `Evaluator/config/eval_run.yaml` (`presets:` block at line 134,
e.g. `quick`, `full`). **Relevant to Phase 1:** an epistemic-humility eval
scenario already exists —
`Evaluator/config/scenarios/labkit_epistemic_humility_smoke.yaml` (4.9K).

Cloud eval runs via `python tuner.py cloud-eval --run latest --preset full` or
as the second job of `cloud-pipeline`. The eval default backend is vLLM
(`evaluation.runtime: vllm`, `image_profile: fast_vllm` per SKILL.md).

**Drift note:** SKILL.md "Key Directories" references `Evaluator/recipes/` for
"unified evaluation recipe configs", but that directory does **not** exist in
this snapshot. Eval configuration is under `Evaluator/config/` (scenarios +
`eval_run.yaml` presets). The harness is custom YAML-assertion based; the
Phase-1 metric suite (refusal recall / over-refusal decomposition, truthful
rate, token ECE, OOD subsets) will need new scenario configs + likely a custom
scorer — none of those specific metrics are pre-built. This is CODE-phase work,
flagged here so ARCHITECT can scope it.

### A.6 Local RTX 3090 vs HF Jobs (summary)

| | Local (RTX 3090) | HF Jobs (cloud) |
|---|---|---|
| Entry | `train_*.py` direct, or `tuner.py local-run` | `tuner.py cloud-pipeline` / `run-experiment` |
| Role per HANDOFF | 3B pilot, fast iteration | 7-8B confirm |
| Output | `{method}_output/<ts>/` | `runs/hf_jobs/{method}/<ts>-<sha>/` (HF Bucket) |
| Preconditions | local GPU + Docker | clean tracked worktree, pushed commit, `HF_TOKEN` |

---

## B. Local dataset inventory (measured)

Root: `datasets/`. All ten Phase-1-relevant dirs carry a `dataset.md` (provenance
**present and verified** for every one). Row counts via `wc -l`, sizes via `du`.

| Dir | Key file(s) | Rows (measured) | Size | `dataset.md` | Phase-1 role |
|-----|-------------|-----------------|------|--------------|--------------|
| `triviaqa-rc-nocontext` | `validation.jsonl` | **17,944** | 19.4M | yes | probe pool + in-domain train/eval |
| | `cheng_test_gold.jsonl` | **11,313** | 8.2M | yes | Cheng test gold aliases (exact grading) |
| `popqa` | `test.jsonl` | 14,267 | 8.0M | yes | OOD: long-tail knowledge boundary |
| `mmlu` | `test.jsonl` | 14,042 | 7.2M | yes | OOD + **token ECE** (has `choices`+`answer`) |
| | `validation.jsonl` | 1,531 | 803K | yes | |
| `truthfulqa` | `TruthfulQA.csv` | 817 (rows) | 492K | yes | eval (truthful rate) |
| `kuq` | `knowns_unknowns.jsonl` | 6,884 | 2.3M | yes | OOD: unanswerable detection (has `unknown` bool) |
| | `unknowns_all.jsonl` | 6,363 | 5.1M | yes | categorized unknowns |
| `coconot` | `contrast_test.jsonl` | 379 | 68K | yes | OOD: **over-refusal** headline probe |
| | `original_test.jsonl` | 1,001 | 204K | yes | noncompliance recall |
| | `original_train.jsonl` | 11,477 | 6.5M | yes | candidate KTO-negative source |
| `say-i-dont-know-outputs` | 5× method JSON | 11,313 each | 47M | yes | Cheng test outputs (bridge eval) |
| `selfaware` | `SelfAware.json` | 3,369 (Q) | 1.2M | yes | OOD: answerable/unanswerable |
| `abstentionbench-repo` | `data.py`, indices | — | 284K | yes | AbstentionBench loader + subsample indices |
| `abstentionbench-results` | `abstention_performance.csv` | 624 | 65K | yes | OOD reanalysis (precision/recall/F1) |

### B.1 Schemas (spot-checked, first row of each)

- `triviaqa validation.jsonl`: `question, question_id, question_source, entity_pages, search_results, answer` — `answer` carries aliases; usable as probe pool.
- `cheng_test_gold.jsonl`: `question_norm, tqa_question_id, source_split, answer_value, aliases, normalized_aliases` — joins to outputs via normalized question text.
- `say-i-dont-know …idk_sft.json`: list of 11,313 dicts `{question_id, question, answer, generated_answer}` where `answer` is the IDK training target (encodes known/unknown), `generated_answer` is the model output.
- `popqa test.jsonl`: `question, possible_answers, s_pop, o_pop, …` (popularity-scored).
- `mmlu test.jsonl`: `question, subject, choices, answer` — MCQ, supports token-level ECE.
- `kuq knowns_unknowns.jsonl`: `question, answer, unknown, source, category` — `unknown` is a boolean label.
- `coconot contrast_test.jsonl`: `id, category, subcategory, prompt, response`.

### B.2 Are Phase-1 design needs satisfiable from disk?

| Need (HANDOFF §2 / research-trajectory) | On disk? | Notes |
|---|---|---|
| Probe train subset ~20k (TriviaQA) | **Partial** | `validation.jsonl` is 17,944 rows — ~2k short of 20k. Either accept ~18k, or pull an additional TriviaQA split (rc.nocontext train) via `datasets/scripts/fetch_datasets.py`. **Flag for ARCHITECT.** |
| Held-out test (Cheng's set) | **Yes** | `cheng_test_gold.jsonl` (11,313) + the 5 method outputs. Note: probe-pool `validation.jsonl` and Cheng test gold are both drawn from TriviaQA validation — ensure the ~18k probe subset is **disjoint** from the 11,313 Cheng test questions to avoid train/test leakage. **Flag for ARCHITECT.** |
| Cheng gold aliases | **Yes** | `datasets/triviaqa-rc-nocontext/cheng_test_gold.jsonl`, exactly as referenced. |
| OOD eval subsets (KUQ, CoCoNot, AbstentionBench) | **Yes** | All present with usable schemas. CoCoNot `contrast_test` (over-refusal) and KUQ `knowns_unknowns` (labeled) are the headline OOD probes. |
| MMLU for token ECE | **Yes** | `mmlu/test.jsonl` (14,042) has `choices`+`answer`. |
| TruthfulQA | **Yes** | 817 questions. |

**Fetch gaps (record only, do not re-fetch this phase per guidelines):**
- CoCoNot `pref` split (preference pairs) is **not** downloaded — the
  `dataset.md` notes "add to fetch_datasets.py if the KTO arm wants it". Needed
  only if CoCoNot pairs feed a KTO-negative source.
- An additional TriviaQA split if the full 20k probe subset is wanted disjoint
  from the Cheng test set.
- Gitignored large binaries (library pdfs 273M, fulltext 38M) are re-fetchable
  via `library/scripts/fetch_library.py --enrich` (HANDOFF §5) — not needed for
  Phase-1 training/eval.

No `dataset.md`-vs-measured discrepancies found: every stated size matches the
measured rows (e.g. KUQ states "6,884 + 6,363", measured 6,884 + 6,363; TriviaQA
states "17,944 + 11,313", measured 17,944 + 11,313).

---

## C. Cheng et al. bridge-arm replication requirements

Anchor: Cheng et al., "Can AI Assistants Know What They Don't Know?" (arXiv
2401.13275, ICML 2024), model **Llama-2-7b-chat**, dataset OpenMOSS
Say-I-Dont-Know.

### C.1 Published numbers we replicate against (verified, read-only)

From `meta-analysis/evidence/effects.csv` (our EXACT reanalysis of the authors'
released outputs, n=11,313, computed by `analysis/reanalyze_idk_outputs.py`):

| Metric (on TriviaQA-Idk, n=11313) | Idk-SFT | Idk-DPO | Source |
|---|---|---|---|
| Over-refusal on known (%) | **42.71** | **23.27** | effects.csv:21 |
| Refusal recall on unknown (%) | 84.06 | 71.19 | effects.csv:22 |
| (also: PPO over-refusal 30.86, BoN 25.64) | | | effects.csv:23-24 |

Per-method full table in `meta-analysis/evidence/idk-method-reanalysis.csv`
(Idk-SFT row: refusal_recall 84.06, over_refusal 42.71, truthful 70.3). These
are the targets the bridge arm validates the pipeline against (HANDOFF §3:
"Idk-SFT 42.7% over-refusal, DPO 23.3%" — confirmed to two decimals).

### C.2 What the replication needs

**Eval side (have it now):** `reanalyze_idk_outputs.py` already reproduces these
numbers. Its mechanics (for porting into the Phase-1 harness):
- Refusal detection: substring match on 4 markers ("beyond the scope of my
  knowledge", "i am not sure what the answer is", "i don't know the answer",
  "i do not know the answer") — script lines 48-57.
- Known/unknown label: encoded in the IDK training *target* (`answer` field);
  a target that is a refusal template ⇒ unknown-labeled.
- Correctness: word-bounded normalized gold-alias match against
  `cheng_test_gold.jsonl` (lines 86-88).

**Train side (the GAP):** the bridge arm must *train* Idk-SFT + Idk-DPO on
Llama-2-7b-chat. We have Cheng's **test outputs only** — there is **no IDK
*training* set on disk** (`find datasets -iname "*idk*train*"` → nothing; the
say-i-dont-know-outputs dir holds the 5 test-output files). To run the bridge
arm we need either:
- the OpenMOSS Say-I-Dont-Know **training data** (Idk-SFT corpus + DPO
  preference pairs), fetched from `https://github.com/OpenMOSS/Say-I-Dont-Know`, or
- regeneration via their recipe (correctness-probe Llama-2-7b-chat on TriviaQA
  train → build known/unknown splits → SFT/DPO targets). research-trajectory.md
  §"Dataset strategy" explicitly says reuse the Cheng *recipe*, not their labels.

The IDK refusal *template* itself is recoverable from the test outputs (the
`answer` field on unknown-labeled rows) — e.g. "This question is beyond the
scope of my knowledge…".

**License note (provenance, SACROSANCT):** `say-i-dont-know-outputs/dataset.md`
states license "unstated — analysis use only, do not redistribute as training
data." The released *outputs* are for analysis; sourcing actual *training* data
must respect the OpenMOSS repo's own license terms. Flag for the user before
fetching/redistributing.

### C.3 Is Llama-2-7b-chat gated on HF? — YES

- `meta-llama/Llama-2-7b-chat-hf` is **gated** on the HF hub (requires
  accepting Meta's Llama-2 community license and an authenticated `HF_TOKEN`
  with access granted). This is a known hub state for all `meta-llama/Llama-2-*`
  repos.
- **No tuner preset targets Llama-2-7b-chat.** The only Llama-2 entry in the
  tuner is `unsloth/llama-2-13b-bnb-4bit` (KTO map, `train_kto.py:433`) — a
  **13B base** model, not the 7B chat model. `unsloth/llama-2-7b` is referenced
  in `synaptic-tuner/docs/prep/UNSLOTH_WINDOWS_INSTALLATION_GUIDE.md` but that
  is the **base** 7B, not `-chat`.
- The bridge arm therefore needs an explicit `--model-name` override pointing
  at either the gated `meta-llama/Llama-2-7b-chat-hf` (after license acceptance
  + token) or an ungated community/unsloth mirror of Llama-2-7b-**chat**.
  Verify the exact chat repo is available and ungated before committing the
  bridge arm to the protocol. **Flag for ARCHITECT/user.**

---

## D. Consolidated gaps & flags for ARCHITECT

| # | Gap / risk | Severity | Action owner |
|---|---|---|---|
| 1 | **No DPO trainer** — three-way design unrunnable as-is | **HIGH** | ARCHITECT/user: build `Trainers/dpo/` (TRL DPOTrainer) or drop to two-way |
| 2 | TriviaQA probe pool is 17,944 rows (< 20k target) | MED | ARCHITECT: accept ~18k or fetch extra TriviaQA split |
| 3 | Probe pool and Cheng test set both from TriviaQA validation → leakage risk | MED | ARCHITECT: enforce disjoint probe-vs-test split |
| 4 | Cheng IDK *training* data not on disk (only test outputs) | MED | CODE/user: fetch from OpenMOSS repo or regenerate via recipe (license-gated) |
| 5 | Llama-2-7b-chat HF-gated + no tuner preset | MED | user: accept Meta license / pick ungated mirror; ARCHITECT: `--model-name` override |
| 6 | Phase-1 metric suite (over-refusal decomp, token ECE, OOD scorers) not pre-built in `Evaluator/` | MED | CODE: new eval scenarios + custom scorer |
| 7 | SKILL.md references `Evaluator/recipes/` which doesn't exist | LOW | doc drift only; use `Evaluator/config/` |

---

## E. Verification provenance

- Tuner skill loaded first: `synaptic-tuner/.skills/fine-tuning/SKILL.md`,
  `.../reference/dataset-formats.md` (HANDOFF §1).
- DPO absence: `grep` of `tuner/cli/parser.py:222` (`--method` choices),
  trainer-dir `ls`, whole-word `dpo` search across `*.py`/`*.yaml`.
- Dataset rows: `wc -l` on each JSONL; JSON outputs counted via `json.load` len.
- Sizes: `du -sh` per dir/file.
- Cheng numbers: read-only from `meta-analysis/evidence/effects.csv`,
  `idk-method-reanalysis.csv`, `analysis/reanalyze_idk_outputs.py`. **Nothing
  under `meta-analysis/` was modified.**
- No `CLAUDE.md` created or edited.
