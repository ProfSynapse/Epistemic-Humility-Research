---
name: mech-interp-runner
description: Run, plan, validate, or aggregate Epistemic-Humility local Phase 3 mechanistic-interpretability sweeps, including hidden-state candidate inventories, causal-pilot sweep planning, explicit non-GPU/GPU gates, base-original skip handling, and offline result aggregation. Use when working on local mech-interp sweeps, causal-pilot diagnostics, activation-addition/logit-diagnostic runs, or future reruns of the Phase 3 full candidate inventory.
---

# Mech-Interp Runner

Use the checked-in scripts. Do not hand-roll terminal loops.

## Scope

- Treat outputs as Tier 2 exploratory local mechanism evidence.
- Do not edit `synaptic-tuner/`.
- Do not run Docker/GPU unless the user explicitly approves that live run.
- Keep base-original `h_base` adapterless work fail-closed until the live runner
  explicitly supports adapterless base execution.

## Full Sweep Plan

Plan the reusable full local sweep without model loading:

```bash
python experiment/phase1/probe/phase3_causal_pilot_sweep.py \
  --config experiment/phase1/probe/config/phase3_causal_pilot_local_sweep.yaml
```

The sweep config points at:

- `experiment/phase1/probe/config/phase3_causal_pilot_full_candidates.yaml`
- `experiment/phase1/probe/config/phase3_causal_pilot_gpu_smoke.yaml`

Expected current shape: 9 inventory candidates, 8 executable candidates, 1
skipped base-original candidate, and 16 executable jobs across generation and
logit-diagnostic modes. The checked-in local sweep uses Docker command planning
for live GPU execution.

## Materialize Without Running

```bash
python experiment/phase1/probe/phase3_causal_pilot_sweep.py \
  --config experiment/phase1/probe/config/phase3_causal_pilot_local_sweep.yaml \
  --write-plan --materialize-configs
```

This writes a plan plus per-candidate runner configs only. It does not execute
generation or logit diagnostics. Planned live commands should start with
`docker run --rm --gpus all --ipc=host --entrypoint python`, mount the repo to
`/workspace/repo`, and use `/workspace/repo/...` paths for the runner and
materialized configs.

For a logit-only sweep from the full config, filter before planning:

```bash
python experiment/phase1/probe/phase3_causal_pilot_sweep.py \
  --config experiment/phase1/probe/config/phase3_causal_pilot_local_sweep.yaml \
  --mode-filter logit_diagnostic --write-plan --materialize-configs
```

## Live Execution Gate

Only after explicit user approval:

```bash
python experiment/phase1/probe/phase3_causal_pilot_sweep.py \
  --config experiment/phase1/probe/config/phase3_causal_pilot_local_sweep.yaml \
  --mode-filter logit_diagnostic \
  --write-plan --materialize-configs --execute \
  --allow-logit-diagnostic
```

The wrapper still relies on `phase3_causal_pilot_runner.py` for live model
loading, hooks, output manifests, and fail-closed control validation. Execution
is serial by default; do not parallelize GPU jobs unless the user explicitly
asks for a capacity experiment.

Live execution observability is under the sweep output root:

- `OUTPUT_ROOT/_execution_logs/*.stdout.log`
- `OUTPUT_ROOT/_execution_logs/*.stderr.log`
- `OUTPUT_ROOT/_execution_logs/execution_results.jsonl`

The wrapper appends one execution-results row after each job finishes. If a
Docker sweep is interrupted or a job fails, inspect this JSONL plus the per-job
logs before deciding what to rerun; do not rely only on `sweep_manifest.json` or
`planned_commands.jsonl`.

If a failed Docker attempt is immediately rerun, `execution_results.jsonl` may
contain both the failed row and the later successful row for the same
candidate/mode. Treat it as an append-only event log: group by candidate/mode
and use the latest successful event when summarizing completed work, while
still preserving the failed event as provenance for the retry.

Docker materialized runner configs must contain container-readable paths. The
sweep wrapper rewrites obvious runner config paths such as `output.root`,
`selection.probe_results`, `runtime_model.adapter_path`, and candidate direction
artifact paths to `/workspace/repo/...` when `execution.backend: docker`. A mixed
path like `/workspace/repo/F:\Code\...` means the materialized YAML is unsafe to
run and the sweep should be stopped and replanned.

## SAE Plumbing Smoke

Use the CPU-only SAE-shaped plumbing smoke to validate existing hidden-state
extraction artifacts before adding real SAE training code:

```bash
python experiment/phase1/probe/phase3_sae_smoke.py \
  --config experiment/phase1/probe/config/phase3_selfaware_sae_smoke.yaml
```

This smoke is numpy-only and deterministic. It loads verified SelfAware
extraction manifests and row shards, selects a small balanced known/unknown row
slice, applies a seeded random encoder, keeps a top-k sparse code, decodes it,
and writes claim-safe metrics/manifests under the configured `sae_smokes` root.

Treat every output as `SAE_PLUMBING_SMOKE_ONLY`. It is not a trained SAE, not a
mechanistic interpretation result, and not evidence for paper claims. Use it
only to catch broken manifest, row-selection, safetensors, layer, role, shape,
or output-root plumbing before a governed SAE implementation exists.

The generated `sae_smokes` output tree is local/reproducible and may contain
tensor slices from hidden activations. Keep it gitignored by default; commit
the runner, config, tests, and session note rather than smoke tensor outputs
unless a governed artifact-publication decision explicitly whitelists a subset.

Fail closed if the source extraction manifest is missing, not `status: ok`, or
not `verified: true`; if labels are not exactly `known`/`unknown`; if the
balanced slice is unavailable; if a role shard or layer tensor is missing; if
tensor shapes disagree with the manifest; or if the output root is inside a
source extraction directory.

## SAE Training Pilot

After the plumbing smoke passes, use the bounded SAE training pilot for a first
real autoencoder run over existing hidden-state tensors:

```bash
python experiment/phase1/probe/phase3_sae_train.py \
  --config experiment/phase1/probe/config/phase3_selfaware_sae_pilot.yaml
```

This trains a small ReLU sparse autoencoder with an L1 code penalty over the
configured hidden-state layer, using deterministic train/validation splits and
local `sae_runs` outputs. Treat every output as `SAE_TRAINING_PILOT_ONLY`: it
is exploratory representation-learning evidence only, not causal evidence, not
feature-interpretability evidence, and not Phase 1 headline evidence.

Current local sensitivity found that a vanilla ReLU SAE with L1 coefficients
`1e-4` and `1e-2` stayed dense on the SelfAware delta slices, and `1e-1` was
only moderately sparse. Top-k ReLU produced exact sparse codes: k=16 is the
current checked-in interpretability pilot default, while k=32 is the softer
reconstruction/sparsity compromise. Do not interpret either as feature-level
causal evidence without downstream feature inspection and intervention.

The generated `sae_runs` output tree contains learned weights and normalization
statistics derived from hidden activations. Keep it gitignored by default and
commit only the runner, config, tests, skill updates, and session note unless a
governed artifact-publication decision explicitly whitelists a subset.

## SAE Feature Analysis

After a trained SAE pilot exists, use the feature-analysis runner to rank learned
features by known/unknown activation separation:

```bash
python experiment/phase1/probe/phase3_sae_feature_analysis.py \
  --config experiment/phase1/probe/config/phase3_selfaware_sae_feature_analysis.yaml
```

This reuses the trained SAE weights, saved normalization statistics, selected
rows, and verified source extraction tensors to recompute feature codes. It
writes `feature_rankings.csv`, `summary.json`, and top activating row examples
under the configured `sae_feature_analysis` output root.

Treat every output as `SAE_FEATURE_ANALYSIS_ONLY`: this is feature-screening
evidence for choosing candidate features, not causal evidence, not a
monosemantic-feature claim, and not Phase 1 headline evidence. Candidate
features still need row-level inspection and downstream logit/intervention
controls before being described as mechanisms.

Current local top-k16 SelfAware screen found stronger known/unknown separation
in the SFT->DPO delta SAE than the SFT->KTO delta SAE. DPO's top separated
feature had |d| about 1.28 and was known-skewed; KTO's top separated feature
had |d| about 0.88 and was unknown-skewed. Treat this as a prioritization cue
for the next causal diagnostic pass, not as an explanation by itself.

Generated `sae_feature_analysis` outputs are local/reproducible and may expose
row-level examples from the probe set. Keep them gitignored by default.

## SAE Feature Directions

After feature analysis, export selected SAE decoder columns as raw hidden-state
direction candidates for later controlled diagnostics:

```bash
python experiment/phase1/probe/phase3_sae_feature_directions.py \
  --config experiment/phase1/probe/config/phase3_selfaware_sae_feature_directions.yaml
```

The exporter multiplies each selected decoder column by the saved training
normalization scale, because the SAE was trained in standardized activation
space but the causal/logit runner intervenes in raw hidden-state space. Preserve
the feature's natural polarity: addition to a known-skewed feature should be
interpreted differently than addition to an unknown-skewed feature, and
subtraction is the paired opposite control.

Treat every output as `SAE_FEATURE_DIRECTION_CANDIDATES_ONLY`. These are bridge
artifacts for causal tests, not evidence that the SAE feature is monosemantic or
behaviorally active. Current exported top-k16 feature directions have much
smaller norms than the broad known/unknown mean-difference directions, so use a
separate coefficient smoke rather than blindly reusing prior grids.

Generated `sae_feature_directions` outputs are local/reproducible and should
stay gitignored unless a governed artifact-publication decision says otherwise.

## SAE Feature Composite Directions

When single SAE decoder-feature interventions look non-local or entangled, build
explicit composite directions rather than hand-editing tensors:

```bash
python experiment/phase1/probe/phase3_sae_feature_composites.py \
  --config experiment/phase1/probe/config/phase3_selfaware_sae_feature_composites.yaml
```

Composite directions are derived from an exported
`sae_feature_directions.manifest.json`, so each output keeps source direction
IDs, feature IDs, weights, combination method, rescaling method, layer, role,
hash, and vector path. Current supported combinations are
`raw_weighted_mean` and `unit_weighted_mean`; current rescaling choices are
`none`, `mean_source_norm`, and `sum_abs_weighted_source_norm`.

Treat outputs as `SAE_FEATURE_COMPOSITE_DIRECTION_CANDIDATES_ONLY`. They are
subspace-screening bridge artifacts, not proof that a sparse feature circuit has
been found. Composite sources must share layer, role, and hidden dimension.

If a composite is later referenced by a causal-pilot config with metadata fields
such as `contrast`, the composite export config must include the same metadata
so the generated manifest row matches the candidate config. Do not weaken the
dry-run validator to bypass a mismatch; regenerate the composite manifest with
the missing provenance field.

## Direction Transforms

Use direction transforms when broad hidden-state directions need to be compared
against much smaller SAE-derived directions under a shared coefficient grid:

```bash
python experiment/phase1/probe/phase3_direction_transforms.py \
  --config experiment/phase1/probe/config/phase3_selfaware_dpo_subspace_direction_transforms.yaml
python experiment/phase1/probe/phase3_direction_transforms.py \
  --config experiment/phase1/probe/config/phase3_selfaware_kto_subspace_direction_transforms.yaml
```

Current supported transforms are `unit_rescale_to_norm`, `multiply`, and
`identity`. Treat outputs as `DIRECTION_TRANSFORM_CANDIDATES_ONLY`. They are
bridge artifacts for controlled comparisons, not new source evidence. Prefer
same-norm transforms before comparing broad known/unknown deltas with SAE
decoder-feature or composite directions; otherwise coefficient-grid effects can
mostly reflect vector magnitude.

## SAE Feature Logit Diagnostics

After exporting SAE feature directions, run the checked-in feature-level
logit-diagnostic sweep as a coefficient smoke:

```bash
python experiment/phase1/probe/phase3_causal_pilot_sweep.py \
  --config experiment/phase1/probe/config/phase3_selfaware_sae_feature_logit_diagnostic_sweep.yaml \
  --mode-filter logit_diagnostic \
  --write-plan --materialize-configs --execute \
  --allow-logit-diagnostic
```

This pass uses exact top-activating row keys per feature and a smaller
feature-vector coefficient grid. Interpret it as a screening diagnostic:
top-1 token changes, target probability-slice deltas, wrong-layer controls, and
random matched-norm controls decide whether a feature deserves a stronger
causal follow-up. If a wrong-layer control is nearly as strong as the source
layer, do not call the feature a localized mechanism.

For nearby-layer panels, `control_settings.wrong_layer.layer_offsets` can be a
non-empty list such as `[-2, -1, 1, 2]`. The runner expands wrong-layer and
wrong-layer-subtraction controls into one arm per offset while preserving the
legacy single `layer_offset` behavior for older configs.

Current local result: DPO feature 47 at coefficient 50 strongly increased the
static refusal-opener slice on its four selected unknown rows, but the `+1`
wrong-layer control was nearly as strong, so this is an interesting
non-localized steering signal rather than a clean feature mechanism. KTO feature
directions were much weaker in the same smoke. Future follow-up should use a
nearby-layer panel, more rows, and row-specific answer/refusal target slices
before making a mechanistic claim. The first nearby-layer panel for DPO feature
47 confirmed the non-local result: offsets `-2`, `-1`, `+1`, and `+2` all moved
the refusal-opener slice, with offset `-1` close to the source-layer effect.
Treat this as evidence against a tidy layer-local SAE feature knob.

Current composite screen: the DPO unknown-pair composite (`f47 + f51`) was
weaker and no cleaner than feature 47 alone. The DPO unknown-minus-known
contrast (`f47 + f51 - f64 - f65`) produced stronger signed refusal-opener
movement on an 8-row panel, but wrong-layer controls remained comparable and
random matched-norm was still substantial. Treat this as evidence for an
entangled broader direction or subspace, not a localized SAE mechanism.

## Direction Geometry Maps

Before scaling causal runs, map candidate direction geometry against broader
known/unknown and arm-delta direction inventories:

```bash
python experiment/phase1/probe/phase3_direction_geometry.py \
  --config experiment/phase1/probe/config/phase3_selfaware_direction_geometry.yaml
python experiment/phase1/probe/phase3_direction_geometry.py \
  --config experiment/phase1/probe/config/phase3_selfaware_direction_geometry_all_delta_layers.yaml
```

This is CPU-only. It writes `direction_inventory.csv`, `pairwise_cosine.csv`,
`nearest_neighbors.csv`, and `summary.json` under the configured
`direction_geometry` output root. Treat every output as
`DIRECTION_GEOMETRY_ANALYSIS_ONLY`: cosine alignment is triage evidence for
choosing interventions, not causal evidence.

Current local result: the DPO SAE unknown-minus-known composite aligned strongly
with the broad DPO unknown-minus-known delta at layer 24 (`cosine ~= 0.653`) and
remained aligned with adjacent later DPO layers (`layer 25 ~= 0.553`, `layer 26
~= 0.506`, `layer 23 ~= 0.504`). The unknown-only pair aligned less strongly
with the same broad direction (`cosine ~= 0.388`). This supports treating the
SAE composite as a lead into a distributed known/unknown subspace rather than a
standalone sparse feature knob.

## Same-Norm Subspace Diagnostics

After same-norm transform export, run the same-scale subspace logit diagnostic:

```bash
python experiment/phase1/probe/phase3_causal_pilot_sweep.py \
  --config experiment/phase1/probe/config/phase3_selfaware_subspace_normed_logit_diagnostic_sweep.yaml \
  --mode-filter logit_diagnostic \
  --write-plan --materialize-configs --execute \
  --allow-logit-diagnostic
```

Current local result: with all compared directions normalized to the SAE
unknown-minus-known composite norm, the SAE contrast still produced the largest
signed refusal-opener movement on the 8-row unknown panel, especially under
activation subtraction at coefficient 50 (`delta ~= +0.134`, top-1 changed
`62.5%`). The same-norm DPO broad layer-24 direction was cleaner but smaller
under activation addition at coefficient 50 (`delta ~= +0.093`, top-1 changed
`37.5%`). The KTO broad layer-25 direction remained weak at the same norm.
Wrong-layer controls for the SAE contrast stayed comparable to the source-layer
effect, so this remains distributed-subspace evidence rather than layer-local
mechanism evidence.

## Aggregate Completed Runs

```bash
python experiment/phase1/probe/phase3_causal_pilot_aggregate.py \
  --root experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_local_mech_interp_sweep \
  --out experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_local_mech_interp_sweep/summary.csv
```

Use aggregate output as an index. Inspect source manifests and JSONL rows before
interpreting surprising effects.

The aggregate script walks every `run_manifest.json` under the root. If the same
sweep root contains repeated runs, filter to the newest run directory per
candidate/mode before reporting headline diagnostic numbers.

## Probability-Slice Diagnostics

When inspecting next-token probability slices, avoid treating the first token of
every multi-token answer alias as an answer token. Qwen tokenization can split
an answer like `Ireland` into a first token `I`, which collides with refusal
openers such as `I don't know` and falsely inflates the answer bucket.

For row-specific answer aliases, prefer exact single-token aliases and record
multi-token aliases as skipped unless a later diagnostic explicitly models
multi-token sequence probability. Static refusal opener groups may intentionally
use first-token openers, but answer-alias groups should default to
`include_multi_token_first_token: false`.

For changed-row replay claims, use exact row selection through
`selection.row_keys` or `selection.row_keys_by_candidate`. A balanced
`max_rows` slice may contain changed rows, but it is not changed-row-only
evidence.

Inspect top-k next-token entries together with probability slices. Top-1 or
greedy changes alone can hide whether refusal tokens, answer aliases, or nearby
answer-like distractors are moving.

Before making vector- or source-layer-specific interpretations, run implemented
controls such as no-vector baseline, activation addition/subtraction,
wrong-layer, and deterministic random matched-norm. If wrong-layer matches the
candidate effect, do not make a source-layer-specific claim without a stronger
nearby-layer panel.

Wrong-layer controls must be sign-matched to the source intervention. Do not
compare source-layer subtraction against positive wrong-layer addition; use the
`wrong_layer_subtraction` logit-diagnostic control pattern when the source
effect is activation subtraction.

Do not label a shuffled-label control unless there is a real shuffled-label
direction artifact or a valid checked-in derivation path. Report it as not
implemented rather than faking the control.

## Validation

Use focused non-GPU checks:

```bash
python -m pytest experiment/phase1/probe/tests/test_phase3_causal_pilot_sweep.py \
  experiment/phase1/probe/tests/test_phase3_causal_pilot_runner.py \
  experiment/phase1/probe/tests/test_phase3_causal_pilot_dry_run.py -q
python -m pytest experiment/phase1/probe/tests/test_phase3_sae_smoke.py -q
python -m pytest experiment/phase1/probe/tests/test_phase3_sae_train.py -q
python -m pytest experiment/phase1/probe/tests/test_phase3_sae_feature_analysis.py -q
python -m pytest experiment/phase1/probe/tests/test_phase3_sae_feature_directions.py -q
python -m pytest experiment/phase1/probe/tests/test_phase3_sae_feature_composites.py -q
python -m pytest experiment/phase1/probe/tests/test_phase3_direction_geometry.py -q
python -m pytest experiment/phase1/probe/tests/test_phase3_direction_transforms.py -q
python -m py_compile experiment/phase1/probe/phase3_causal_pilot_sweep.py \
  experiment/phase1/probe/phase3_causal_pilot_aggregate.py \
  experiment/phase1/probe/phase3_sae_smoke.py \
  experiment/phase1/probe/phase3_sae_train.py \
  experiment/phase1/probe/phase3_sae_feature_analysis.py \
  experiment/phase1/probe/phase3_sae_feature_directions.py \
  experiment/phase1/probe/phase3_sae_feature_composites.py \
  experiment/phase1/probe/phase3_direction_geometry.py \
  experiment/phase1/probe/phase3_direction_transforms.py
python bin/sync_skills.py --check
```
