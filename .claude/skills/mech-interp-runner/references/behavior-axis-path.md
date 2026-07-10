# Behavior-Axis Path

Load this when running layerwise behavior-axis scans, direction exports,
calibrated-expression plane analysis, multicell readouts, direction transforms,
and multi-layer interventions.

Use layerwise behavior-axis scans when SAE features look entangled or when the
question is where behavior signal lives across `h_base`, `h_lora`, and `delta`:

```bash
python experiment/phase1/probe/phase3_behavior_axis_scan.py \
  --config experiment/phase1/probe/config/phase3_selfaware_behavior_axis_scan.yaml
python experiment/phase1/probe/phase3_behavior_axis_directions.py \
  --config experiment/phase1/probe/config/phase3_selfaware_behavior_axis_directions.yaml
```

## Gold-backed behavior panels

For gold-backed behavior cells, materialize a generated-answer behavior panel
before scanning. Use a no-vector baseline generation pass with
`selection.probe_results` so rows carry aliases/answer values, then run:

```bash
python experiment/phase1/probe/phase3_gold_behavior_panel.py \
  --config archive/experiment/phase1/probe/config/gold-kto-calibrated-expression/phase3_gold_kto_behavior_panel.yaml
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

## Calibrated-expression plane and multicell readout

Use calibrated-expression plane analysis to project behavior cells onto paired
damage axes after direction export:

```bash
python experiment/phase1/probe/phase3_calibrated_expression_plane.py \
  --config archive/experiment/phase1/probe/config/selfaware-geometry-and-subspace/phase3_selfaware_calibrated_expression_plane.yaml
```

When one-axis or simple multi-hook interventions collapse into generic refusal
pressure, run a multicell readout before designing more steering candidates:

```bash
python .skills/mech-interp-runner/scripts/mechinterp_cli.py multicell-readout \
  --config archive/experiment/phase1/probe/config/gold-kto-calibrated-expression/phase3_gold_kto_multicell_readout.yaml
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

## Logit-cell aggregation and sign scoring

After logit diagnostics on behavior-conditioned rows, aggregate by behavior
cell before interpreting:

```bash
python experiment/phase1/probe/phase3_logit_cell_analysis.py \
  --config archive/experiment/phase1/probe/config/selfaware-calibrated-expression-kto-panels/phase3_selfaware_calibrated_expression_kto_logit_cell_analysis.yaml
```

Then rank candidate arms against explicit behavior-cell sign goals:

```bash
python .skills/mech-interp-runner/scripts/mechinterp_cli.py logit-cell-sign-score \
  --config archive/experiment/phase1/probe/config/selfaware-calibrated-expression-kto-panels/phase3_selfaware_kto_cell_sign_score.yaml
```

Use sign scores as triage only. A candidate can satisfy the cell-level
next-token refusal pattern and still fail generated-answer replay.

## Direction transforms

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

## Multi-layer candidates

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
