# TODO / Current State

Last updated: 2026-06-13

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

- Local Docker/GPU recovery passed after Docker was moved/opened on the F drive.
  - Local image pull: `docker pull unsloth/unsloth:latest` succeeded with digest `sha256:f21629b9ae4ed11231768edfaed0f40d41d85d6ea9a71e8096a3d96ea0311772`.
  - Container GPU probe passed: `docker run --rm --gpus all --entrypoint nvidia-smi unsloth/unsloth:latest` saw the RTX 3090.
  - Local SFT max-2 micro command completed from `synaptic-tuner`:
    `py -3.11 tuner.py local-run --job-config F:\Code\Epistemic-Humility-Research\experiment\phase1\run_records\materialized_recipes\sft__4b__micro_max2.yaml --yes`.
  - Artifact root: `synaptic-tuner/toolset-training-artifacts/runs/local/4b/sft__4b__micro_max2/20260613_084227`.
  - It loaded `unsloth/Qwen3-4B-bnb-4bit`, trained on 14,395 SFT examples for exactly 2 steps, and saved `checkpoints/checkpoint-2`, `final_model`, `training_lineage.json`, and `capacity_features.json`.
  - Audit: `logs/training_latest.jsonl` ended with `train_end`, `step: 2`, `oom_risk_level: low`, and peak reserved VRAM about 4.383 GB; no containers remained after completion. No eval/generation ran.
  - Non-blocking warning observed: `Failed to import Triton kernels... No module named 'triton_kernels.routing'`; this did not block the completed micro run.

- Local eval harness is now wired for opt-in real vLLM generation.
  - Default fixture path remains unchanged.
  - Live path: `python experiment/phase1/eval/run_eval.py --config <scoped-config.yaml> --live-vllm`.
  - Local base/SFT/DPO smoke config: `experiment/phase1/eval/config/eval_smoke_local_4b.yaml`.
  - `VLLMGenerator` lazy-loads vLLM, supports one base model plus LoRA arms, rejects generated `<think>` tags, and requires explicit `model_name` so `model_tag` stays a reporting label.
  - Windows UTF-8 read/write fixes landed for eval gold/OOD/config/results paths.
  - Verified: `python -m pytest experiment\phase1\eval\tests -q` (58 passed, 1 intentional McNemar warning).

- Scoped local live eval smoke passed in Docker/Linux for tiny base/SFT/DPO.
  - Initial live smoke reached the base arm but failed when loading the SFT adapter with `ValueError: LoRA rank 32 is greater than max_lora_rank 16`.
  - Config fix: `vllm.max_lora_rank: 32` added to `experiment/phase1/eval/config/eval_smoke_local_4b.yaml`.
  - Focused test after the config fix: `python -m pytest experiment/phase1/eval/tests/test_run_eval_e2e.py -q` -> `13 passed, 1 warning`.
  - Rerun passed base + SFT + DPO, exit code 0, with `eval complete: 3 arm x set rows, config_sha=97dddaaf30d0dfb0`.
  - Outputs: `experiment/phase1/eval/results_smoke_local_4b`, including per-arm `metrics.json` / `bootstrap_ci.json` and comparisons `summary_table.csv` / `mcnemar.csv`.
  - Smoke-only summary table over `n=5` fixture rows: base truthful 60.0, SFT 100.0, DPO 40.0. These are not headline results.
  - `<think>` guard did not trigger: `rg "<think>|</think>" experiment\phase1\eval\results_smoke_local_4b` found no matches.
  - No containers or GPU processes remained after completion.
  - Local eval path is now validated for tiny base/SFT/DPO adapter load, generation, scoring, bootstrap, and comparisons.

- Corrected local OOD diagnostic passed for bounded base/SFT/DPO x CoCoNot/TruthfulQA/SelfAware slices.
  - Run id: `eh-ood-slice-local-4b-4`.
  - Exit code 0 with `eval complete: 9 arm x set rows, config_sha=fe48ee93abfbc559`.
  - Outputs: `experiment/phase1/eval/results_ood_slice_local_4b`.
  - Coverage: base/SFT/DPO x CoCoNot/TruthfulQA/SelfAware, limit 64 each.
  - `rg "<think>|</think>" experiment\phase1\eval\results_ood_slice_local_4b` found no matches.
  - Caveat: these first slices were all known-labeled (`n_unknown_labeled=0`), so unknown/refusal-recall metrics are not meaningful there. This validates known-OOD scoring/over-refusal and the live pipeline, not headline results.

- Mixed SelfAware local diagnostic passed.
  - Run id: `eh-selfaware-mixed-local-4b`.
  - Exit code 0 with `eval complete: 3 arm x set rows, config_sha=3f5f676bde46dce9`.
  - Outputs: `experiment/phase1/eval/results_selfaware_mixed_slice_local_4b`.
  - `rg "<think>|</think>" experiment\phase1\eval\results_selfaware_mixed_slice_local_4b` found no matches.
  - Diagnostic-only summary over n=64: base unknown=27 / known=37, refusal_recall 0.0, answer_on_unknown 100.0, over_refusal 0.0, truthful 15.62; SFT refusal_recall 88.89, answer_on_unknown 11.11, over_refusal 72.97, truthful 48.44; DPO refusal_recall 0.0, answer_on_unknown 100.0, over_refusal 0.0, truthful 14.06.

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
    - Prior bounded SFT max-2 `cloud-pipeline` smoke on Synaptic Tuner `ee4938d` reached eval `runtime_ready` healthy, then failed as job `6a2c58ac7c68f455eff141df` with `ERROR exit 143` after visible logs stopped during slow Qwen3 base `model.safetensors` download around 25%. Bucket stage artifacts contained only `logs/stage_summary.json` and `logs/stage_events.jsonl`; no hidden app traceback or result files were present.
    - Latest bounded SFT max-2 `cloud-pipeline` smoke launched from Synaptic Tuner `0400540` with command shape: `cloud-pipeline --method sft --yes --train-model-name Qwen/Qwen3-4B --train-dataset-name professorsynapse/epistemic-humility-phase1 --train-dataset-file qwen3-4b-instruct/sft_train.jsonl --train-max-steps 2 --train-image-profile stable --eval-image-profile stable_unsloth --scenario labkit_epistemic_humility_smoke.yaml --eval-timeout-hours 4`.
    - Remote training job `6a2c75e97c68f455eff143b2`, created `2026-06-12 21:11:05 UTC`, ended `ERROR`. It cloned and checked out `0400540`, loaded the Unsloth stable image, began loading `Qwen/Qwen3-4B`, then stalled/failed during download of the first shard `model-00001-of-00002.safetensors` around `28.2M/4.97G`; it did not reach max-2 training or eval. Treat this as a remote base-model download/training-bootstrap failure, not a data or eval-code failure.
    - Earlier local launch attempts failed before submission because the default launcher env has Hub `0.36.0` without the Buckets API, while an overlay with Hub `1.19.0` conflicts with installed Transformers if the tuner stack imports both in-process.
    - Host/local logging gotcha: successful submission log `hf_cloud_pipeline_sft_smoke_20260612_171048.log` did not advance past `STEP 1: CLOUD TRAINING`, did not include the remote job id, and was garbled/UTF-16-ish. The remote HF Jobs list was needed to identify the submitted job. Future launcher work should avoid importing Transformers with Hub 1.x, capture/print the job id before polling, and use UTF-8-safe log capture.
    - `unsloth/unsloth:latest`: `numpy was upgraded mid-session (loaded: 2.2.6, installed: 2.4.1)`.
    - `unsloth/unsloth:2026.2.1-pt2.9.0-cu12.8-fixed-numba-numpy-error`: `ModuleNotFoundError: numpy._core.tests` through SciPy/Transformers during `import unsloth`.
    - Synaptic Tuner fixes already merged through submodule `0400540`: quote HF Jobs pip requirements, avoid upgrading generic project deps in the active trainer runtime, isolate bucket-sync `hf_xet`, avoid eval overlay ML-stack upgrades, split eval runtime vs bucket-sync overlays, forward cloud-pipeline eval args, add `--eval-timeout-hours` / eval timeout resolution, and log model-load plus SIGTERM/SIGINT terminated stage events including bootstrap downloads.
    - Next cloud action should avoid immediately repeating the same A10G Qwen3 4B download loop. Run a smaller cloud-pipeline smoke, for example a tiny public model, or improve launcher job-id capture, UTF-8 logging, and model-cache strategy before another Qwen3 4B attempt.

- Docker copy-mode logs can be misleading.
  - The container PID 1 may be `sleep infinity`; the trainer runs through `docker exec`.
  - `docker logs` and host redirected logs can stay blank while training is healthy.
  - For long copy-mode runs, inspect in-container `training_latest.jsonl` only if Docker is healthy and the container is retained.

- Docker CLI behavior from Codex is mixed after the F-drive Docker move/open.
  - Bare `docker ps` and `docker ps -a --format ...` worked, while `docker info`, `docker context ls`, explicit `DOCKER_CONFIG`, explicit pipe commands, and some image listing paths can hit `C:\Users\Joseph\.docker\config.json Access is denied` or Docker pipe permission errors.
  - For actual local container create/pull/run operations, escalated Docker commands worked. Do not modify `C:\Users\Joseph\.docker` as a workaround from Codex.
  - Unsloth image default entrypoint may chmod the mounted repo and fail on `.tmp/pytest-codex*`; for local eval wrapper runs use `--entrypoint python3`.

- Local eval scoring/generation gotchas fixed.
  - OOD records carry their own `aliases`; scoring now prefers normalized non-empty record aliases and falls back to global Cheng gold. Without this, OOD known correctness/truthful vectors could be wrongly zero when questions are absent from Cheng gold.
  - Qwen3 prompt rendering with thinking disabled is insufficient; vLLM `SamplingParams` now receives stop strings `<think>` and `</think>` when `generation.enable_thinking: false`, preserving any configured `generation.stop` values. The generated-thinking guard remains a backstop; do not strip contaminated outputs.
  - Non-blocking warnings seen during local diagnostics: Triton routing module warning, AOT cache save/HF cache metadata permission warnings, and NCCL `destroy_process_group` shutdown warning.

- `Start-Process` may fail in Codex Desktop PowerShell due duplicate `Path` / `PATH`.
  - Reliable detached launcher is a `py -3.11 -c` wrapper around `subprocess.Popen`.

## Next Steps

1. Do not rerun KTO immediately.
2. Commit/push the local Synaptic Tuner KTO logging fix to the exact cloud commit, then clear cloud launcher and dataset prerequisites before any KTO HF smoke.
3. Before any long local run, prefer the bare Docker/host GPU checks that are known to work from Codex:

   ```powershell
   docker ps -a --format "{{.Names}} {{.Status}}"
   nvidia-smi --query-gpu=timestamp,name,utilization.gpu,memory.used,memory.total --format=csv,noheader
   ```

   Avoid treating `docker info` / `docker context ls` failures as definitive engine failures in this environment; they can be Docker config/API permission artifacts.

4. If Docker is healthy, use the SFT max-2 micro recipe as the first confidence check:

   ```powershell
   py -3.11 tuner.py local-run --job-config F:\Code\Epistemic-Humility-Research\experiment\phase1\run_records\materialized_recipes\sft__4b__micro_max2.yaml --yes
   ```

   Run from `F:\Code\Epistemic-Humility-Research\synaptic-tuner`.

5. Stage/commit the generic eval fixes/configs, then decide whether to run a larger bounded real eval slice against the intended held-out/OOD subset before expanding to more training cells.
6. Do not run KTO, the headline/full eval, or any long cell without explicit approval.
7. Do not immediately repeat the same A10G Qwen3 4B HF Jobs download loop. The latest `0400540` bounded SFT max-2 `cloud-pipeline` smoke submitted job `6a2c75e97c68f455eff143b2` and failed during remote `Qwen/Qwen3-4B` first-shard download before training/eval. Next, run a smaller cloud-pipeline smoke, for example a tiny public model, or improve launcher job-id capture, UTF-8 logging, and model-cache strategy before another Qwen3 4B attempt.
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
