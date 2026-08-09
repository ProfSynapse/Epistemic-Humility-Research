# ood-breadth-beyond-selfaware -- launch sequence

Operating record for the run_plan stages in `cell.yaml`. This is a reusable
operating spec, not a claims surface; the signed prose lives in
`AMENDMENT.md`, the machine state in `experiment.yaml`, the pinned thresholds
in `gates.yaml`. Every stage below cites the cell.yaml/gates.yaml line it
implements. Run everything from the canonical checkout
(`/home/profsynapse/code/Epistemic-Humility-Research`); the shell resets its
cwd between calls, so `cd` there explicitly first every time.

GPU launch requires explicit PI approval naming the exact stages and lane
(cell.yaml `run_plan.launch_authority`). Nothing below authorizes itself.

## Stage 0 -- screen and commit manifests (CPU, no gate on the stage itself; the screen IS G0)

```
python3 experiments/ood-breadth-beyond-selfaware/screen_ood_surfaces.py
```

Already run for real as part of harness build (2026-08-08). Every registered
count in `gates.yaml g0_disjointness_screen.expected_drop_counts` reproduced
exactly: KUQ known 3071/unknown 2469, AmbigQA known 830/unknown 1002,
BIG-bench known 23/unknown 23, internal-panel top-up 501 unknown/415 known.
Re-run before the GPU stages launch only if any of the six frozen dataset
files or eight training-pool files could have changed since; if the script's
own "CHECK AGAINST expected_drop_counts" prints a mismatch, STOP per
`gates.yaml g0_disjointness_screen.on_count_mismatch` -- do not proceed.

Outputs: `screen_summary.json` (committed, counts/shas only) at the
experiment root; screened per-surface manifests + internal-panel pool under
gitignored `analysis/screen/`.

## Stage 1 -- add loaders + fixture tests (CPU, done)

`archive/experiment/phase1/eval/ood.py` now carries `load_ambigqa` and
`load_bigbench_known_unknowns`, registered in `OOD_LOADERS` as `"ambigqa"`
and `"bigbench_known_unknowns"` (additive only, deviation D2). Post-change
sha256: `cfd6cf8be6c0a892056b4b339dd2b8725dc9050c5cf991d8ec184f2b216d7760`.
Round-trip verified: both loaders read the real screened files and reproduce
the exact retained counts (see harness-build report).

## Stage 2 -- re-merge the surviving contrastive LoRA to 16-bit (GPU, ~15m)

Not yet run. Needs the surviving adapter
(`scratch/schema_response_confidence/runs/sft_schema_contrastive_seed1_full/20260627_203232/final_model`,
252.1 MB, confirmed present) merged to
`scratch/schema_response_confidence/runs/sft_schema_contrastive_seed1_full/20260627_203232/Qwen3-4B-bnb-4bit/merged-16bit`
(currently an empty directory). Check free disk space first
(`run_plan.disk.check_free_space_before: stage_2`, ~8 GB). Use the same
merge tooling the other seven arms' `merged-16bit` directories were produced
with (unsloth `save_pretrained_merged` or equivalent); this harness does not
prescribe a new merge script.

## Stage 3 -- SelfAware re-parity for A2 (GPU, ~30m) -- gate G1

Re-run the ORIGINAL SelfAware config for A2
(`archive/experiment/phase1/eval/config/eval_amendment_k_*` -- the config
that produced the committed
`experiments/contrastive-sft-behavior-conditional-confidence/analysis/phase1-migrated/eval/results_amendment_k_response_confidence_selfaware_contrastive_sft_seed1_merged_full_4b/contrastive_schema_sft_merged_seed1__selfaware/metrics.json`)
against the freshly re-merged base from stage 2, then:

```
python3 experiments/ood-breadth-beyond-selfaware/gate_score.py \
  --docker-digest <output of `docker inspect --format '{{.Id}}' <container>`> \
  --g1-rerun-metrics <path to the fresh run's metrics.json>
```

Read only the `G1` block of the output. PASS = all nine behavior metrics
within 0.10pp of committed AND n/n_known/n_unknown exact
(`gates.yaml g1_remerge_parity`). FAIL voids arms A2, A6, A7 -- the cell
reports on five arms; do not proceed to build A2/A6/A7 into the stage-5
launch if this fails.

## Stage 4 -- smoke: A1 on S_AMBIGQA, 64 rows (GPU, ~10m) -- gates G2, G3

This is the smoke the lead should run FIRST, before any full-arm launch. It
exercises the real pipeline (real vLLM generation, real docker image, real
scoring) at trivial cost.

1. Build a 64-row smoke slice of the screened AmbigQA surface (deterministic,
   first 64 rows by file order -- no new screening, just a head):

   ```
   head -n 64 experiments/ood-breadth-beyond-selfaware/analysis/screen/ambigqa_validation_screened.jsonl \
     > experiments/ood-breadth-beyond-selfaware/analysis/screen/ambigqa_smoke64.jsonl
   ```

2. Copy `archive/experiment/phase1/eval/config/eval_ood_breadth_clean_schema_sft_merged_seed1_local_4b.yaml`
   to a smoke config with `results_dir` renamed (e.g.
   `results_ood_breadth_smoke64_A1_ambigqa`) and `eval_sets` trimmed to just:

   ```yaml
   eval_sets:
     ambigqa:
       type: ood
       path: ../../../../experiments/ood-breadth-beyond-selfaware/analysis/screen/ambigqa_smoke64.jsonl
       label_from_target: false
   ```

3. Verify the docker digest BEFORE treating the stage as valid
   (`gates.yaml g_docker_digest`, `cell.yaml lane.digest_verification`):

   ```
   docker inspect --format '{{.Id}}' <container_name_or_id>
   # must equal sha256:f21629b9ae4ed11231768edfaed0f40d41d85d6ea9a71e8096a3d96ea0311772 char for char
   ```

4. Launch (per `cell.yaml lane.docker_verb`, `<stage>` = `smoke64`):

   ```
   docker run -d --name eh-ood-breadth-smoke64-$(date +%Y%m%dT%H%M%SZ) --gpus all --ipc=host \
     --entrypoint python3 -e HF_HOME=/workspace/repo/.cache/hf \
     -e HUGGINGFACE_HUB_CACHE=/workspace/repo/.cache/hf/hub \
     -v "/home/profsynapse/code/Epistemic-Humility-Research:/workspace/repo" \
     -w /workspace/repo \
     unsloth/unsloth@sha256:f21629b9ae4ed11231768edfaed0f40d41d85d6ea9a71e8096a3d96ea0311772 \
     archive/experiment/phase1/eval/run_eval.py --config <smoke config path> --live-vllm
   ```

5. Score G2 and G3 for the smoke:
   - G2: `retained_n_must_equal` does not apply to a 64-row slice (that's the
     FULL-surface threshold); instead confirm `label_from_target: false` held
     and `json_coverage_pct >= 99.0` on the 64 rows
     (`gate_score.py score_g2`'s coverage check generalizes to any n).
   - G3: `run_eval.py`'s in-harness assertions
     (`assert_no_think_scaffolding` / `assert_no_generated_thinking`) either
     raised (stage fails loudly) or the run completed; then run
     `gate_score.py`'s post-hoc `<think>` scan against the smoke
     `scored_rows.jsonl` as a second check.
   - Record actual wall-clock time to revise the `run_plan.estimate_status`
     note before stage 5 launches (cell.yaml `run_plan.estimate_status`).

STOP if the smoke fails G2/G3, or if generation throughput implies stage 5's
8-12 GPU-hour budget is badly wrong -- re-derive the budget, do not launch
stage 5 on a stale estimate.

## Stage 5 -- behavior panel, 8 arms x 3 surfaces (GPU, ~6.0-10.0h)

One `docker run` per arm config, in the order cell.yaml recommends (grouped
by base so adapter-only arms reuse a warm base): A1, A4, A5 (base = A1) --
then A8 (own base) -- then A3 (own base) -- then A2, A6, A7 (base = A2,
gated: only launch these three if stage 3's G1 passed). Each invocation is
`cell.yaml lane.docker_verb` with `--config archive/experiment/phase1/eval/config/eval_ood_breadth_<arm_name>_local_4b.yaml`.
Verify the docker digest before EACH stage per `g_docker_digest`. One GPU job
at a time (`lane.concurrency`).

## Stage 6 -- internal-panel extraction, A1 and A4 (GPU, ~20-40m)

Forward-only, no generation semantics beyond the harness's mechanical
1-token gate (see `extract_A1.yaml`/`extract_A4.yaml` header comments).

```
PYTHONPATH=experiments/common/renders python3 -m MechInterp.cli extract \
  --config experiments/ood-breadth-beyond-selfaware/extract_A1.yaml \
  --model <A1 base absolute path> \
  --i-know-this-runs-on-gpu

PYTHONPATH=experiments/common/renders python3 -m MechInterp.cli extract \
  --config experiments/ood-breadth-beyond-selfaware/extract_A4.yaml \
  --model <A1 base absolute path> --adapter <A4 GRPO-v2 adapter absolute path> \
  --i-know-this-runs-on-gpu
```

(Exact CLI entry point/flags per `synaptic-tuner/MechInterp/cli.py`; confirm
current flag names against that file at launch time since this harness build
did not modify the tuner submodule.) Confirm each run's manifest.json reports
`n_answered == n_rows == 2748` before proceeding -- a lower `n_answered`
means the `content_end` gate rejected rows, which should not happen given
`content_end` always returns `prompt_len` (see render module docstring).

## Stage 7 -- probe fit + calibration reports (CPU, ~45m) -- contributes to G7

```
python3 experiments/ood-breadth-beyond-selfaware/internal_panel_probe_gate.py \
  --arm A1 \
  --extraction-dir experiments/ood-breadth-beyond-selfaware/analysis/extraction/A1 \
  --scored-rows archive/experiment/phase1/eval/results_ood_breadth_clean_schema_sft_merged_seed1_full_4b/clean_schema_sft_merged_seed1__ambigqa/scored_rows.jsonl \
  --out experiments/ood-breadth-beyond-selfaware/analysis/gate/g7_A1.json

python3 experiments/ood-breadth-beyond-selfaware/internal_panel_probe_gate.py \
  --arm A4 \
  --extraction-dir experiments/ood-breadth-beyond-selfaware/analysis/extraction/A4 \
  --scored-rows archive/experiment/phase1/eval/results_ood_breadth_clean_schema_sft_grpo_v2_seed1_corrected_base_full_4b/clean_schema_sft_grpo_v2_seed1_corrected_base__ambigqa/scored_rows.jsonl \
  --out experiments/ood-breadth-beyond-selfaware/analysis/gate/g7_A4.json
```

Both output blocks must show `gate_pass: true` (both `heldout_probe_auroc >=
0.90` AND `margin >= 0.15`) for G7 to pass, per `gates.yaml
g7_internal_readout_transfer.requires: both_conditions_on_both_arms`.

Also run `archive/experiment/phase1/eval/analysis/calibration_gap_report.py
--scored <each arm's ambigqa scored_rows.jsonl>` per arm for the
stated-calibration reporting numbers (Analysis A only, per
`rendering_and_scoring.carried_over_unchanged.stated_calibration`).

## Stage 8 -- aggregate, bootstrap, adjudicate (CPU, ~2h) -- gates G4, G5, G6, G7

```
python3 experiments/ood-breadth-beyond-selfaware/gate_score.py \
  --docker-digest <last-used live digest, for the record> \
  --g1-rerun-metrics <stage-3 metrics.json path> \
  --out experiments/ood-breadth-beyond-selfaware/analysis/gate/gate_report.json
```

Read `integrity_all_pass` first. If false, the evidential block is
`NOT_READ` by construction (`gates.yaml` discipline: integrity gates read
first, all must pass before any evidential gate is read) -- fix the
integrity failure and re-run before treating any G4/G5/G6 number as
meaningful. G7 is read from stage 7's two output files, not recomputed here.

Adjudicate against `AMENDMENT.md`'s Prediction/Falsifier sections once every
gate has a real (non-`NOT_RUN`) status. This step is lead-only per the
project's delegation discipline (protocol interpretation and gate/falsifier
adjudication are never delegated).

## Pre-launch smoke already performed (this harness build, CPU-only)

- Stage 0 (G0 screen): run for real, all registered counts matched exactly.
- ood.py loaders: round-tripped against the real screened files, exact
  behavior-surface counts (7418/arm) reproduced.
- All 8 arm configs: dry-run through `run_eval._load_eval_records` for real
  (CPU), every config resolves gold + all three eval_sets and produces
  exactly 7418 fully-labeled rows.
- Internal-panel render_fn: smoke-tested against the real Qwen3 tokenizer on
  disk; produces the expected `<|im_start|>...` chat format with correct
  thinking-off scaffolding.
- `internal_panel_probe_gate.py` (G7) and `gate_score.py` (G1-G6): full
  pipeline exercised end-to-end against synthetic activations/metrics with
  the REAL 2748-row panel and REAL committed SelfAware reference numbers;
  correct PASS/FAIL behavior confirmed in both directions (a random-noise
  synthetic surface correctly FAILS G4; a within-tolerance synthetic re-run
  correctly PASSES G1). Synthetic fixtures deleted after the smoke; nothing
  from this section is committed or reported as a result.
