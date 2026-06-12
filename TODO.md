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
  - Qwen3 4B Phase 1 train/dev JSONLs are public there: `sft_train.jsonl`, `sft_dev.jsonl`, `dpo_train.jsonl`, `dpo_dev.jsonl`, `kto_congruence_train.jsonl`, `kto_congruence_dev.jsonl`, `kto_correctness_safe_train.jsonl`, and `kto_correctness_safe_dev.jsonl`.

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

- Local eval harness is now wired for opt-in real vLLM generation.
  - Default fixture path remains unchanged.
  - Live path: `python experiment/phase1/eval/run_eval.py --config <scoped-config.yaml> --live-vllm`.
  - Local base/SFT/DPO smoke config: `experiment/phase1/eval/config/eval_smoke_local_4b.yaml`.
  - `VLLMGenerator` lazy-loads vLLM, supports one base model plus LoRA arms, rejects generated `<think>` tags, and requires explicit `model_name` so `model_tag` stays a reporting label.
  - Windows UTF-8 read/write fixes landed for eval gold/OOD/config/results paths.
  - Verified: `python -m pytest experiment\phase1\eval\tests -q` (58 passed, 1 intentional McNemar warning).

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
  - Use the isolated launcher venv `C:\tmp\hfjobs-launcher312` or equivalent; set `PYTHONIOENCODING=utf-8` and `PYTHONUTF8=1` so Rich output cannot crash on Windows.
  - Tiny SFT HF Jobs smoke reached remote submission, exact public checkout, public HF dataset access, bucket creation, model load, tokenization, two training steps, and final artifact sync on the pinned stable image:
    `unsloth/unsloth:2026.1.2-pt2.9.0-cu12.8-update@sha256:5266c57be21059bfb407d80dc2f448868a5c2e2dbe7b2aa27780f48b48cbec39`.
    - Import probe passed: job `6a2c379d7c68f455eff13e99`.
    - Training + bucket sync passed after Synaptic Tuner PRs #104/#105: jobs `6a2c40c27c68f455eff13f95` and `6a2c4658871c005b5352b6fd`.
    - Latest bounded SFT max-2 `cloud-pipeline` smoke on Synaptic Tuner `ee4938d` reached eval `runtime_ready` healthy, then failed as job `6a2c58ac7c68f455eff141df` with `ERROR exit 143` after visible logs stopped during slow Qwen3 base `model.safetensors` download around 25%. Bucket stage artifacts contained only `logs/stage_summary.json` and `logs/stage_events.jsonl`; no hidden app traceback or result files were present. Treat this as runtime allowance/download-load pressure, not an eval-code failure.
    - `unsloth/unsloth:latest`: `numpy was upgraded mid-session (loaded: 2.2.6, installed: 2.4.1)`.
    - `unsloth/unsloth:2026.2.1-pt2.9.0-cu12.8-fixed-numba-numpy-error`: `ModuleNotFoundError: numpy._core.tests` through SciPy/Transformers during `import unsloth`.
    - Synaptic Tuner fixes already merged through submodule `0400540`: quote HF Jobs pip requirements, avoid upgrading generic project deps in the active trainer runtime, isolate bucket-sync `hf_xet`, avoid eval overlay ML-stack upgrades, split eval runtime vs bucket-sync overlays, forward cloud-pipeline eval args, add `--eval-timeout-hours` / eval timeout resolution, and log model-load plus SIGTERM/SIGINT terminated stage events including bootstrap downloads.
    - Next cloud action is another bounded SFT max-2 cloud-pipeline smoke from Synaptic Tuner `0400540` or later; keep the same dataset, model, LoRA, and Qwen settings, keep training tiny, and pass a separate longer eval budget with `--eval-timeout-hours`.

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

5. With explicit GPU approval, run the smallest local `--live-vllm` eval smoke:
   `python experiment/phase1/eval/run_eval.py --config experiment/phase1/eval/config/eval_smoke_local_4b.yaml --live-vllm`.
   Do not run the full headline eval yet.
6. If that local eval smoke passes, materialize the next same-model real eval config against the intended held-out/OOD subset before expanding to more training cells.
7. Rerun the bounded SFT max-2 HF Jobs cloud-pipeline smoke from Synaptic Tuner `0400540` or later, keeping the same dataset/model/LoRA/Qwen settings and tiny training max-2, and pass a separate longer eval budget with `--eval-timeout-hours`; the prior `ee4938d` smoke reached eval `runtime_ready` and then failed with exit 143 during/after slow Qwen3 base download/load, with no app traceback in stage artifacts.
8. Only after local eval and cloud smoke both work should we consider more headline cells. KTO remains blocked for local expansion until Docker reliability is re-established and for cloud expansion until an explicit KTO smoke is approved with the cloud prerequisites cleared.
9. Before cloud-lane expansion beyond the SFT smoke, verify process-local `HF_TOKEN` availability, use Synaptic Tuner's `cloud-pipeline` flow from a clean pushed exact commit, and confirm the already public Qwen3 4B dataset file names.

## Files Changed During This Session

- `experiment/phase1/probe/*`: Qwen3 probe hardening and deterministic 20k subset.
- `experiment/phase1/data/build_datasets.py`: row-key identity fix for duplicate TriviaQA IDs.
- `experiment/phase1/data/tests/test_build_datasets.py`: regression coverage for row-key split behavior.
- `.agents/skills/experiment-runner/scripts/run_matrix.py`: local path/materialized output fixes.
- `.agents/skills/experiment-runner/scripts/prepare_local_cell.py`: single-cell local preparation helper plus KTO copy-mode workaround.
- `.agents/skills/experiment-runner/SKILL.md`: local Docker, data, KTO, and micro-loop gotchas.
- `experiment/phase1/run_records/*`: local SFT/DPO/KTO run records and materialized recipes.
- `experiment/phase1/eval/*`: opt-in live vLLM generation path plus UTF-8 eval loader fixes.
- `synaptic-tuner`: submodule advanced through generic HF Jobs cloud/eval dependency-isolation fixes.
