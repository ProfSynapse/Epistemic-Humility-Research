# RUNBOOK: J-lens on a trained checkpoint plus rule-selected mid-band refusal-axis ablation

Status of this document: DRAFT, built alongside the still-unsigned cell. Every
command below assumes the canonical checkout
(`/home/profsynapse/code/Epistemic-Humility-Research`) as cwd and the repo
root on `PYTHONPATH` where a script needs it. Do not launch any GPU/docker
stage until the cell is signed (`bin/exp sign jlens-trained-checkpoint-midband-ablation`)
and the lead has cleared the GPU (currently occupied by another cell).

All generated artifacts (`analysis/**`) are gitignored per this cell's
`.gitignore`; nothing this runbook produces is committed automatically.

## Stage 0 -- prerequisites

- `HF_TOKEN` in the environment (read automatically by `huggingface_hub`,
  needed only for Stage 1's private-pool fetch; documented in the pinned
  original `experiments/j-space-localization-qwen3-4b/jlens.py`'s own
  docstring, ported unchanged into `configs/jlens_trained.py`).
- Local checkpoint dirs present on disk:
  `scratch/schema_response_confidence/runs/sft_schema_clean_seed1_full/20260623_123624/Qwen3-4B-bnb-4bit/merged-16bit`
  (base) and
  `scratch/schema_response_confidence/runs/schema_clean_sft_grpo_v2_seed1_full/20260624_095831/final_model`
  (adapter) -- same lineage as `experiments/caution-ablation-rederivation/`.
- Archived extraction + behavior rows present:
  `archive/experiment/phase1-data/probe/qwen3-4b-clean-sft-grpo-v2-seed1-selfaware/hidden_states_selfaware_clean_sft_grpo_v2_full/extraction__55254a04aa1f/`
  (manifest verified, 1233 rows x 37 layers) and
  `archive/experiment/phase1-data/probe/analysis/current_selfaware_behavior_rows/clean_sft_grpo_v2/rows.jsonl`
  (known_refused n=168, known_correct_answered n=373).
- `mkdir -p experiments/jlens-trained-checkpoint-midband-ablation/analysis/{results,directions,intervention/instantiated_configs,logs}`

## Stage 1 -- corpus build (CPU)

Rebuilds the SAME deterministic 1000-row corpus the raw-base profile used
(same source pool, same seed, same n -- see `configs/jlens_trained.py`'s
`build_corpus`/`load_corpus`, a byte-for-byte port of the pinned original's
corpus machinery).

```
python3 experiments/jlens-trained-checkpoint-midband-ablation/configs/jlens_trained.py \
  build-corpus \
  --out experiments/jlens-trained-checkpoint-midband-ablation/analysis/corpus_pool.jsonl \
  --n 1000 --seed 20260707
```

## Stage 2 -- J-lens smoke (GPU, ~15 min)

JT-G0 integrity gate: PASS requires final-layer J-lens vs direct unembed on
the trained substrate at **cosine >= 0.95 and top-10 overlap >= 0.7** (the
raw-base reference values were cosine 0.9811 / top-10 overlap 0.82 -- these
JT-G0 thresholds are a lower bar than the raw-base reference, not equal to
it). **Fail = stop; no ablation arms run.**

```
docker run --rm -d \
  --name jlens-trained-smoke-$(date -u +%Y%m%dT%H%M%SZ) \
  --gpus all --ipc=host --user 1000:1000 --entrypoint python3 \
  -v "$HOME/.cache/huggingface:/home/unsloth/.cache/huggingface" \
  -v "/home/profsynapse/code/Epistemic-Humility-Research:/workspace/repo" \
  -w /workspace/repo \
  --env HF_HOME=/home/unsloth/.cache/huggingface \
  --env HUGGINGFACE_HUB_CACHE=/home/unsloth/.cache/huggingface \
  --env HF_TOKEN \
  --env PYTHONPATH=/workspace/repo/synaptic-tuner \
  unsloth/unsloth:latest \
  experiments/jlens-trained-checkpoint-midband-ablation/configs/jlens_trained.py smoke \
  --model /workspace/repo/scratch/schema_response_confidence/runs/sft_schema_clean_seed1_full/20260623_123624/Qwen3-4B-bnb-4bit/merged-16bit \
  --adapter /workspace/repo/scratch/schema_response_confidence/runs/schema_clean_sft_grpo_v2_seed1_full/20260624_095831/final_model \
  --corpus /workspace/repo/experiments/jlens-trained-checkpoint-midband-ablation/analysis/corpus_pool.jsonl \
  --n-prompts 1000 --n-test-dirs 5 --seed 20260707 \
  --out /workspace/repo/experiments/jlens-trained-checkpoint-midband-ablation/analysis/results/smoke_trained.json
```

Synchronous poll pattern (same shape reused for every GPU stage below --
launch detached, follow logs to a file under `analysis/logs/`, block on
container exit, then remove the container):

```
CONTAINER=<name printed by `docker run -d` above>
LOGFILE=experiments/jlens-trained-checkpoint-midband-ablation/analysis/logs/${CONTAINER}.log
docker logs -f "$CONTAINER" > "$LOGFILE" 2>&1 &
LOGPID=$!
until [ "$(docker inspect -f '{{.State.Status}}' "$CONTAINER" 2>/dev/null)" = "exited" ]; do sleep 30; done
wait "$LOGPID"
docker inspect -f '{{.State.ExitCode}}' "$CONTAINER"   # 0 required
docker rm "$CONTAINER"
```

Read `analysis/results/smoke_trained.json`'s `mean_cosine_sim` /
`mean_top10_overlap` against the JT-G0 thresholds above before proceeding.

## Stage 3 -- J-lens profile (GPU, ~2.5 h)

Identical settings to the raw-base profile for comparability: same corpus
manifest/seed, 5 random directions, the same 13-point grid, plain user-turn
render (`enable_thinking: false` is baked into `render_prompt`, not a flag).

```
docker run --rm -d \
  --name jlens-trained-profile-$(date -u +%Y%m%dT%H%M%SZ) \
  --gpus all --ipc=host --user 1000:1000 --entrypoint python3 \
  -v "$HOME/.cache/huggingface:/home/unsloth/.cache/huggingface" \
  -v "/home/profsynapse/code/Epistemic-Humility-Research:/workspace/repo" \
  -w /workspace/repo \
  --env HF_HOME=/home/unsloth/.cache/huggingface \
  --env HUGGINGFACE_HUB_CACHE=/home/unsloth/.cache/huggingface \
  --env HF_TOKEN \
  --env PYTHONPATH=/workspace/repo/synaptic-tuner \
  unsloth/unsloth:latest \
  experiments/jlens-trained-checkpoint-midband-ablation/configs/jlens_trained.py profile \
  --model /workspace/repo/scratch/schema_response_confidence/runs/sft_schema_clean_seed1_full/20260623_123624/Qwen3-4B-bnb-4bit/merged-16bit \
  --adapter /workspace/repo/scratch/schema_response_confidence/runs/schema_clean_sft_grpo_v2_seed1_full/20260624_095831/final_model \
  --corpus /workspace/repo/experiments/jlens-trained-checkpoint-midband-ablation/analysis/corpus_pool.jsonl \
  --n-prompts 1000 --seed 20260707 \
  --layers 2,5,8,11,14,17,20,23,26,29,32,35,36 \
  --n-random-dirs 5 \
  --out /workspace/repo/experiments/jlens-trained-checkpoint-midband-ablation/analysis/results/profile_trained.json
```

Follow with the same synchronous poll pattern as Stage 2 (new container
name, log file `profile_trained-*.log`). The runner flushes a partial JSON
after every completed layer, so progress is visible on disk mid-run.

## Stage 3.5 -- site-selection rule (CPU, worked example)

Fixed at signing per `AMENDMENT.md` ("Site-selection rule"); never revised
after any result. Interior window = grid points `{14, 17, 20, 23, 26, 29}`
(relative depth hs/36 in [0.35, 0.85]). Early points = `{2, 5, 8, 11}`.

```
python3 - <<'PY'
import json
import statistics

profile = json.load(open(
    "experiments/jlens-trained-checkpoint-midband-ablation/analysis/results/profile_trained.json"
))
per_layer = profile["per_layer"]

interior = [14, 17, 20, 23, 26, 29]
early = [2, 5, 8, 11]

interior_vals = {hs: per_layer[str(hs)]["effective_dim_frac_mean"] for hs in interior}
early_vals = [per_layer[str(hs)]["effective_dim_frac_mean"] for hs in early]

interior_max = max(interior_vals.values())
early_median = statistics.median(early_vals)

# NO-INTERIOR-BAND BRANCH: declare "no interior band" if interior_max is
# below 1.5x the early median. In that branch the ablation still runs, at
# the fixed fallback site hs23 (the raw-base rule site), reframed as a
# band-portability probe.
no_band = interior_max < 1.5 * early_median

if no_band:
    site = 23
    rule_note = "NO-INTERIOR-BAND branch: fixed fallback site hs23"
else:
    # RULE (shallow band edge): shallowest interior point whose
    # effective_dim_frac_mean is at least 0.5x the interior maximum.
    threshold = 0.5 * interior_max
    site = min(hs for hs in interior if interior_vals[hs] >= threshold)
    rule_note = f"shallow-band-edge rule, threshold={threshold:.6f}"

# VOID GUARD: cannot fire under the 0.85 depth cap (deepest selectable is
# hs29, which is 6 layers short of hs35) -- asserted defensively anyway.
assert abs(site - 35) > 2, (
    f"VOID GUARD fired: selected site hs{site} is within 2 layers of hs35; "
    "the mid-band-vs-late contrast is void, report the profile only."
)

print(f"interior_max={interior_max:.6f} early_median={early_median:.6f} "
      f"no_band={no_band} ({rule_note}) -> SITE=hs{site}")
PY
```

Record the printed `SITE` value and the branch taken (band vs no-band) in
`NOTEBOOK.md` before proceeding -- this is the JT-G1 "band present vs
absent" call input.

## Stage 4 -- direction fits (CPU, minutes)

Fits the raw mass-mean refusal-axis direction at every interior grid point
in one pass: whichever layer equals the Stage 3.5 `SITE` is the BINDING fit
(pos_cell `known_refused`, neg_cell `known_correct_answered`, source
`h_lora`, layer = SITE -- the JT-G0 requirement); the other five are
descriptive-only and feed the reported AUROC-by-depth profile, never site
selection (site selection already happened in Stage 3.5, off the J-lens
profile, not off these fits).

```
for L in 14 17 20 23 26 29; do
  python3 experiments/common/mechinterp/residual_caution_direction.py \
    --extraction-dir archive/experiment/phase1-data/probe/qwen3-4b-clean-sft-grpo-v2-seed1-selfaware/hidden_states_selfaware_clean_sft_grpo_v2_full/extraction__55254a04aa1f/ \
    --behavior-rows archive/experiment/phase1-data/probe/analysis/current_selfaware_behavior_rows/clean_sft_grpo_v2/rows.jsonl \
    --layer "$L" --source h_lora \
    --out experiments/jlens-trained-checkpoint-midband-ablation/analysis/directions/caution_direction_L${L}_seed1.json
done
```

Each output JSON already carries `pos_cell`, `neg_cell`, `source`, `layer`,
`n_pos`/`n_neg`, and `prompt_token_auroc` (in-sample construction sanity,
not a held-out claim) -- confirm `n_pos=168`, `n_neg=373` on every file
(JT-G0 "archived extraction and behavior rows load with verified manifest
and expected counts").

## Stage 5 -- template instantiation

The pinned template
(`configs/phase3_jlens_midband_refusal_axis_intervention_seed1.TEMPLATE.yaml`)
is never edited or run directly. Substitute the literal `{SITE}` placeholder
with the Stage 3.5 value and write the instantiated copy under `analysis/`:

```
SITE=<value printed by Stage 3.5>
sed "s/{SITE}/${SITE}/g" \
  experiments/jlens-trained-checkpoint-midband-ablation/configs/phase3_jlens_midband_refusal_axis_intervention_seed1.TEMPLATE.yaml \
  > experiments/jlens-trained-checkpoint-midband-ablation/analysis/intervention/instantiated_configs/phase3_jlens_midband_refusal_axis_intervention_seed1_L${SITE}.yaml

# Confirm the ONLY two lines that differ from the template are
# caution_direction and output.root:
diff experiments/jlens-trained-checkpoint-midband-ablation/configs/phase3_jlens_midband_refusal_axis_intervention_seed1.TEMPLATE.yaml \
     experiments/jlens-trained-checkpoint-midband-ablation/analysis/intervention/instantiated_configs/phase3_jlens_midband_refusal_axis_intervention_seed1_L${SITE}.yaml
```

## Stage 6 -- four-arm intervention (GPU, ~50 min)

Same parity-locked legacy HF greedy intervention stack as the governed
rederivation (`experiments/common/mechinterp/residual_intervention_runner.py`,
`instrument.engine_exception: {kind: parity-locked}` in the governed cell --
this cell reuses that instrument unmodified, not a fresh implementation).
Baseline arm re-checks the 0.994 integrity floor (JT-G0).

```
CONTAINER=jlens-trained-intervention-$(date -u +%Y%m%dT%H%M%SZ)
docker run --rm -d \
  --name "$CONTAINER" \
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
  --config experiments/jlens-trained-checkpoint-midband-ablation/analysis/intervention/instantiated_configs/phase3_jlens_midband_refusal_axis_intervention_seed1_L${SITE}.yaml
```

Then the same synchronous poll pattern as Stage 2/3 (log file
`analysis/logs/${CONTAINER}.log`). Output lands at
`analysis/intervention/jlens_midband_refusal_axis_intervention_L${SITE}/{rows.jsonl,summary.json,checkpoint.json}`
per the instantiated config's `output.root` (resolved relative to the
container's `/workspace/repo` mount, i.e. this cell's own `analysis/`).
`summary.json`'s `analysis.by_arm.<arm_id>.<behavior_cell>.refusal_rate` /
`.correct_rate` give the aggregate rates the AMENDMENT's Prediction/
Falsifier/JT-G1 thresholds are read against directly; no separate
aggregation script is needed for the headline call.

## Stage 7 -- paired comparison vs L35 (CPU, descriptive only, no gate)

Row-level paired comparison of this cell's mid-band `ablate` arm against
the existing L35 rederivation rows (path from `experiment.yaml` inputs):
`experiments/caution-ablation-rederivation/analysis/current_clean_grpo_v2_caution_residual_intervention/rows.jsonl`
(2164 rows on disk; greedy deterministic, same checkpoint, same rows filter,
same instrument -- `residual_intervention_runner.py`'s output schema, see
Stage 6). **Pre-stated fallback** if those gitignored rows are gone at run
time: re-run the L35 `ablate` arm under the archived config
`experiments/caution-ablation-rederivation/configs/phase3_current_clean_grpo_v2_caution_residual_intervention.yaml`
with the sha-pinned direction
(`caution_direction_L35.json` sha256
`9eb2a8c91dd950e669065f7a80b1424a0c3c24c389ed2a9ea1f98f13072d8785`, pinned
in that cell's `gates.yaml` `ca_g0.direction_sha_match`) -- see this
report's flag section on the config's own 4-arm ~49 min runtime vs the
AMENDMENT's ~12 min single-arm estimate for that fallback, which the lead
should resolve before relying on the fallback path's time budget.

Both rows.jsonl files share the exact schema `residual_intervention_runner.py`
writes: `probe_pool_row_key`, `arm_id`, `arm_mode`, `arm_alpha`, `label`,
`behavior_cell`, `refused`, `correct`, `truthful`, `generated_answer`. Sketch
(no committed script -- descriptive comparison only, carries no gate per
AMENDMENT.md JT-G1):

```python
import json

def load_ablate_rows(path, behavior_cells=("known_refused", "known_correct_answered")):
    by_key = {}
    with open(path) as fh:
        for line in fh:
            rec = json.loads(line)
            if rec["arm_id"] != "ablate" or rec.get("behavior_cell") not in behavior_cells:
                continue
            by_key[rec["probe_pool_row_key"]] = rec
    return by_key

midband = load_ablate_rows(
    "experiments/jlens-trained-checkpoint-midband-ablation/analysis/"
    f"intervention/jlens_midband_refusal_axis_intervention_L{SITE}/rows.jsonl")
l35 = load_ablate_rows(
    "experiments/caution-ablation-rederivation/analysis/"
    "current_clean_grpo_v2_caution_residual_intervention/rows.jsonl")

paired_keys = sorted(set(midband) & set(l35))
for cell in ("known_refused", "known_correct_answered"):
    cell_keys = [k for k in paired_keys if midband[k]["behavior_cell"] == cell]
    mid_refused = sum(midband[k]["refused"] for k in cell_keys)
    l35_refused = sum(l35[k]["refused"] for k in cell_keys)
    n = len(cell_keys)
    print(f"{cell}: n_paired={n} "
          f"midband_refusal_rate={mid_refused / n:.4f} "
          f"l35_refusal_rate={l35_refused / n:.4f} "
          f"delta_pts={(mid_refused - l35_refused) / n * 100:.2f}")
```

"Cost per row" is read from the two runs' wall-clock (container start/exit
timestamps captured in `analysis/logs/*.log`, or `docker inspect`'s
`.State.StartedAt`/`.State.FinishedAt`) divided by each run's
`total_units` from its own `summary.json`, not from a per-row timestamp
field (the runner does not record one).

## JT-G0 (integrity, pre-outcome stop) -- verbatim from AMENDMENT.md

Smoke passes (final-layer J-lens tracks the direct unembed on the trained
substrate at cosine >= 0.95 and top-10 overlap >= 0.7); archived extraction
and behavior rows load with verified manifest and expected counts (1233
rows; 168/373 cells); binding direction fit carries pos_cell known_refused,
neg_cell known_correct_answered, source h_lora, and the rule-selected
layer; intervention baseline arm reproduces 0.994 within 0.02; full
coverage of the declared row set in every arm.

## JT-G1 (call, per branch) -- verbatim from AMENDMENT.md

- Band: interior band present (interior max >= 1.5x early median) vs
  absent.
- Ablation at the rule site: reproduced (<= 0.10 with specificity intact),
  partial (0.10-0.30 exclusive, or specificity break), not-transferred
  (>= 0.30).
- The paired mid-band-vs-L35 release comparison is reported descriptively
  (releases, specificity, cost per row) and carries no gate: L35 sits at
  0.0298 and a rate-delta bet would have ~3 points of headroom.

Either way the governed paper-3 numbers and the seed-2 confirmatory cell
are untouched by this cell (pre-stated; exploratory tier).
