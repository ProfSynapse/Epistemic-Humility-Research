# Phase 1 Training Recipes

These nine `eh_*` recipe YAMLs are **experiment-specific** orchestration for the
Phase 1 abstention study (paper 2: SFT vs DPO vs KTO). They live in the research
repo — **not** in the `synaptic-tuner` submodule — because the tuner is a fully
general training tool; everything specific to this experiment belongs here.

They are consumed **against the tuner submodule as a dependency**: the trainers,
method registration, and model presets they invoke (`Trainers/dpo`,
`Trainers/kto`, `Trainers/sft`, `--qwen3-4b`/`--qwen3-8b`) live in
`synaptic-tuner/`. The recipes themselves are pinned here so the tuner stays
generic and reusable.

## Recipe inventory

| Recipe | Arm | Model | Provider |
|--------|-----|-------|----------|
| `eh_phase1_qwen3_4b_sft.yaml` | SFT | Qwen3-4B-Instruct | local_docker |
| `eh_phase1_qwen3_4b_dpo.yaml` | DPO | Qwen3-4B-Instruct | local_docker |
| `eh_phase1_qwen3_4b_kto_congruence.yaml` | KTO (congruence, primary) | Qwen3-4B-Instruct | local_docker |
| `eh_phase1_qwen3_4b_kto_correctness_safe.yaml` | KTO (correctness-safe, ablation) | Qwen3-4B-Instruct | local_docker |
| `eh_phase1_qwen3_8b_sft.yaml` | SFT | Qwen3-8B-Instruct | hf_jobs |
| `eh_phase1_qwen3_8b_dpo.yaml` | DPO | Qwen3-8B-Instruct | hf_jobs |
| `eh_phase1_qwen3_8b_kto_congruence.yaml` | KTO (congruence) | Qwen3-8B-Instruct | hf_jobs |
| `eh_bridge_llama2_7b_chat_sft.yaml` | BRIDGE Idk-SFT replication | meta-llama/Llama-2-7b-chat-hf (gated) | hf_jobs |
| `eh_bridge_llama2_7b_chat_dpo.yaml` | BRIDGE Idk-DPO replication | meta-llama/Llama-2-7b-chat-hf (gated) | hf_jobs |

The 4B arms share LoRA budget r=32/alpha=64; the 8B arms share r=64/alpha=128;
the bridge arms use r=32/alpha=64. Within a model size, the SFT/DPO/KTO arms
differ only in training objective, not in capacity — the LoRA surface is held
identical across arms by design.

## Path contract (read before running)

These recipes were authored when they lived inside the tuner and assumed a
single `/workspace/repo` that contained both the trainers and the dataset tree.
Now that they live in the research repo while the data also lives in the
research repo (`experiment/phase1/data/...`) and the trainers live in the tuner
submodule, two distinct roots exist and must be resolved by the **WS-5
experiment runner** (research repo):

- **`dataset.local_file`** — research-repo-relative, e.g.
  `experiment/phase1/data/qwen3-4b-instruct/dpo_train.jsonl`. Built by the WS-2
  dataset builders (`experiment/phase1/data/build_datasets.py`).

- **`run.command`** (local 4B pilots only) — uses two placeholder variables the
  WS-5 runner substitutes before invocation:
  - `{tuner_root}` — the `synaptic-tuner` trainer root inside the run
    environment. Under the tuner's `local_docker` backend this is the tuner repo
    root mounted at `/workspace/repo`; the runner resolves the concrete value.
  - `{data_root}` — where the research-repo `experiment/phase1/data` tree is made
    available to the run environment. The WS-5 runner owns the mount/stage
    strategy that binds this research-repo path into the container.

The 8B and bridge recipes use the tuner's declarative `run.method`/`run.trainer`
form (no explicit `run.command`); for those, only `dataset.local_file` matters
and the tuner's own runner translates the repo-relative dataset path for the
container, with the dataset staged via the cloud backend's transfer mechanism.

> The placeholder substitution and mount strategy are the **WS-5 runner's**
> responsibility (research repo). These recipes stay declarative about where the
> two roots resolve. If WS-5 prefers fully declarative recipes (no `run.command`
> at all, runner constructs the invocation), the four local 4B `run.command`
> blocks can be dropped in favor of the runner deriving the command from
> `method` + `dataset.local_file` + the trainer flags — that is a runner-side
> decision.

## Gated prerequisites (bridge arms)

`meta-llama/Llama-2-7b-chat-hf` is license-gated: access requires accepting the
Llama-2 license on Hugging Face under the operator account and exporting a valid
`HF_TOKEN` (or `HF_API_KEY`) into the run environment. The credential is passed
via env only and is **never** written into a recipe. The bridge arms also
consume Cheng et al.'s OpenMOSS Idk training data, itself a license-gated CODE
prerequisite requiring user sign-off before fetch.
