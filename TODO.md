# TODO / Current State

Last updated: 2026-06-12

## Operator Rules

- No cloud work unless explicitly approved.
- Do not restart WSL, Docker Desktop, or other host services without Joseph's explicit go-ahead.
- Prefer short local confidence loops before any long GPU run after Docker trouble.

## Current Experiment State

We are proving the Phase 1 local lane before committing more GPU time. The goal is to verify the actual local pipeline surfaces: probe data, WS-2 datasets, Docker/GPU training, artifact copy-out, run records, and later local evaluation.

### Completed

- WS-1 knowledge probe completed for `unsloth/Qwen3-4B-bnb-4bit`.
  - Output: `experiment/phase1/probe/qwen3-4b-instruct/probe_results.jsonl`
  - Rows: 20,000
  - Bad JSON: 0
  - Generated `<think>` contamination: 0
  - Duplicate row keys: 0
  - Labels: known 8,892 / unknown 7,103 / discard 4,005

- WS-2 datasets rebuilt and audited.
  - Output dir: `experiment/phase1/data/qwen3-4b-instruct/`
  - Non-discard rows: 15,995
  - Train/dev split is clean by `probe_pool_row_key`.
  - Important fix: TriviaQA `question_id` is not unique, so audits must use `*_question_keys`, not bare `*_question_ids`.
  - Public HF dataset repo: https://huggingface.co/datasets/professorsynapse/epistemic-humility-phase1
  - SFT smoke files published there: `qwen3-4b-instruct/sft_train.jsonl` and `qwen3-4b-instruct/sft_dev.jsonl`.

- Local SFT headline seed 1 completed.
  - Run id: `sft__4b__headline__seed1`
  - Adapter: `synaptic-tuner/toolset-training-artifacts/runs/local/4b/sft__4b__headline__seed1/20260611_202126/final_model`
  - Metrics: `.../logs/training_latest.jsonl`
  - Run record: `experiment/phase1/run_records/sft__4b__headline__seed1.json`

- Local DPO headline seed 1 completed.
  - Run id: `dpo__4b__headline__seed1`
  - Adapter: `synaptic-tuner/toolset-training-artifacts/runs/local/4b/dpo__4b__headline__seed1/20260611_211512/final_model`
  - Metrics: `.../logs/training_latest.jsonl`
  - Run record: `experiment/phase1/run_records/dpo__4b__headline__seed1.json`

- Fast local sanity loop passed after reboot.
  - Recipe: `experiment/phase1/run_records/materialized_recipes/sft__4b__micro_max2.yaml`
  - Artifact root: `synaptic-tuner/toolset-training-artifacts/runs/local/4b/sft__4b__micro_max2/20260612_084145`
  - Verified: Docker, GPU, model load, staged data load, LoRA, two optimizer steps, checkpoint, final adapter, logs, lineage, capacity file, and host copy-out.

## Known Issues / Gotchas

- KTO source logging bug is fixed locally, but KTO is still gated for cloud.
  - First full KTO attempt trained nearly to completion but failed after training because `train_kto.py` references `logging` without importing it.
  - A 20-step patched KTO debug run proved that adding `import logging` inside the copied container file allows the KTO trainer to complete and copy artifacts.
  - `synaptic-tuner/Trainers/kto/train_kto.py` now imports `logging` locally and was verified with `python -m pytest synaptic-tuner\tests\trainers\kto\test_train_kto_source.py -q` (5 passed).
  - HF Jobs/cloud KTO smoke remains blocked until the Synaptic Tuner fix is committed/pushed to the exact cloud commit and the cloud launcher/dataset prerequisites are cleared. The experiment-side local copy-mode workaround will not apply in HF Jobs.
  - The patched full KTO rerun progressed to at least step 1,650 / 3,599, then `docker exec` returned Windows code `3221225786`; Docker Desktop then returned HTTP 500 for `docker ps/info/inspect`.
  - Run record: `experiment/phase1/run_records/kto__4b__headline__seed1.json`
  - Current status: `failed_docker_exec_3221225786`

- Cloud lane should use Synaptic Tuner workflows, not ad hoc launch scripts.
  - Publish Phase 1 datasets with the Synaptic Tuner dataset-publishing skill/script before launching cloud cells.
  - Prefer `python tuner.py cloud-pipeline ...` for HF Jobs.
  - Require a clean pushed exact commit, the HF dataset repo/file, `HF_TOKEN`, and exact approval before any cost-incurring launch.
  - `tuner.py` loads `.env` from the Synaptic Tuner repo root, but `HF_TOKEN` currently lives in the parent research repo `.env`; use process-local env injection or a Synaptic Tuner `.env` without printing/copying secrets.
  - Current launcher env blocker: the `kto` conda env has `huggingface_hub 0.36.0` with Jobs API support, but lacks Buckets `create_bucket`; keep bucket-support upgrades isolated from the main Unsloth/training runtime.

- Docker copy-mode logs can be misleading.
  - The container PID 1 may be `sleep infinity`; the trainer runs through `docker exec`.
  - `docker logs` and host redirected logs can stay blank while training is healthy.
  - For long copy-mode runs, inspect in-container `training_latest.jsonl` only if Docker is healthy and the container is retained.

- `Start-Process` may fail in Codex Desktop PowerShell due duplicate `Path` / `PATH`.
  - Reliable detached launcher is a `py -3.11 -c` wrapper around `subprocess.Popen`.

## Next Steps

1. Do not rerun KTO immediately.
2. Commit/push the local Synaptic Tuner KTO logging fix to the exact cloud commit, then clear cloud launcher and dataset prerequisites before any KTO HF smoke.
3. Before any long local run, run:

   ```powershell
   docker info --format "{{.ServerVersion}}"
   docker ps -a --format "{{.Names}} {{.Status}}"
   nvidia-smi --query-gpu=timestamp,name,utilization.gpu,memory.used,memory.total --format=csv,noheader
   ```

4. If Docker is healthy, use the SFT max-2 micro recipe as the first confidence check:

   ```powershell
   py -3.11 tuner.py local-run --job-config F:\Code\Epistemic-Humility-Research\experiment\phase1\run_records\materialized_recipes\sft__4b__micro_max2.yaml --yes
   ```

   Run from `F:\Code\Epistemic-Humility-Research\synaptic-tuner`.

5. Next scientific pipeline step is local evaluation against the completed SFT and DPO adapters, if the repo already has the evaluation runner wired locally.
6. If local eval is not wired yet, document that gap and implement the smallest local-only eval path before expanding the 4B matrix.
7. Only after local eval works should we consider more headline cells. KTO HF smoke remains blocked until the fixed Synaptic Tuner commit is pushed and cloud prerequisites are cleared.
8. Before cloud-lane expansion beyond the SFT smoke, publish the remaining required Phase 1 dataset files to HF, record the dataset repo/file names, verify process-local `HF_TOKEN` availability, and use Synaptic Tuner's `cloud-pipeline` flow from a clean pushed exact commit.

## Files Changed During This Session

- `experiment/phase1/probe/*`: Qwen3 probe hardening and deterministic 20k subset.
- `experiment/phase1/data/build_datasets.py`: row-key identity fix for duplicate TriviaQA IDs.
- `experiment/phase1/data/tests/test_build_datasets.py`: regression coverage for row-key split behavior.
- `.agents/skills/experiment-runner/scripts/run_matrix.py`: local path/materialized output fixes.
- `.agents/skills/experiment-runner/scripts/prepare_local_cell.py`: single-cell local preparation helper plus KTO copy-mode workaround.
- `.agents/skills/experiment-runner/SKILL.md`: local Docker, data, KTO, and micro-loop gotchas.
- `experiment/phase1/run_records/*`: local SFT/DPO/KTO run records and materialized recipes.
