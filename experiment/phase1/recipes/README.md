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

No recipe carries a `run.command` or any WS-5 placeholder vocabulary
(`{tuner_root}`/`{data_root}`/`/workspace/repo` literals) — they stay valid,
tuner-runnable job-configs. The **WS-5 experiment runner**
(`.claude/skills/experiment-runner/`) owns all command construction, container
wiring, and per-cell data feeding.

The three local-4B DPO/KTO recipes are stripped to the declarative core
(`model / dataset / training / lora / artifacts + method / provider`). The other
six recipes additionally keep a harmless declarative `run:` block of pointer keys
(`method / trainer / dry_run / dashboard / quiet`) — no `command`, no `workdir`,
no placeholders. The runner's `materialize_recipe` defensively pops `run.command`
and `run.workdir` from every materialized recipe regardless, so a residual `run:`
pointer block never contradicts the runner-built invocation.

**`run.method` + `run.trainer` are set by the runner, in ONE layer.** Under the
handler-extension dispatch (the tuner's `local-run` handler routes every method
through its generic command builder, reading `run.trainer` to pick the per-method
trainer script), a recipe with no `run.trainer` would silently default to
`Trainers/sft/train_sft.py` — so a DPO/KTO cell would run the SFT trainer. To make
that hazard impossible, `materialize_recipe` ALWAYS sets `run.method = <cell
method>` and `run.trainer = Trainers/<method>/train_<method>.py` on the materialized
recipe, per cell, regardless of what the committed base recipe carries. The
committed recipes therefore need NOT carry a `run:` block at all (and the three
local-4B DPO/KTO recipes deliberately do not) — the runner is the single source of
truth for `run.method`/`run.trainer`, so the value can never drift between a
committed file and the dispatch. Do not also hand-maintain `run.trainer` in the
committed recipes; that would create two layers that can disagree.

The data-locality reason this matters (verified against the tuner source): the
tuner container sees ONLY the tuner repo. Local Docker bind-mounts the tuner repo
root at `/workspace/repo` and joins `dataset.local_file` tuner-repo-relative
(`local_run_handler.py:502`: `/workspace/repo / local_file`); HF Jobs clones ONLY
the tuner repo. The research repo's `experiment/phase1/data/` is never visible to
the container, so a research-repo-relative `dataset.local_file` does not resolve.
WS-5 therefore feeds data per lane:

- **`dataset.local_file`** here is a **staging placeholder** the runner rewrites
  per cell. On the **local lane**, WS-5 stages the per-cell
  `experiment/phase1/data/<model_tag>/<method>_{train,dev}.jsonl` into the tuner's
  already-gitignored `synaptic-tuner/scratch/eh_staging/<run_id>/` and rewrites
  `dataset.local_file` to that tuner-repo-relative staged path so the
  `/workspace/repo` join resolves.

- On the **cloud lane**, WS-5 swaps `dataset.local_file` for an HF-hub
  `dataset.name` (the Phase-1 datasets are published publicly via the tuner's
  dataset-publishing skill), because HF Jobs checks out a pushed tuner commit that
  cannot see the ephemeral staged scratch.

All nine recipes (4B, 8B, bridge) are fed per lane in exactly this way; none
carry a `run.command`. The runner derives the invocation from `method` +
`dataset.local_file`/`dataset.name` + the trainer flags. See
`.claude/skills/experiment-runner/reference/lanes.md` for the full per-lane
contract and the current cloud-lane capability gate.

## Gated prerequisites (bridge arms)

`meta-llama/Llama-2-7b-chat-hf` is license-gated: access requires accepting the
Llama-2 license on Hugging Face under the operator account and exporting a valid
`HF_TOKEN` (or `HF_API_KEY`) into the run environment. The credential is passed
via env only and is **never** written into a recipe. The bridge arms also
consume Cheng et al.'s OpenMOSS Idk training data, itself a license-gated CODE
prerequisite requiring user sign-off before fetch.
