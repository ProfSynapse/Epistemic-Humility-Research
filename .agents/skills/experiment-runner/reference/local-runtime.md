# Local Runtime

Read for Windows/Docker/GPU/local-trainer execution problems and monitor behavior.

- Native Windows vLLM can import `vllm` while still failing at runtime with
  `ModuleNotFoundError: vllm._C`; use Docker/WSL Linux vLLM for real WS-1 probe
  runs.

- The `vllm/vllm-openai` image has a server entrypoint. Override it for checks
  and probe execution, e.g. `--entrypoint nvidia-smi` for GPU smoke and
  `--entrypoint python3` for `probe.py`.

- Docker may require an unsandboxed/escalated command from Codex. On the desktop
  run, Docker engine `29.3.1` was reachable outside the sandbox.

- After Joseph moved/opened Docker on the F drive, Codex Docker CLI behavior is
  mixed: bare `docker ps` and `docker ps -a --format ...` worked, while
  `docker info`, `docker context ls`, explicit `DOCKER_CONFIG`, explicit pipe
  commands, and some image listing paths can hit
  `C:\Users\Joseph\.docker\config.json Access is denied` or Docker pipe
  permission errors. Do not modify `C:\Users\Joseph\.docker` from Codex as a
  workaround. For actual local container create/pull/run operations, escalated
  Docker commands worked.

- Local copy-mode can leave the Docker container alive with PID 1 as
  `sleep infinity` after training is complete, while host stdout/stderr and
  host artifact directories are stale or missing. Do not treat an old host PID,
  frozen dashboard step, or running sleep container as the completion source of
  truth. Verify local completion from the run record plus host-visible
  `final_model` and metrics/lineage `train_end`; if host artifacts are absent,
  inspect the in-container path
  `/workspace/repo/toolset-training-artifacts/runs/local/<size>/<run_id>/<timestamp>/`
  for `final_model`, `training_lineage.json`, and `logs/training_*.jsonl`.
  On Windows, `docker cp` can fail when it tries to create the container symlink
  `logs/training_latest.jsonl` (`A required privilege is not held by the
  client`) after copying most real files. Recover any missed provenance files
  individually and materialize `training_latest.jsonl` as a normal copy of the
  concrete timestamped metrics log; keep the large recovered artifact tree
  gitignored.

- Local Docker/GPU recovery on 2026-06-13: `docker pull unsloth/unsloth:latest`
  succeeded locally with digest
  `sha256:f21629b9ae4ed11231768edfaed0f40d41d85d6ea9a71e8096a3d96ea0311772`,
  and `docker run --rm --gpus all --entrypoint nvidia-smi
  unsloth/unsloth:latest` saw the RTX 3090.

- Redirect Hugging Face caches to repo-local `.cache/hf` during local runs to
  avoid Windows permission failures under `C:\Users\Joseph\.cache\huggingface`.

- `.env` may contain `HF_TOKEN` while the current process environment does not.
  Load it process-locally or pass `--env-file .env`; never print token values.
  For local eval containers that only use public/local assets, do not pass the
  full repo `.env`; pass only narrow cache/env variables such as `HF_HOME` and
  `HUGGINGFACE_HUB_CACHE`. The grouped-SFT broader OOD eval completed this way
  after the full `.env` launch was correctly rejected as unnecessary secret
  exposure.

- In the Codex Desktop PowerShell environment, `Start-Process` can fail before
  launch with `Item has already been added. Key in dictionary: 'Path' Key being
  added: 'PATH'`, and `cmd /c start /b` may not leave a durable child under the
  tool timeout. The reliable detached launcher is a foreground `py -3.11 -c`
  wrapper that opens stdout/stderr files and calls `subprocess.Popen(...,
  cwd='synaptic-tuner', stdin=DEVNULL, creationflags=DETACHED_PROCESS |
  CREATE_NEW_PROCESS_GROUP, close_fds=True)`. If that launcher path is skipped
  or blocked, do not keep retrying fragile PowerShell job mechanisms. For an
  already materialized and audited local recipe, it is acceptable to launch the
  equivalent `docker run -d` directly, but record the bypass in the run record,
  keep the materialized recipe as the provenance source of truth, and verify
  parity for model path, staged data path, LoRA budget, seed, output root,
  timestamp, image, workdir, and trainer flags before treating the run as clean.

- In local copy-mode, the Docker container PID 1 may be `sleep infinity` while
  the tuner starts the trainer with `docker exec`. In that case `docker logs`
  and the host redirected stdout/stderr can remain blank during training, and
  artifacts may not appear on the host until copy-out at completion. Inspect
  progress with `docker top` and `docker exec <container> sh -lc "tail .../logs/
  training_*.jsonl"` inside `/workspace/repo/toolset-training-artifacts/...`.

- Historical KTO note: the earlier pinned tuner source completed training and
  saved artifacts, then crashed during best-effort registry logging with
  `NameError: name 'logging' is not defined`. The source now imports `logging`
  locally and passed
  `python -m pytest synaptic-tuner\tests\trainers\kto\test_train_kto_source.py -q`
  (5 passed). Keep the KTO-only local copy-mode workaround in
  `prepare_local_cell.py` as temporary compatibility for unfixed copies only;
  remove it after the fixed Synaptic Tuner source is the committed baseline.

- A timed-out host monitor can leave Docker Desktop's Linux engine unhealthy
  after an interrupted `docker exec`; observed wrapper exit
  `3221225786`, no active GPU process, retained container inaccessible, and both
  `desktop-linux` and `default` contexts returning HTTP 500 for `docker ps/info`.
  Clearing hung `docker.exe` clients and restarting Docker Desktop/WSL from the
  shell did not recover it in-session. Treat this as a Docker Desktop backend
  recovery blocker before launching another long local cell; first verify
  `docker info` and `docker ps` return normally.

- Current local recovery status supersedes the failed-backend state for short
  SFT confidence checks: the existing SFT max-2 micro recipe completed on
  2026-06-13 from `synaptic-tuner` with
  `py -3.11 tuner.py local-run --job-config F:\Code\Epistemic-Humility-Research\experiment\phase1\run_records\materialized_recipes\sft__4b__micro_max2.yaml --yes`.
  Artifact root:
  `synaptic-tuner/toolset-training-artifacts/runs/local/4b/sft__4b__micro_max2/20260613_084227`.
  It loaded `unsloth/Qwen3-4B-bnb-4bit`, trained on 14,395 SFT examples for
  exactly 2 steps, and saved `checkpoints/checkpoint-2`, `final_model`,
  `training_lineage.json`, and `capacity_features.json`. Audit:
  `logs/training_latest.jsonl` ended with `train_end`, `step: 2`,
  `oom_risk_level: low`, peak reserved VRAM about 4.383 GB, and no containers
  remained after completion. No eval/generation ran. Non-blocking warning:
  `Failed to import Triton kernels... No module named 'triton_kernels.routing'`;
  it did not block this completed micro run.

- Local schema-SFT batch probing on 2026-06-22: Qwen3-4B LoRA r=32,
  completion-only, BF16, batch 16 completed a 512-row response-confidence smoke
  in about 70 seconds, but the saved capacity profile marked `oom_risk_level:
  critical` and reported impossible reserved-memory percentages at shutdown.
  Treat that as a capacity red flag, not as clearance for full runs. The first
  full schema-SFT was launched at batch 12 as the speed/safety compromise, but
  live telemetry still reached about 23.7/24 GB VRAM and reported critical risk
  by step 125. Do not run parallel GPU work beside this cell; if it OOMs or must
  be repeated, prefer batch 8 before trying to recover throughput elsewhere.

- The Unsloth image default entrypoint may chmod the mounted repo and fail on
  `.tmp/pytest-codex*`. For local eval wrapper runs, override the entrypoint
  with `--entrypoint python3`.

- Current Synaptic Tuner SFT custom `--config` handling treats non-default
  config paths as Python modules. A YAML path can fail with a null loader before
  training starts. For one-off local SFT bridge runs, prefer a small Python shim
  config or a checked wrapper until the trainer supports custom YAML config
  loading. Passing nested JSON such as `--chat-template-kwargs` through
  PowerShell -> Docker -> Python is also fragile; avoid CLI JSON quoting for
  reproducible local runs when the same value can live in the Python config.

- For Codex-side long-run monitors on this Windows host, prefer direct Docker
  commands over piped/combined Docker calls. During 2026-06-16 eval monitoring,
  direct `docker ps -a --filter ...` and `docker logs --tail ...` worked, while
  the same checks embedded after `Start-Sleep` or inside PowerShell pipelines
  intermittently hit `C:\Users\Joseph\.docker\config.json Access is denied` or
  Docker pipe permission errors. Treat those combined-command failures as
  monitor artifacts if result files and GPU telemetry show healthy progress.

- One live vLLM eval container can run beside local KTO training on the RTX 3090
  if the eval is scoped to one arm, uses container-visible paths, overrides the
  image entrypoint with `--entrypoint python3`, and caps vLLM with
  `gpu_memory_utilization: 0.40` plus `max_lora_rank: 32`. On 2026-06-16,
  sequential DPO seed 2 and seed 3 full SelfAware evals each exited 0 while
  `sft_kto__4b__amendment_a__seed2` kept training; total card VRAM peaked near
  16.4 GB, and KTO's own reserved VRAM stayed about 4.389 GB with low OOM risk.
  Do not launch two vLLM engines plus training unless intentionally testing
  capacity. Run seed evals sequentially beside training.

- On the local RTX 3090, one conservative vLLM eval engine
  (`gpu_memory_utilization: 0.40`) can run beside KTO training, but the combined
  card usage can still climb near 17 GB once vLLM is generating. Do not launch a
  second vLLM eval engine while KTO is active unless intentionally testing local
  capacity. Queue seed/config evals sequentially beside the trainer.

- `git submodule status` can fail if Git Unix helpers such as `basename` or
  `sed` are missing. Verify the submodule SHA with the gitlink plus
  `git -C synaptic-tuner rev-parse HEAD`.
