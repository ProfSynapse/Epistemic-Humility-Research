# Refusal-axis ablation fresh-seed confirmatory — RUNBOOK

Prep-only artifact. Written by the PREP builder per the lead's task; the lead
reviews, signs (`bin/exp sign`), and separately authorizes the GPU run. No
stage below has been executed. All commands assume the canonical checkout
`/home/profsynapse/code/Epistemic-Humility-Research` (never `/mnt/f`).

## TRUE execution order (differs from AMENDMENT.md's prose numbering)

AMENDMENT.md lists the recipe as "1. Behavior rows, 2. Extraction, 3. Fit,
4. Intervention." That is the conceptual/data-lineage order, but the
behavior-rows JOIN script (AMENDMENT stage 1) consumes the extraction's own
`rows.jsonl` (AMENDMENT stage 2's output) as one of its two inputs, so it is
MECHANICALLY DEPENDENT on extraction and must run second, not first. The
runner should execute in this order:

1. **(pre-existing, no run needed)** Seed-2 SelfAware full generation+eval.
   Already resolved by `experiments/grpo-three-seed-confirmatory`
   (byte-identical response-confidence prompt contract). Confirmed on disk:
   `archive/experiment/phase1/eval/results_grpo3seed_response_confidence_selfaware_clean_sft_grpo_v2_seed2_full_4b/clean_schema_sft_grpo_v2_seed2__selfaware/scored_rows.jsonl`
   (3369 lines, verified present and readable during prep).
2. **Extraction** (AMENDMENT stage 2; GPU) —
   `configs/extraction_hidden_state_selfaware_manifest_clean_sft_grpo_v2_seed2_full.yaml`.
3. **Behavior rows** (AMENDMENT stage 1; CPU, no GPU) —
   `configs/behavior_rows_build_clean_sft_grpo_v2_seed2.py`, consuming
   stage 2's `rows.jsonl` and stage 1(pre-existing)'s `scored_rows.jsonl`.
4. **Fit** (AMENDMENT stage 3; CPU, no GPU) —
   `experiments/common/mechinterp/residual_caution_direction.py` (CLI-only,
   no config file exists for this stage; exact invocation below).
5. **Intervention** (AMENDMENT stage 4; GPU) —
   `configs/phase3_current_clean_grpo_v2_caution_residual_intervention_seed2.yaml`.

## Stage 2 — Extraction

Config: `configs/extraction_hidden_state_selfaware_manifest_clean_sft_grpo_v2_seed2_full.yaml`.

Driver: `experiments/common/knowledge_probe/hidden_state_probe.py` (the live,
renamed home of the phase1_probe hidden-state harness). Confirmed self-
contained for this launch: running it directly as `python3
experiments/common/knowledge_probe/hidden_state_probe.py` puts that
directory on `sys.path[0]` (Python's own script-dir auto-add), so the bare
`import backends` in `hs_backends.py`'s `TransformersPeftBackend.render()`
resolves straight to `experiments/common/knowledge_probe/backends.py` with
NO symlink needed — verified directly (`python3 -c "import backends;
print(backends.__file__)"` after inserting that dir onto sys.path resolves
to that exact file). This differs from stage 4 below, which does need a
shim.

Docker pattern (mirrors `experiments/caution-ablation-rederivation`'s proven
configs-1/2 launch: `unsloth/unsloth:latest`, `--user 1000:1000` because the
image's default uid 1001 cannot write into this host's uid-1000 dirs):

```
docker run --rm \
  --name refusal-axis-ablation-confirmatory-extraction-seed2-<UTC timestamp> \
  --gpus all --ipc=host --user 1000:1000 --entrypoint python3 \
  -v "$HOME/.cache/huggingface:/home/unsloth/.cache/huggingface" \
  -v "/home/profsynapse/code/Epistemic-Humility-Research:/workspace/repo" \
  -w /workspace/repo \
  --env HF_HOME=/home/unsloth/.cache/huggingface \
  --env HUGGINGFACE_HUB_CACHE=/home/unsloth/.cache/huggingface \
  --env HF_TOKEN \
  unsloth/unsloth:latest \
  experiments/common/knowledge_probe/hidden_state_probe.py \
  --config experiments/refusal-axis-ablation-confirmatory/configs/extraction_hidden_state_selfaware_manifest_clean_sft_grpo_v2_seed2_full.yaml
```

No `PYTHONPATH` override needed (unlike stage 4) — do not copy the stage-4
`PYTHONPATH=/workspace/repo/synaptic-tuner` env var onto this launch, it is
unrelated to this driver.

Expected artifacts (under `analysis/hidden_states/`, gitignored):

- `qwen3-4b-clean-sft-grpo-v2-seed2-selfaware/hidden_states_selfaware_clean_sft_grpo_v2_seed2_full/extraction__<sha>/manifest.json`
- same dir: `rows.jsonl`, plus per-row `*__h_base.safetensors` /
  `*__h_lora.safetensors` / `*__delta.safetensors`.

RC-G0 before proceeding:

- Container exits 0.
- `manifest.json`: `status: "ok"`, `verified: true`,
  `active_adapter_name: "clean_sft_grpo_v2_seed2"`,
  `adapter_path` matches the seed-2 final_model path above,
  `base_model_id`/`base_model_hash` match the seed-2 merged base,
  `token_position_rule: "final_prompt_token"`, `persist_dtype: "float32"`.
- Row count in `rows.jsonl` matches the frozen SelfAware manifest's full
  row count for the `clean_sft_grpo_v2_seed2` active arm: 1233 rows,
  matching seed 1's `extraction__55254a04aa1f/rows.jsonl` exactly (verified
  by direct line count during this prep pass) — same frozen manifest, same
  expected count, since row selection is dataset-level and
  checkpoint-agnostic.
- No question/generation text leaked outside `analysis/` (git status clean
  of new tracked files).

## Stage 1 (behavior rows; runs after stage 2) — Behavior-rows join

Script: `configs/behavior_rows_build_clean_sft_grpo_v2_seed2.py` (CPU-only,
no GPU, no model load; imports only the pure `stable_row_key`/`behavior_cell`
functions from the shared
`experiments/common/scripts/build_current_selfaware_behavior_rows.py`, never
its `OUT_ROOT`-bound `materialize()`/`main()`).

```
python3 experiments/refusal-axis-ablation-confirmatory/configs/behavior_rows_build_clean_sft_grpo_v2_seed2.py \
  --source-rows experiments/refusal-axis-ablation-confirmatory/analysis/hidden_states/qwen3-4b-clean-sft-grpo-v2-seed2-selfaware/hidden_states_selfaware_clean_sft_grpo_v2_seed2_full/extraction__<sha-from-stage-2>/rows.jsonl \
  --scored-rows archive/experiment/phase1/eval/results_grpo3seed_response_confidence_selfaware_clean_sft_grpo_v2_seed2_full_4b/clean_schema_sft_grpo_v2_seed2__selfaware/scored_rows.jsonl \
  --out experiments/refusal-axis-ablation-confirmatory/analysis/behavior_rows/clean_sft_grpo_v2_seed2/rows.jsonl
```

Expected artifacts: `analysis/behavior_rows/clean_sft_grpo_v2_seed2/rows.jsonl`
+ sibling `summary.json` (aggregate counts only).

RC-G0 before proceeding:

- Script exits 0 with zero `missing` keys (the join raises `ValueError` and
  stops on any coverage gap — do not catch and continue).
- `summary.json.behavior_cell_counts` includes non-trivial `known_refused`
  and `known_correct_answered` counts (the two cells the fit and
  intervention stages consume). Seed 1's
  `archive/experiment/phase1-data/probe/analysis/current_selfaware_behavior_rows/clean_sft_grpo_v2/summary.json`
  counts (row_count 1233; known_refused 168, known_correct_answered 373,
  known_answered_wrong 15, unknown_refused 676, unknown_answered_wrong 1;
  mean_stated_confidence 0.8146) are a sanity-magnitude reference only, not
  an exact-match requirement — seed-2 behavior can legitimately differ.

## Stage 3 — Fit (raw mass-mean refusal-axis direction)

No config file exists for this stage — `residual_caution_direction.py` is
argparse-only. CPU-only, no GPU, deterministic (mass-mean, no fit
randomness).

```
python3 experiments/common/mechinterp/residual_caution_direction.py \
  --extraction-dir experiments/refusal-axis-ablation-confirmatory/analysis/hidden_states/qwen3-4b-clean-sft-grpo-v2-seed2-selfaware/hidden_states_selfaware_clean_sft_grpo_v2_seed2_full/extraction__<sha-from-stage-2> \
  --behavior-rows experiments/refusal-axis-ablation-confirmatory/analysis/behavior_rows/clean_sft_grpo_v2_seed2/rows.jsonl \
  --layer 35 \
  --source h_lora \
  --out experiments/refusal-axis-ablation-confirmatory/analysis/directions/caution_direction_L35_seed2.json
```

**SCHEMA-VERSION FLAG (report this to the lead, do not silently resolve):**
the script's live `SCHEMA_VERSION` constant is
`"mechinterp-residual-caution-direction/v1"`, NOT
`"phase3-residual-caution-direction/v1"` — the schema string recorded in the
seed-1 direction file this cell is meant to mirror
(`caution_direction_L35.json`'s own `schema_version` field, and the
AMENDMENT's own prose: "output schema phase3-residual-caution-direction/v1").
No script anywhere in this checkout currently emits the literal
`"phase3-residual-caution-direction/v1"` string for a RAW (non-perp)
direction — only `caution_perp`-specific scripts
(`archive/experiment/phase1/probe/amendments/amendment_an_refit_caution_perp.py`)
still use that string. This is very likely the SAME class of drift the
rederivation cell found in `backends.py` (a rename that updated the constant
but never touched frozen historical artifacts), not a functional
difference — `fit()`'s math (mass-mean contrast, `pos_cell: known_refused`,
`neg_cell: known_correct_answered`, layer 35) is unchanged and matches the
AMENDMENT's design exactly. Flagging because the OUTPUT JSON's
`schema_version` field will read differently than seed 1's own file, and the
AMENDMENT text names the older string explicitly.

Expected artifact: `analysis/directions/caution_direction_L35_seed2.json`
(schema fields: `layer: 35`, `block: 34`, `source: "h_lora"`, `pos_cell:
"known_refused"`, `neg_cell: "known_correct_answered"`, `n_pos`, `n_neg`,
`prompt_token_auroc`).

RC-G0 before proceeding: script exits 0; `n_pos`/`n_neg` match stage 1's
`known_refused`/`known_correct_answered` counts exactly; `prompt_token_auroc`
recorded (in-sample sanity, not a held-out claim — do not gate on it, per
the script's own docstring).

## Stage 4 — Intervention (four arms)

Config: `configs/phase3_current_clean_grpo_v2_caution_residual_intervention_seed2.yaml`.

Driver: `experiments/common/mechinterp/residual_intervention_runner.py`.
UNLIKE stage 2, this driver inserts `archive/experiment/phase1/probe` onto
`sys.path` internally (its own `PROBE_DIR` constant), so its bare `import
backends` needs the ONE symlink the caution-ablation-rederivation cell's
lead authorized:
`archive/experiment/phase1/probe/backends.py -> ../../../../experiments/common/knowledge_probe/backends.py`.
Confirmed still present on disk during this prep pass (`ls -la`
resolved it to the correct target) — verify again immediately before
launch rather than assuming it persisted; it is untracked/uncommitted
(environment-level, not a repo file) and could be removed by an unrelated
cleanup.

Docker pattern (identical to the rederivation cell's configs-1/2 launch,
mount fixed at `/workspace/repo` because `model.model_name` is a hardcoded
absolute in-container path):

```
docker run --rm \
  --name refusal-axis-ablation-confirmatory-intervention-seed2-<UTC timestamp> \
  --gpus all --ipc=host --user 1000:1000 --entrypoint python3 \
  -v "$HOME/.cache/huggingface:/home/unsloth/.cache/huggingface" \
  -v "/home/profsynapse/code/Epistemic-Humility-Research:/workspace/repo" \
  -w /workspace/repo \
  --env HF_HOME=/home/unsloth/.cache/huggingface \
  --env HUGGINGFACE_HUB_CACHE=/home/unsloth/.cache/huggingface \
  --env HF_TOKEN \
  --env PYTHONPATH=/workspace/repo/synaptic-tuner \
  unsloth/unsloth:latest \
  experiments/common/mechinterp/residual_intervention_runner.py \
  --config experiments/refusal-axis-ablation-confirmatory/configs/phase3_current_clean_grpo_v2_caution_residual_intervention_seed2.yaml
```

4 arms (baseline, ablate, shift_minus2, shift_plus2) x 2 cells
(known_refused, known_correct_answered), full row set, no `--fresh` (this
cell's output dir is empty on first launch, so resume semantics are
equivalent to a fresh run).

Expected artifacts (gitignored):
`analysis/intervention/current_clean_grpo_v2_seed2_caution_residual_intervention/`
— `summary.json`, `rows.jsonl`, one entry per (arm, cell, row).

RC-G0 (integrity, pre-outcome stop, per AMENDMENT.md):

- Container exits 0; full coverage of the seed-2 behavior-cell row set in
  every arm (4 arms x 2 cells, row counts matching stage 1's
  `known_refused`/`known_correct_answered` counts exactly, same shape as
  the seed-1 rederivation's 4 x 541 = 2164 check).
- Baseline arm `known_refused` refusal rate >= 0.97 (AMENDMENT's explicit
  RC-G0 floor; seed-1 read 0.994 — this is the pre-outcome integrity gate,
  separate from the confirmatory RC-G1 call on the ablate arm).

RC-G1 (confirmatory call, fixed in AMENDMENT.md, never retuned): ablate-arm
`known_refused` refusal rate at or below 0.10 AND specificity intact
(`known_correct_answered` induced refusal at or below 0.05, correct-rate
drop at or below 0.05) = CONFIRMED. (0.10, 0.30) or any specificity break =
NOT CONFIRMED. At or above 0.30 = falsifier fired (per AMENDMENT.md
Falsifier section).

## Open items for the lead (not resolved by this prep pass)

1. **Schema-version drift** (stage 3, detailed above) — accept the live
   script's `mechinterp-residual-caution-direction/v1` output as-is, or
   require a byte-identical `phase3-residual-caution-direction/v1` string
   before signing.
2. **Extraction prompt mismatch, inherited from seed 1** (stage 2, detailed
   in that config's header comment) — the extraction's rendered prompt is
   the harness's generic default, not the response-confidence contract that
   produced the behavior labels being read off. This is a pre-existing
   property of the seed-1 recipe being mirrored, not introduced here; flagged
   for awareness since the AMENDMENT's design prose describes "prompt
   contract (response-confidence, byte-identical prompt text)" for the
   pipeline as a whole.
3. **`adapter_name` relabeled** in the stage-4 config
   (`clean_sft_grpo_v2_seed2` vs seed 1's `clean_sft_grpo_v2`) to avoid
   collision with seed-1 artifact names; this is an internal generation-tag
   string only (not a path, not a direction/row/output field), but flagged
   since the AMENDMENT says "only substrate/direction/row/output paths
   changed."
