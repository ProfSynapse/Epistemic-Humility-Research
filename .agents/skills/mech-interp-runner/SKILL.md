---
name: mech-interp-runner
description: Run, plan, validate, or aggregate Epistemic-Humility local Phase 3 mechanistic-interpretability sweeps, including hidden-state candidate inventories, causal-pilot sweep planning, explicit non-GPU/GPU gates, base-original skip handling, and offline result aggregation. Use when working on local mech-interp sweeps, causal-pilot diagnostics, activation-addition/logit-diagnostic runs, behavior-axis scans, SAE feature screens, or future reruns of the Phase 3 full candidate inventory.
---

# Mech-Interp Runner

Use checked-in scripts and configs. Do not hand-roll terminal loops.

## Progressive Disclosure

Keep this file as the runnable workflow and invariant checklist. Load extra
context only when needed:

- For current Phase 3 findings and interpretation caveats, read
  `references/phase3-current-findings.md`.
- For detailed provenance, read the active session note under `docs/sessions/`.
- For exact historical output values, inspect run manifests, summary CSVs, and
  JSONL rows under the relevant `causal_pilots`, `behavior_axis_scan`,
  `sae_*`, or `direction_geometry` output root.

Do not add running result logs or long historical summaries to `SKILL.md`.
Promote only durable procedure, guardrails, and reusable commands here.

## Compact Recovery Loop

After context compaction or degraded memory:

1. Re-read this skill and drill into references only as needed.
2. Re-read the latest relevant `docs/sessions/` note and local KG/search
   results if they affect the next experiment.
3. Set up or run the current local experiment with checked-in scripts/configs.
4. Analyze outputs against the current research target.
5. Update session notes, findings references, and skills when a durable
   procedure or gotcha changes.
6. Choose the next highest-ROI local slice from the evidence and repeat.

Stay local to this repository for Phase 3 mech-interp work. Do not use external
workflow or memory systems such as Nexus unless the user explicitly asks for
them in the current turn.

## Skill Maintenance Contract

Keep `SKILL.md` self-documenting and bounded:

- Put timeless rules, routing, commands, and validation gates in `SKILL.md`.
- Put current findings, numeric results, and interpretation snapshots in
  `references/*.md`.
- Put run-specific provenance, decisions, and narrative updates in
  `docs/sessions/*.md`.
- Put reusable analysis logic in checked-in scripts or configs, not prose.
- If a section grows because of one experiment, move the details to a reference
  and leave only the general rule plus the reference path.
- After editing this skill, run `python bin/sync_skills.py --write`, then
  `python bin/sync_skills.py --check`.

Before adding a paragraph to this file, ask: "Will this still guide a future
agent six months from now without loading today's run history?" If not, put it
in a reference or session note.

## Research Target

The target is not a raw refusal axis. The target is coherent epistemic-humility
expression: the model answers when it has usable knowledge and abstains when it
does not.

Separate these surfaces before interpreting a direction:

- `known_correct_answer`: desired answering behavior.
- `known_refused`: over-refusal damage.
- `unknown_refused`: desired abstention behavior.
- `unknown_answered_wrong`: hallucination / under-refusal damage.
- Confidence-bearing variants when available: low-confidence unknown refusal,
  high-confidence wrong answer, and uncertain-but-correct known answer.

A candidate direction is only promising if it improves one damaged behavior
without degrading the paired desired behavior. Lower refusal alone is not a win.
First-token answer-start movement is not generated-answer correctness.

## Scope

- Treat outputs as Tier 2 exploratory local mechanism evidence.
- Do not edit `synaptic-tuner/`.
- Do not run Docker/GPU unless the user explicitly approves that live run.
- Keep base-original `h_base` adapterless work fail-closed until the live runner
  explicitly supports adapterless base execution.
- Keep generated outputs gitignored by default unless a governed publication
  decision explicitly whitelists them.

## CLI Wrapper

Prefer the skill CLI for common local analyses instead of hand-writing long
PowerShell commands:

```bash
python .skills/mech-interp-runner/scripts/phase3_cli.py --help
python .skills/mech-interp-runner/scripts/phase3_cli.py validate --quick
```

The wrapper delegates to checked-in repo scripts, resolves paths from the repo
root, uses `sys.executable`, and forces UTF-8 subprocess output
(`PYTHONUTF8=1`, `PYTHONIOENCODING=utf-8`, `PYTHONUNBUFFERED=1`) to avoid
Windows console encoding failures.

Use it for routine non-GPU analysis:

```bash
python .skills/mech-interp-runner/scripts/phase3_cli.py behavior-axis-scan \
  --config experiment/phase1/probe/config/phase3_sycophancy_answer_behavior_axis_scan.yaml
python .skills/mech-interp-runner/scripts/phase3_cli.py causal-sweep \
  --config experiment/phase1/probe/config/phase3_sycophancy_answer_logit_sweep.yaml \
  --mode-filter logit_diagnostic --write-plan --materialize-configs
python .skills/mech-interp-runner/scripts/phase3_cli.py sycophancy-generation-analysis \
  --generations path/to/generations.jsonl \
  --output-root path/to/analysis
```

Use `--dry-run` on any subcommand to print the delegated command before running
it. For live Docker/GPU execution, the same approval rule applies: do not pass
`--execute` unless the user has approved that live run.

## Hidden-State Extraction Preflight

Before launching a hidden-state extraction, run a model-free config preflight
from the repo root. Importing `hidden_state_probe.py` directly requires the
probe directory on `PYTHONPATH`; otherwise root-level imports can fail with
`ModuleNotFoundError: No module named 'hidden_state_schema'`.

PowerShell pattern:

```powershell
$env:PYTHONPATH='experiment/phase1/probe'
@'
from pathlib import Path
from hidden_state_probe import parse_config, resolve_output_dir, select_matched_slice
for path in [
    Path('experiment/phase1/probe/config/example_hidden_state_config.yaml'),
]:
    cfg, sha = parse_config(path)
    rows = select_matched_slice(cfg)
    out = resolve_output_dir(cfg, sha)
    print(path.name, sha[:16], len(rows), out.as_posix())
'@ | python -
```

This validates YAML shape, arm declarations, selection source, row count, and
deterministic output path without constructing the model backend. It is not a
substitute for the manifest verification gate after live extraction.

### Extraction granularity: residual_stream vs attention_head

`extraction.granularity` selects what each row captures (default
`residual_stream`, the original behavior):

- `residual_stream` — one final-prompt-token vector per layer; `expected_layer_count`
  = N+1 (embeddings + N blocks), each width `hidden_dim`. Validated by
  `validate_hidden_state_shape`.
- `attention_head` — the ITI surface: each attention block's final-token o_proj
  INPUT (the concatenated per-head context), captured via forward hooks on
  `...layers.<i>.self_attn.o_proj`. N blocks (NO embedding layer), each width
  `num_attention_heads * head_dim` (this differs from `hidden_dim` under Qwen3
  GQA — head_dim is read from `config.head_dim`, never `hidden_dim // heads`).
  Validated by `validate_head_state_shape`; reshape per head with
  `reshape_o_proj_input_to_heads`.

For the head path the manifest carries `granularity`, `num_attention_heads`, and
`head_dim` (the finalize gate REQUIRES the two dims non-null when
granularity=attention_head; they stay null for residual). Each `rows.jsonl`
record also self-describes its granularity + head layout, so a downstream
per-head reshape can proceed from the rows alone. Persistence is
granularity-agnostic (both write a `layer_id -> vector` map), so the same
`extraction_dir` layout, resume, and verification gate apply unchanged.

## Sycophancy / Helpfulness Probe Path

Use this path when testing whether training regimens change susceptibility to
user pressure, helpfulness framing, or answer-sycophancy. Treat it as adjacent
evidence: it can explain over-answering or user-pleasing pressure, but it is not
the same construct as calibrated epistemic humility.

Start with the checked-in answer-sycophancy OOD loader and smoke config:

```bash
python experiment/phase1/eval/run_eval.py \
  --config experiment/phase1/eval/config/eval_sycophancy_answer_smoke_seed1_all_arms_local_4b.yaml \
  --live-vllm
```

For Windows/WSL local runs, prefer the working Docker vLLM environment if host
Python reports `ModuleNotFoundError: No module named 'vllm._C'`. The host import
can detect the package while missing compiled vLLM extensions.

Analyze scored rows with:

```bash
python experiment/phase1/eval/analysis/sycophancy_answer_analysis.py \
  --results-dir experiment/phase1/eval/results_sycophancy_answer_smoke_seed1_all_arms_4b \
  --output-root experiment/phase1/eval/analysis/sycophancy_answer_smoke_seed1_all_arms_4b
```

Read the paired JSONL before interpreting summary metrics. On small slices, low
neutral correctness can make capitulation percentages unstable. Report neutral
accuracy, wrong-hint accuracy, wrong-hint match rate, over-refusal, and
condition-level stated confidence together.

Wrong-hint matching must be correctness/refusal-aware. Do not count a row as
matching the user's wrong answer if the model answered correctly while negating
or mentioning that wrong answer.

For mechanistic follow-up, build an extraction-compatible row manifest before
running hidden-state extraction:

```bash
python experiment/phase1/probe/phase3_sycophancy_answer_row_manifest.py
```

Prefer same-condition controls before interpreting a sycophancy axis. A
neutral-vs-wrong-hint contrast can mostly encode the extra user-hint text. Use
wrong-hint-followed vs wrong-hint-not-followed, or wrong-hint-followed vs
wrong-hint-refused, when the panel has enough rows.

Run offline scans only after the hidden-state extraction manifests are
`status=ok` and `verified=true`:

```bash
python experiment/phase1/probe/phase3_behavior_axis_scan.py \
  --config experiment/phase1/probe/config/phase3_sycophancy_answer_behavior_axis_scan.yaml
```

For Docker hidden-state extraction, git provenance can fail under mounted-repo
ownership unless git is called with `safe.directory`. Keep the strict manifest
gate; fix provenance collection rather than allowing null commit fields.

For generated-answer sycophancy replays, use the screening analyzer and then
manually inspect the per-row JSONL:

```bash
python experiment/phase1/probe/phase3_sycophancy_generation_analysis.py \
  --generations path/to/generations.jsonl \
  --output-root path/to/analysis
```

The automatic wrong-hint match is conservative about correct/refusal rows, but
it can still overcount hedged mentions. Treat the summary CSV as triage and the
row JSONL as the interpretation surface.

## Standard Sweep Workflow

Plan/materialize before live execution:

```bash
python experiment/phase1/probe/phase3_causal_pilot_sweep.py \
  --config experiment/phase1/probe/config/phase3_causal_pilot_local_sweep.yaml \
  --mode-filter logit_diagnostic \
  --write-plan --materialize-configs
```

Only after approval, execute:

```bash
python experiment/phase1/probe/phase3_causal_pilot_sweep.py \
  --config experiment/phase1/probe/config/phase3_causal_pilot_local_sweep.yaml \
  --mode-filter logit_diagnostic \
  --write-plan --materialize-configs --execute \
  --allow-logit-diagnostic
```

Aggregate completed runs:

```bash
python experiment/phase1/probe/phase3_causal_pilot_aggregate.py \
  --root experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_local_mech_interp_sweep \
  --out experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_local_mech_interp_sweep/summary.csv
```

Use aggregate output as an index. Inspect `run_manifest.json`, per-row JSONL,
and source configs before interpreting surprising effects.

Aggregation collects every completed run under the root. If a candidate was
rerun after a failed or partial attempt, filter to the latest successful
`run_manifest.json` per candidate/mode before reporting metrics.

## Live Execution Observability

Sweep execution logs are under:

- `OUTPUT_ROOT/_execution_logs/*.stdout.log`
- `OUTPUT_ROOT/_execution_logs/*.stderr.log`
- `OUTPUT_ROOT/_execution_logs/execution_results.jsonl`

`execution_results.jsonl` is append-only. If a failed Docker attempt is rerun,
group by candidate/mode and use the latest successful event while preserving
failed events as retry provenance.

Docker materialized runner configs must contain container-readable paths. A path
like `/workspace/repo/F:\Code\...` is unsafe; stop and replan.

## Resumable GPU Sweeps (checkpoint/resume)

Long GPU sweeps are killed mid-run when the CLI session is torn down (Monitor
timeout, agent teardown, host restart). Two rules keep a partial sweep cheap to
recover:

1. **Detach the container so it outlives the CLI.** A foreground
   `docker.exe run --rm ...` launched via a background Bash shell dies when that
   shell is reaped, taking the GPU work with it. Launch with `docker.exe run -d
   --name <run>` instead, then poll `docker.exe logs <run>` / the output
   `summary.json`, and watch terminal state with
   `docker.exe inspect -f '{{.State.Status}} {{.State.ExitCode}}' <run>`. The
   detached container keeps running across CLI restarts.

2. **Make the runner resume by default.** Stream per-row results to
   `rows.jsonl` (flush per row) keyed by a unique work unit — for the per-head
   ITI runner that is `(arm_id, probe_pool_row_key)`. On start, read the existing
   `rows.jsonl`, skip completed units, and append only the missing ones; tolerate
   a truncated final line (killed mid-write) by dropping it so that unit
   regenerates. Load the model lazily so a fully-resumed run re-emits the summary
   with no GPU. Guard resume with a `checkpoint.json` fingerprint over everything
   that defines a unit (model, adapter, prompt, steering path, rows, alphas,
   `max_new_tokens`, `max_rows`); refuse to resume on mismatch unless `--fresh`,
   so two configs never mix in one `rows.jsonl`. Reference implementation:
   `phase3_head_intervention_runner.py` (`run_config(..., fresh=...)`,
   `_load_completed`, `_config_fingerprint`); greedy/deterministic decoding makes
   resumed rows identical to a clean run.

## Runtime Semantics

For live `phase3_causal_pilot_runner.py` diagnostics, runtime identity is
controlled by `runtime_model`, not descriptive `model` metadata. If
`runtime_model.adapter_path` is null, the runner falls back to the candidate
extraction manifest adapter by default. That is an arm-native panel.

For same-runtime adapterless SFT panels, disable extraction-adapter fallback:

```yaml
runner_overrides:
  runtime_model:
    model_name: /workspace/repo/path/to/sft/merged-16bit
    adapter_path: null
    use_extraction_adapter: false
    allow_adapterless: true
```

Use `runner_overrides` for reusable sweep-level changes such as exact row
slices, runtime pins, logit target groups, and control settings.

## Row Selection

Use fixed row keys for causal replay claims:

```yaml
runner_overrides:
  selection:
    row_keys:
      - selfaware::selfaware::000002::selfaware-3
```

For changed-row or behavior-conditioned claims, balanced `max_rows` is not
enough. Use exact `selection.row_keys` or `selection.row_keys_by_candidate` and
record how rows were chosen.

For reusable fixed panels, put row keys in a text file and reference it:

```yaml
runner_overrides:
  selection:
    probe_results: null
    row_keys_file: experiment/phase1/probe/config/example_fixed_row_keys.txt
```

Use one row key per line. Blank lines and `#` comments are allowed. Keep these
files small, named by the panel purpose, and checked in only when they contain
non-restricted row identifiers.

For behavior-cell replay panels from an existing behavior-labeled rows file,
use the checked-in builder instead of copying row keys from terminal output:

```bash
python experiment/phase1/probe/phase3_behavior_panel_row_keys.py \
  --config experiment/phase1/probe/config/example_behavior_panel_row_keys.yaml
```

The builder selects deterministic row-key quotas by `behavior_cell`, applies
exclude row-key files, and writes selected rows plus a manifest. Use it for
disjoint replay panels such as known-refused / known-correct / unknown-refused
stress tests.

Do not infer rare-cell availability from the current extracted overlay alone.
Full evals can contain enough rare failures even when a prior hidden-state
extraction slice does not. For SelfAware full-eval rare-cell panels, first build
a focused extraction-ready manifest from scored rows:

```bash
python experiment/phase1/probe/phase3_selfaware_behavior_manifest.py \
  --config experiment/phase1/probe/config/example_selfaware_behavior_manifest.yaml
```

Then point a `selection.source: selfaware_manifest` hidden-state extraction at
the generated manifest. Keep quotas explicit and `require_quotas: true` for
balanced axes so sparse rare-cell panels fail closed instead of silently
becoming one-sided.

Hidden-state extraction also supports exact probe-pool row-key files:

```yaml
selection:
  source: probe_pool
  questions_frozen: ../data/qwen3-4b-instruct/questions_frozen.json
  probe_results: qwen3-4b-instruct/probe_results.jsonl
  row_keys_file: config/example_fixed_row_keys.txt
```

The extraction selector validates every key against the frozen known/unknown
pools, rejects duplicates and discard/out-of-frozen keys, and preserves file
order. Use this for rare-cell-enriched panels instead of increasing random
`n_known`/`n_unknown` slices blindly.

For per-row logit targets, prefer structured row fields over copied strings:

```yaml
logit_targets:
  groups:
    - name: wrong_hint_answer
      source: row_field
      field_path: sycophancy.incorrect_answer
      include_leading_space_variants: true
      include_multi_token_first_token: false
```

This requires the extraction rows to preserve the nested metadata field. Verify
`rows.jsonl` before launching live diagnostics.

For row-alias logit targets, verify the live runner actually receives aliases.
Legacy probe result files usually expose `normalized_aliases`; current behavior
row overlays expose `aliases`. The causal-pilot runner supports both, but only
when `selection.probe_results` points at a row source that contains one of
those fields. If answer-alias metrics are absent from `logit_diagnostics.jsonl`,
do not interpret the run as answer-channel evidence; fix alias loading and rerun.

## SAE Path

Use SAE scripts as screens, not causal evidence:

```bash
python experiment/phase1/probe/phase3_sae_smoke.py \
  --config experiment/phase1/probe/config/phase3_selfaware_sae_smoke.yaml
python experiment/phase1/probe/phase3_sae_train.py \
  --config experiment/phase1/probe/config/phase3_selfaware_sae_pilot.yaml
python experiment/phase1/probe/phase3_sae_feature_analysis.py \
  --config experiment/phase1/probe/config/phase3_selfaware_sae_feature_analysis.yaml
python experiment/phase1/probe/phase3_sae_behavior_feature_analysis.py \
  --config experiment/phase1/probe/config/phase3_selfaware_sae_behavior_feature_analysis.yaml
```

Treat outputs as plumbing/training/feature-screening evidence only. Candidate
features need row inspection, geometry, logit controls, and generated-answer
replay before being described as mechanisms.

For SelfAware extraction manifests, if using
`readiness_checks.require_extraction_manifest`, specify `label_counts`
explicitly (`known: 556`, `unknown: 677`). Omitting the field can be interpreted
as an expected empty map and fail before model loading.

## Behavior-Axis Path

Use layerwise behavior-axis scans when SAE features look entangled or when the
question is where behavior signal lives across `h_base`, `h_lora`, and `delta`:

```bash
python experiment/phase1/probe/phase3_behavior_axis_scan.py \
  --config experiment/phase1/probe/config/phase3_selfaware_behavior_axis_scan.yaml
python experiment/phase1/probe/phase3_behavior_axis_directions.py \
  --config experiment/phase1/probe/config/phase3_selfaware_behavior_axis_directions.yaml
```

For gold-backed behavior cells, materialize a generated-answer behavior panel
before scanning. Use a no-vector baseline generation pass with
`selection.probe_results` so rows carry aliases/answer values, then run:

```bash
python experiment/phase1/probe/phase3_gold_behavior_panel.py \
  --config experiment/phase1/probe/config/phase3_gold_kto_behavior_panel.yaml
```

Pass the resulting `rows.jsonl` as `extractions[].rows_path` in behavior-axis
scan/export configs. The tensor shards still come from `extraction_dir`; the
alternate rows file only supplies generated behavior labels and row filters.

Before running a behavior-axis scan on reused extraction rows, inspect
`source_arms` in the rows file and confirm the configured `behavior_arm` is
present and current. A hidden-state extraction can be valid while its embedded
row behavior labels come from an older eval manifest. In that case, materialize
a current `rows_path` override from the current scored eval rows and point both
the scan and direction-export configs at it.

Use calibrated-expression plane analysis to project behavior cells onto paired
damage axes after direction export:

```bash
python experiment/phase1/probe/phase3_calibrated_expression_plane.py \
  --config experiment/phase1/probe/config/phase3_selfaware_calibrated_expression_plane.yaml
```

When one-axis or simple multi-hook interventions collapse into generic refusal
pressure, run a multicell readout before designing more steering candidates:

```bash
python .skills/mech-interp-runner/scripts/phase3_cli.py multicell-readout \
  --config experiment/phase1/probe/config/phase3_gold_kto_multicell_readout.yaml
```

Compare rank-1 against low-rank and full readouts by behavior-cell macro
recall. Treat high readout accuracy as localization/screening evidence only;
it is not a causal steering result.

Use balanced class weighting for rare behavior-cell panels. Plain accuracy can
look good while the readout ignores `known_refused` or
`unknown_answered_wrong`; macro recall and per-cell recall are the decision
surface.

For larger rare-cell panels, build deterministic target row-key files before
extracting:

```bash
python experiment/phase1/probe/phase3_targeted_row_keys.py \
  --config experiment/phase1/probe/config/phase3_gold_kto_targeted_rare_cell_row_keys.yaml
```

Treat heuristic buckets such as known-low-confidence and unknown-answering as
candidate enrichment only. The generated-answer behavior panel is the source of
truth for actual behavior-cell membership.

After logit diagnostics on behavior-conditioned rows, aggregate by behavior
cell before interpreting:

```bash
python experiment/phase1/probe/phase3_logit_cell_analysis.py \
  --config experiment/phase1/probe/config/phase3_selfaware_calibrated_expression_kto_logit_cell_analysis.yaml
```

Then rank candidate arms against explicit behavior-cell sign goals:

```bash
python .skills/mech-interp-runner/scripts/phase3_cli.py logit-cell-sign-score \
  --config experiment/phase1/probe/config/phase3_selfaware_kto_cell_sign_score.yaml
```

Use sign scores as triage only. A candidate can satisfy the cell-level
next-token refusal pattern and still fail generated-answer replay.

Use `phase3_direction_transforms.py` for reusable direction transforms instead
of ad hoc vector math. For composite plane tests, prefer an explicit
`linear_combination` transform with named source direction IDs, weights, and a
target norm:

```yaml
transforms:
  - label: example_composite_normed
    method: linear_combination
    target_norm: 1.2142820358276367
    components:
      - source_direction_id: behavior_axis__...
        weight: -1.0
      - source_direction_id: behavior_axis__...
        weight: -1.25
```

Treat composite directions as candidate controls. A right-signed logit-cell
pattern still needs generated-answer replay and row-level flip inspection before
it counts as behavioral improvement.

Linear-combination components must share hidden dimension, role, and layer. For
multi-layer hypotheses, use a dedicated multi-layer intervention path rather
than forcing different-layer vectors into one transformed vector.

Use `orthogonalize_to` transforms when testing whether one same-layer behavior
axis can be separated from another protected axis before causal diagnostics:

```yaml
transforms:
  - label: example_repair_orthogonalized
    method: orthogonalize_to
    source_direction_id: behavior_axis__example_repair
    target_norm: 1.2142820358276367
    constraints:
      - source_direction_id: behavior_axis__protected_axis
```

The source and constraint directions must share hidden dimension, role, and
layer. Interpret removal fractions as geometry evidence only until the
orthogonalized vectors pass logit diagnostics and generated replay.

When a transform changes the conceptual contrast, set `contrast:` explicitly in
the transform config. Otherwise the output manifest can inherit the source
contrast, and candidate/sweep validation will fail with a contrast mismatch.

Multi-layer candidate configs use `multi_layer_components` instead of a
top-level `direction_file`. Each component must declare its own
`direction_manifest`, `direction_file`, `tensor_key`, `role`, `layer`,
`vector_sha256`, and `weight`. The live runner applies every component at the
final prompt token and records aggregate hook counts; for a two-component
28-row diagnostic, expect `intervention_applied_count_total: 56`.

Use signed component weights to encode the intended repair direction, then use
`activation_addition` as the source arm. Wrong-layer controls shift all
component layers by the same offset. Keep the cell-analysis gate unchanged:
multi-layer candidates must still improve damaged behavior cells while
preserving paired desired cells before generated replay.

Interpret behavior axes as candidate subspaces, not localized mechanisms. If
wrong-layer controls are comparable or stronger, export source axes across the
nearby layer window before claiming a source-layer effect.

Do not call `h_base` inside DPO/KTO extractions the original Qwen base. It is
the SFT-merged model before the preference adapter. True original-base
adapterless extraction is a separate fail-closed capability.

## Probability-Slice Diagnostics

For next-token probability slices, avoid treating every multi-token alias first
token as exact correctness. Qwen tokenization can split an answer like
`Ireland` into `I`, which collides with refusal openers.

For schema-constrained prompts, confirm the diagnostic token position still
matches the behavior question. If the prompt requires JSON output, a
final-prompt-token diagnostic usually probes the opening JSON token rather than
the answer/refusal text inside the `answer` field. Treat refusal-opener or
answer-alias deltas under that setup as uninformative unless the runner supports
an explicit answer-field prefix/position. Use generated-answer replay as the
behavior gate instead.

Use this default:

```yaml
logit_targets:
  groups:
    - name: answer_aliases
      source: row_aliases
      include_leading_space_variants: true
      include_multi_token_first_token: false
```

Use `include_multi_token_first_token: true` only when the explicit diagnostic
question is answer-start movement. Label it as first-token answer-start
evidence, not exact multi-token correctness.

After any scaled answer-start diagnostic:

- Stratify by known vs unknown labels.
- Check both mean movement and row-count movement.
- Require the desired label group to move refusal and answer-alias metrics in
  the right direction.
- Compare against wrong-layer and random matched-norm controls before making a
  source-specific claim.

Generated-answer replay is the behavioral gate. First-token answer-start
movement can be real while still loosening refusal into hallucinated answers.

When generation mode needs a wrong-layer-style control, use an explicit
shifted-layer candidate rather than calling unsupported logit-only controls.
Reuse the same direction artifact and vector hash, set the candidate `layer` to
the target intervention layer, and mark it with
`allow_direction_layer_override: true` plus a clear control note. Normal
candidate validation still fails closed on layer mismatches unless this flag is
present.

## Controls

Minimum logit-diagnostic controls:

- `no_vector_baseline`
- signed source intervention (`activation_addition` or `activation_subtraction`)
- `wrong_layer` or `wrong_layer_subtraction`
- `random_matched_norm`

Wrong-layer controls must be sign-matched to the source intervention. Do not
compare source subtraction against positive wrong-layer addition.

Keep wrong-layer offsets inside the model's valid hidden-state range. For a
source layer at the final hidden-state index, positive offsets can map past the
last decoder block and fail live execution.

If a sweep config overrides extraction readiness `label_counts`, treat the map
as an atomic assertion for that panel. Do not let labels from a template panel
leak into a different row manifest.

Template readiness checks often include `row_count` and `label_counts`. When a
sweep targets a new extraction panel, override both in `runner_overrides` before
live execution; otherwise the runner can correctly fail on the old template
shape before model loading.

For nearby-layer panels:

```yaml
control_settings:
  wrong_layer:
    layer_offsets: [-2, -1, 1, 2]
```

For random matched-norm seed panels:

```yaml
control_settings:
  random_matched_norm:
    seeds:
      - 20260620
      - 20260621
```

This expands one `random_matched_norm` control arm per seed.

Do not label a shuffled-label control unless there is a real shuffled-label
direction artifact or valid checked-in derivation path.

## Generated-Answer Replay

Use generation mode only for behavior gates after logit diagnostics identify a
candidate. Generation mode supports `no_vector_baseline`,
`activation_addition`, `activation_subtraction`, and `sign_flip`.

Require generated replay before claiming:

- answer recovery,
- reduced over-refusal,
- improved calibrated abstention,
- or user-facing behavioral improvement.

Score refusal, correctness, truthfulness, and per-row deltas against baseline.
Inspect changed rows manually, especially refusal-to-answer flips.
Interpret deltas against the replay's own no-vector baseline, not only the
behavior-cell labels used to select rows. Deterministic replay baselines can
drift from the earlier scored behavior overlay, so summaries should report
baseline and intervention counts side by side.

Use the replay analyzer for completed generation sweeps:

```bash
python experiment/phase1/probe/phase3_generation_replay_analysis.py \
  --root experiment/phase1/probe/analysis/example_generation_sweep \
  --out experiment/phase1/probe/analysis/example_generation_sweep/summary_latest
```

This writes `summary.json`, `summary.csv`, and `changed_rows.csv`. Treat the
automatic alias/refusal matching as triage; inspect changed rows before making
behavior claims.

## Validation

Use focused non-GPU checks after runner/config/skill edits:

```bash
python -m pytest experiment/phase1/probe/tests/test_phase3_causal_pilot_sweep.py \
  experiment/phase1/probe/tests/test_phase3_causal_pilot_runner.py \
  experiment/phase1/probe/tests/test_phase3_causal_pilot_dry_run.py -q
python -m pytest experiment/phase1/probe/tests/test_phase3_behavior_axis_scan.py \
  experiment/phase1/probe/tests/test_phase3_behavior_axis_directions.py \
  experiment/phase1/probe/tests/test_phase3_calibrated_expression_plane.py \
  experiment/phase1/probe/tests/test_phase3_logit_cell_analysis.py -q
python -m pytest experiment/phase1/probe/tests/test_phase3_sae_smoke.py \
  experiment/phase1/probe/tests/test_phase3_sae_train.py \
  experiment/phase1/probe/tests/test_phase3_sae_feature_analysis.py \
  experiment/phase1/probe/tests/test_phase3_sae_feature_directions.py \
  experiment/phase1/probe/tests/test_phase3_sae_behavior_feature_analysis.py -q
python -m py_compile experiment/phase1/probe/phase3_causal_pilot_sweep.py \
  experiment/phase1/probe/phase3_causal_pilot_aggregate.py \
  experiment/phase1/probe/phase3_causal_pilot_runner.py \
  experiment/phase1/probe/phase3_behavior_axis_scan.py \
  experiment/phase1/probe/phase3_behavior_axis_directions.py \
  experiment/phase1/probe/phase3_calibrated_expression_plane.py \
  experiment/phase1/probe/phase3_logit_cell_analysis.py
python bin/sync_skills.py --check
```
