# LoRA Hidden-State Probing Tier Plan

Status: exploratory future tier
Created: 2026-06-14
Scope: future mechanism work after the locked Phase 1 lane

## Purpose

This plan captures a future activation-probing tier for the epistemic-humility
program. It is not a protocol change and does not alter either committed track:
the locked PROTOCOL v0.3 headline matrix signed on 2026-06-10, or Amendment A /
v0.4 signed on 2026-06-14 as a prospective sequential-extension track. Any
probing result from this tier is exploratory mechanism evidence unless a later
signed protocol revision explicitly promotes it.

The research question is whether abstention training changes the model's
internal knowledge state, only changes the surface refusal policy, or moves the
representation enough that base-trained probes no longer transfer. The tier
should compare base, LoRA-adapted, and delta activations on the same prompts
used by the behavioral and token-confidence evaluations.

## Core Design

Hidden-state inspection of LoRA-adapted models is feasible without merging the
adapter. For the MVP, use Hugging Face Transformers with PEFT unmerged adapters
and `output_hidden_states=True`.

Primary comparison:

```text
h_base  = hidden states with adapter disabled or unloaded
h_lora  = hidden states with the target PEFT adapter active
delta   = h_lora - h_base
```

Run deterministic forward passes with:

- `model.eval()`
- `use_cache=False`
- fixed dtype and device
- identical tokenizer and chat template
- `enable_thinking=False`, matching the Phase 1 Qwen3 discipline
- controlled prompts and no sampling during hidden-state extraction

Start with the final prompt token as the first token position. Expand only after
that baseline is stable, for example to answer-token positions, refusal-token
positions, layerwise windows, or pooled prompt representations.

## Adapter State Discipline

Merging is not the primary attribution path. Unmerged PEFT adapters are better
for attribution because the base/adapted contrast can be controlled in one
process with explicit adapter state.

Every extraction manifest should log:

- base model id/path and revision or local artifact hash
- adapter id/path and artifact hash
- active adapter name
- whether the adapter was disabled, unloaded, active, or merged
- dtype, device, tokenizer revision, chat-template settings, and
  `enable_thinking`
- prompt renderer hash and dataset/eval split identity
- layer list, token-position rule, tensor shape, and persistence format

Merged checkpoints are useful for deployment or tooling sanity checks, but not
as the primary evidence for attribution. If a merged sanity check is used, log it
separately and compare it against the unmerged-adapter forward pass.

## Build-Versus-Borrow Plan

Borrow:

- Transformers model outputs for `output_hidden_states=True`.
- PEFT `PeftModel` adapter activation and disabling/unloading controls.
- PyTorch forward hooks when module-level activations are needed.
- `nnsight` first for intervention, patching, and steering prototypes.
- TransformerLens only after compatibility with the model family, tokenizer, and
  LoRA path is confirmed; reserve it for deeper circuit or logit-lens work.

Build project-specific glue:

- paired base/adapted inference harness
- prompt rendering discipline shared with Phase 1 eval/probe
- layer and token-position selection rules
- tensor persistence and compression policy
- probe train/dev/test splits that respect existing leakage constraints
- provenance manifests for model, adapter, prompt, split, and extraction config
- metrics and controls for coherence across hidden state, token confidence, and
  stated abstention behavior
- adapter-state assertions to catch base-vs-adapter mistakes before extraction

Do not build custom intervention machinery before the borrowed tools fail a
concrete need. The first repo-native investment should be the paired harness and
provenance layer, because those are specific to this experiment.

## Evidence And Implementation Anchors

| Strategic choice | External support | Project anchor | Implementation implication |
|---|---|---|---|
| Use Transformers hidden states for the MVP. | Hugging Face Transformers documents `output_hidden_states=True` and returns per-layer `hidden_states` tensors in model outputs: <https://huggingface.co/docs/transformers/main_classes/output>. | The current probe is already config-driven and manifest-stamped in `experiment/phase1/probe/config/probe.yaml` and `experiment/phase1/probe/probe.py`. | Add hidden-state extraction as a separate probe-tier harness rather than mixing it into the stochastic knowledge probe. |
| Prefer unmerged PEFT adapters for attribution. | Hugging Face PEFT documents `PeftModel.set_adapter()`, `disable_adapter()`, and `merge_and_unload()`: <https://huggingface.co/docs/peft/package_reference/peft_model>. | Current eval uses explicit adapter paths per arm and vLLM LoRA requests in `experiment/phase1/eval/config/eval_smoke_local_4b.yaml` and `experiment/phase1/eval/run_eval.py`. | The primary contrast should be base-vs-active-adapter in one harness; merged checkpoints are sanity checks only. |
| Treat LoRA deltas as adapter-attribution candidates, not proof by themselves. | Hu et al. define LoRA as frozen pretrained weights plus trainable low-rank matrices injected into Transformer layers: <https://arxiv.org/abs/2106.09685>. | The Phase 1 recipes pin identical LoRA budgets, for example `experiment/phase1/recipes/eh_phase1_qwen3_4b_sft.yaml`; architecture rationale is in `docs/architecture/phase1-pipeline.md`. | Record LoRA rank/alpha/dropout/target modules in every extraction manifest and compare `h_lora - h_base` under identical prompts. |
| Use PyTorch hooks only when model-output hidden states are too coarse. | PyTorch documents `register_forward_hook` on `torch.nn.Module`: <https://docs.pytorch.org/docs/stable/generated/torch.nn.Module.html#torch.nn.Module.register_forward_hook>. | `experiment/phase1/probe/backends.py` already centralizes prompt rendering and thinking-tag checks; future module hooks should reuse the same prompt bytes. | Start with layer hidden states; add module hooks later for specific submodules such as attention or MLP outputs. |
| Use nnsight / TransformerLens for interventions after correlational probes stabilize. | nnsight documents tracing, activation access, setting activations, cross-prompt intervention, activation patching, and steering tutorials: <https://nnsight.net/documentation/>. TransformerLens provides an activation-patching API: <https://transformerlensorg.github.io/TransformerLens/generated/code/transformer_lens.patching.html>. | `experiment/phase1/eval/run_eval.py` already defines behavioral outcomes and provenance-stamped metric outputs. | Causal patching should be a later phase that measures movement in refusal, correctness, token confidence, and stated confidence, not an MVP dependency. |
| Treat patching metrics and corruption choices as first-class design choices. | Zhang and Nanda show activation patching results vary with metrics and corruption methods, and give best-practice recommendations: <https://arxiv.org/abs/2309.16042>. | Existing metric provenance and McNemar/bootstrap outputs live in `experiment/phase1/eval/run_eval.py`, `experiment/phase1/eval/stats.py`, and `experiment/phase1/eval/scorers.py`. | Pre-register patching metrics inside the future tier before interpreting any intervention effect. |
| Preserve prompt, split, and provenance discipline from Phase 1. | This is project-specific rather than borrowed from a library. | `experiment/phase1/data/build_datasets.py` enforces leakage guard, frozen question budget, and grouped dev split; `experiment/phase1/data/config/build.yaml` records the builder knobs; `experiment/phase1/run_records/sft__4b__headline__seed1.json` shows run-record provenance; `TODO.md` records the Amendment A / v0.4 separation and bounded local evidence caveats. | Hidden-state outputs must carry config hashes, source question keys, prompt-rendering settings, adapter state, and the exact behavioral/eval artifact they align to. |

## Analysis Sequence

1. Correlational extraction

   Extract `h_base`, `h_lora`, and `delta` for matched prompts across base and
   each trained adapter. Begin with final prompt token, all layers, and a small
   balanced slice of known/unknown questions.

2. Linear probes

   Train probes for correctness, known/unknown status, refusal outcome, and
   answer-on-unknown behavior. Evaluate both within-model and base-to-adapter
   transfer.

3. Coherence metrics

   Compare hidden-state probe confidence with token-level confidence,
   behavioral refusal/correctness, and stated confidence when available. The
   target quantity is coherence delta, not a single probe score.

4. Causal validation

   Only after correlational probes are stable, test whether interventions move
   behavior. Use activation patching or steering to measure effects on refusal,
   correctness, logprob confidence, and stated confidence.

## File-By-File Future Implementation Plan

This is a future implementation plan, not completed work. Keep it separate from
the signed v0.3 and Amendment A / v0.4 execution paths unless a later protocol
revision says otherwise.

### Phase 0 - design and schema only

- `docs/plans/lora-hidden-state-probing-tier.md`: keep this document as the
  controlling exploratory design note; update it before code if the target
  token rule, layer set, or intervention metric changes.
- `docs/research-trajectory.md`: continue to describe this as
  Phase 3 mechanism work, not a Phase 1 headline or Amendment A result.
- `experiment/phase1/probe/README.md`: add a future section for hidden-state
  extraction once code exists, explicitly separating it from the existing
  stochastic knowledge probe.

### Phase 1 - correlational extraction harness

- `experiment/phase1/probe/config/hidden_state_probe.yaml` (new): define the
  hidden-state extraction config: `model_tag`, `model_name`, adapter arms,
  adapter paths, adapter state (`disabled`, `active`, optional `merged_sanity`),
  `enable_thinking: false`, layer list, token-position rule, dtype/device,
  prompt source, output format, and extraction config hash.
- `experiment/phase1/probe/hidden_state_probe.py` (new): load the base
  Transformers model and PEFT adapters, run deterministic forward passes with
  `output_hidden_states=True`, `use_cache=False`, and `model.eval()`, and write
  `h_base`, `h_lora`, and `delta` for the configured prompts. It should reuse
  the prompt-rendering discipline from `experiment/phase1/probe/backends.py`
  rather than inventing a second Qwen3 chat-template path.
- `experiment/phase1/probe/hidden_state_schema.py` (new): centralize validation
  for tensor shape, layer ids, token-position metadata, adapter state, prompt
  hash, and manifest fields so tests can assert the file contract without
  loading a model.
- `experiment/phase1/probe/backends.py`: if needed, extract the Qwen3
  prompt-rendering and thinking-tag assertions into a shared helper used by both
  the current generation probe and the new hidden-state harness. Do not weaken
  the existing runtime self-checks.

### Phase 2 - prompt and split alignment

- `experiment/phase1/probe/probe.py`: treat existing `probe_results.jsonl`
  fields (`probe_pool_row_key`, `question`, `label`, `probe_config_sha`) as the
  alignment source for hidden-state rows; do not rerun stochastic probing inside
  the hidden-state harness.
- `experiment/phase1/data/qwen3-4b-instruct/questions_frozen.json`: read the
  frozen train/dev question keys when building matched known/unknown extraction
  slices, so hidden-state probes use the same budget identity as Phase 1.
- `experiment/phase1/data/build_datasets.py`: no initial code change should be
  required; use its existing `norm_question` / frozen-budget discipline as the
  contract the hidden-state selection code must respect.
- `experiment/phase1/eval/config/eval_smoke_local_4b.yaml` and later real eval
  configs: read adapter paths and `model_name` conventions from these configs
  when possible so extraction and behavioral eval point at the same artifacts.

### Phase 3 - outputs and provenance

- `experiment/phase1/probe/<model_tag>/hidden_states/<extraction_id>/`
  (new output tree): write tensor shards plus a manifest. Prefer a tensor-native
  format such as `safetensors` for activations and JSON/JSONL for row metadata.
- `experiment/phase1/probe/<model_tag>/hidden_states/<extraction_id>/manifest.json`
  (new): record base model id/revision, adapter path/hash, active adapter name,
  adapter state, whether a merged sanity check was run, dtype/device, tokenizer
  revision, `enable_thinking`, prompt hash, source split, layer list,
  token-position rule, tensor shapes, code commit, and extraction config hash.
- `experiment/phase1/run_records/<run_id>.json`: future analysis should link
  each extraction to the training run record for the adapter it probes, but
  should not mutate existing run records retroactively.

### Phase 4 - tests and smoke checks

- `experiment/phase1/probe/tests/test_hidden_state_probe.py` (new): fixture-test
  config parsing, prompt identity, adapter-state validation, tensor-shape
  schema, and manifest hash stamping without requiring a GPU.
- `experiment/phase1/probe/tests/test_probe_smoke.py`: add only narrow shared
  prompt-rendering regression coverage if `backends.py` is refactored for reuse.
- `experiment/phase1/eval/tests/test_run_eval_e2e.py`: do not couple eval tests
  to hidden-state extraction unless a future behavior-vs-activation join is added.

### Phase 5 - probes, joins, and causal work

- `experiment/phase1/probe/hidden_state_analysis.py` (new): train and evaluate
  linear probes on extracted activations, reporting within-model and
  base-to-adapter transfer.
- `experiment/phase1/eval/results_*`: join hidden-state probe confidence to
  existing behavioral metrics only by explicit row ids and config hashes; never
  by loose question text alone.
- `experiment/phase1/probe/activation_patching.py` (new, later): prototype
  nnsight or TransformerLens patching only after Phase 1-4 outputs are stable
  and the intervention metric is written down.

## Controls And Confounds

Main risks to control before interpreting an effect:

- surface IDK phrasing rather than epistemic humility
- refusal/safety behavior rather than knowledge-boundary behavior
- recall strength, difficulty, source dataset, and topic imbalance
- token-position dependence
- cached decoding or generation-shape differences
- final normalization differences across extraction methods
- adapter-state mistakes, especially accidentally comparing adapter-active runs
  to adapter-active runs
- Qwen3 thinking-template leakage or prompt mismatch
- Goodhart risk if hidden-state probes are later used directly in reward loops

Minimum controls:

- matched known/unknown prompts from the same frozen split
- same rendered prompt bytes across base and adapter-active passes
- same final-token extraction rule across arms
- adapter-disabled base pass in the same harness
- negative controls on unrelated or shuffled labels
- prompt-format controls to test whether probes learn task format

## Candidate Evidence Outcomes

The tier should preserve the three-outcome reading from the research trajectory:

- hidden state, token confidence, and behavior move together: humility may have
  become more internally coherent
- behavior changes while hidden-state probes transfer unchanged: humility may be
  a surface policy over an unchanged epistemic state
- probes fail to transfer: training moved the representation; localize by layer,
  token position, and adapter delta before making a behavioral claim

## Compact Source List

Use these as the first references when turning this plan into implementation:

- PyTorch `register_forward_hook` documentation:
  <https://docs.pytorch.org/docs/stable/generated/torch.nn.Module.html#torch.nn.Module.register_forward_hook>
- Hugging Face Transformers model-output documentation:
  <https://huggingface.co/docs/transformers/main_classes/output>
- Hugging Face PEFT `PeftModel` documentation:
  <https://huggingface.co/docs/peft/package_reference/peft_model>
- Hu et al., "LoRA: Low-Rank Adaptation of Large Language Models":
  <https://arxiv.org/abs/2106.09685>
- `nnsight` documentation: <https://nnsight.net/>
- TransformerLens activation-patching documentation:
  <https://transformerlensorg.github.io/TransformerLens/generated/code/transformer_lens.patching.html>
- Zhang and Nanda, "Towards Best Practices of Activation Patching in Language
  Models: Metrics and Methods": <https://arxiv.org/abs/2309.16042>
