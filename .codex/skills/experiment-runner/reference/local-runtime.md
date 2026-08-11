# Local Runtime

Read for Windows/Docker/GPU/local-trainer execution problems and monitor behavior.

**Scope note:** this file is the `tuner.py local-run` training-job lane,
launched from Windows Python (`py.exe`) against Docker Desktop over an
npipe. It is a different Docker path from the local `mechinterp` GPU-verb
lane (`extract`/`steer`/`dose-calibrate` run directly from WSL2 against the
native `default` Docker context / unix socket). The binding container
invariant for that lane lives in the `mechinterp-cells` skill's "Local GPU
runs execute in a pinned container" section, not here.

## Proven local-run launch command (the one-liner)

A local training cell is launched with a single tuner CLI verb. The proven,
reproducible invocation (works from WSL or Windows on this dual-boot host):

```bash
# From the synaptic-tuner directory. Use the WINDOWS Python launcher (py.exe),
# NOT WSL python3, and pass a Windows F:\ path to the materialized recipe.
py.exe -3.11 tuner.py local-run --job-config 'F:\Code\Epistemic-Humility-Research\archive\experiment\phase1\run_records\materialized_recipes\<recipe>.yaml' --yes
```

Why `py.exe -3.11` and not `python3`: the tuner shells out to a bare `docker`
binary. On this host the WSL-native `/usr/bin/docker` is a broken apt build
(`docker.io` 29.1.3) that SEGFAULTS, and the active context is Docker Desktop
over a Windows npipe (`desktop-linux`) that the Linux client cannot drive
anyway. The Windows Python launcher runs the tuner as a Windows process, so its
`docker` resolves to Docker Desktop's working CLI. Running `python3 tuner.py`
from WSL fails at `docker pull` with `Failed to initialize: protocol not
available`. (You CAN drive this entirely from a WSL shell — `py.exe` is on PATH
from WSL — it is not a hand-off to the user.) If you ever need a raw Docker
command from WSL, use `docker.exe` (it accepts `/mnt/f` bind paths); never bare
`docker`.

Staging: `setup.copy` paths in the materialized recipe resolve relative to the
`synaptic-tuner/` directory (the tuner cwd), NOT the research repo root. The
sibling copy entries (`Trainers/sft`, `shared`, `tuner`) live under the tuner,
so any data file (e.g. a `scratch/.../foo.jsonl`) must be staged INTO
`synaptic-tuner/scratch/...` before launch — copying from the research-root
`scratch/` is required and safe (tuner `scratch/` is gitignored; this is the
allowed ephemeral staging write). Verify the staged file's sha256 matches the
run record before launching. Symptom if skipped: `Error: Configured copy path
does not exist: scratch\...`.

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

- Teammate watch discipline for long containers (added after four silent
  stalls across three executor agents, 2026-07-31 to 2026-08-03; stalls of
  1.5h/8h/10h/1h idle GPU): a spawned teammate agent is NOT reliably
  re-invoked when its own background `docker wait` completes — the wake was
  observed to drop both when the completion landed mid-turn (notification
  swallowed, not queued) and when the agent was properly idle. Lead-session
  background-task notifications ARE reliable. This is harness plumbing, not
  agent discipline; swapping executors does not fix it. Binding architecture
  for any teammate-driven container chain:
  1. SHORT operations (merges, bounded smokes, anything under ~10 min) run
     FOREGROUND inside the teammate's turn with an explicit timeout —
     foreground work cannot stall (zero stalls since adopting this).
  2. LONG containers: teammate reports the exact container name via
     SendMessage IMMEDIATELY at launch; the LEAD holds a bare background
     `docker wait <name>` as the PRIMARY wake. The teammate's own watch is
     best-effort redundancy only.
  3. When the lead watch fires: verify artifacts on disk, then IMMEDIATELY
     SendMessage the teammate the verified numbers plus an explicit proceed
     order — never wait for the teammate's own report. If the idle-guard
     blocks the send, the teammate is genuinely mid-turn and will handle it;
     resend at its next idle notification.
  4. The teammate must `docker inspect` every launched-but-unclosed container
     at the START of every turn, regardless of any wake, and act on exited
     ones in the same turn instead of idling.

- Storage hygiene (added after the 2026-08-02 disk-full crash truncated a
  merge shard mid-write): run `scripts/ops/prune_runtime.sh stage` at every
  stage boundary (prunes stopped containers and dangling images only) and
  `scripts/ops/prune_runtime.sh scan` monthly or below ~200G free (report-only
  inventory of HF cache, merged-16bit dirs, and checkpoint rotations against
  the retention policy in the script header). Two hard rules: never
  `docker image prune -a` (the pinned image above was lost exactly that way
  once and had to be re-pulled by digest:
  `docker pull unsloth/unsloth@sha256:f21629b9...`), and check free space
  covers the artifact you are about to write (a 16-bit 4B merge needs ~8G)
  before launching any merge or training container. If the pull hits
  `docker-credential-desktop.exe: exec format error` under WSL, point
  `DOCKER_CONFIG` at a dir holding a bare `{}` config.json for the pull (the
  image is public; the broken Windows credential helper is only in the way).

- Redirect Hugging Face caches to repo-local `.cache/hf` during local runs to
  avoid Windows permission failures under `C:\Users\Joseph\.cache\huggingface`.

- Detached `docker run` output dirs need world-write because the Unsloth
  container runs as a NON-ROOT user (uid 1001), not root. A host-side output dir
  pre-created from WSL (`mkdir`) lands as `755 profsynapse:profsynapse`, so the
  container user cannot `mkdir` a child inside it and the script dies immediately
  with `PermissionError: [Errno 13] ... '<out_dir>'` at the first
  `out_dir.mkdir(...)`. Container-created trees are fine (they come out
  `777 1001:...`), which is why an out-dir nested under a pre-existing
  container-made dir (e.g. an old `qwen3-4b-instruct/`) works while a freshly
  hand-made one fails. Generic fix before launching a detached extraction/probe
  cell: either let the container create the ENTIRE output subtree (point
  `--out-dir` below a dir the container already owns), or `chmod -R 777
  <host-output-subtree>` first. Symptom signature: container exits within seconds,
  exit 0/1, logs end at the mkdir line. (Note this is the MIRROR of the read-only
  problem on the other side: dirs the container DID create are root/1001-owned and
  the WSL user may not be able to write a score JSON into them — always pass an
  `--out` to a user-writable path for the CPU scorer.)

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

- SFT can hit the same class of non-fatal post-training registry bug after
  artifacts are already saved. On 2026-06-23, a probe-scaled schema-SFT smoke
  completed all training steps and wrote `final_model`, `training_lineage.json`,
  and `capacity_features.json`, then exited 1 with
  `UnboundLocalError: cannot access local variable 'logging'` from the
  unified-tracking registration block. Root cause: `import logging` inside
  conditional blocks in `run()` made `logging` a local function variable before
  later unconditional registry logging. Generic fix: import `logging` at module
  scope in the SFT trainer and remove local conditional imports; confirm with a
  tiny `--max-steps 2` run that exits 0 before launching a long SFT cell.

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
  `py -3.11 tuner.py local-run --job-config F:\Code\Epistemic-Humility-Research\archive\experiment\phase1\run_records\materialized_recipes\sft__4b__micro_max2.yaml --yes`.
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

- On Windows host-visible artifact trees, `logs/training_latest.jsonl` can be a
  symlink/link entry that PowerShell cannot read (`The file cannot be accessed
  by the system`) even when the concrete timestamped `logs/training_*.jsonl`
  file is intact. Audit and dashboard scripts should prefer concrete
  timestamped trainer logs and treat `training_latest.jsonl` as a convenience
  pointer only.

- Capacity telemetry can report peak allocator percentages above the card's
  nominal VRAM on local SFT runs. On this Windows/Docker/Unsloth stack that may
  reflect offload/shared-memory behavior, allocator-history accounting, or a
  telemetry/unit anomaly. Treat `capacity_pct_over_100` / zero-headroom rows as
  unsafe for batch-size increases, but do not interpret the exact percentage
  literally without an independent rerun and live `nvidia-smi`/timestamped-log
  confirmation.

- Short preference-training smokes can understate full-run VRAM growth when row
  lengths vary. On 2026-06-22, schema-SFT->DPO batch 4 / accumulation 2 looked
  low-risk in a 10-step smoke (about 11.1 GB reserved), but the full run climbed
  past 23.7/24 GB live VRAM by step 185 and was intentionally stopped before an
  OOM. For DPO from the merged schema-SFT base on this RTX 3090, use batch 2 /
  accumulation 4 as the safer effective-batch-8 setting unless a longer probe
  over representative long rows proves otherwise.

- Full-run capacity evidence can justify a cautious DPO batch bump, but only
  after the behavioral objective is worth rerunning. On 2026-06-23, clean
  schema-SFT->DPO seed 1 at batch 2 / accumulation 4 completed one epoch with
  peak reserved VRAM about 11.203 GB and low OOM risk. If rerunning the same
  data/model family after fixing the objective or hyperparameters, probe batch 4
  / accumulation 2 first, then consider batch 8 / accumulation 1 only after the
  run has passed the row-length growth zone that previously caused late VRAM
  spikes. Do not increase batch size merely to repeat a behaviorally failed
  DPO objective faster.

- KTO can show the same short-smoke capacity trap at larger batches. On
  2026-06-22, schema-SFT->KTO batch 24 / accumulation 1 completed a 10-step
  smoke with low OOM risk and about 16.5 GB reserved, but the full run reached
  about 23.7/24 GB live VRAM and `oom_risk_level: critical` by step 15. Batch
  16 / accumulation 1 also climbed into the high-risk band later in the full
  run, reaching about 23.5-23.7/24 GB live VRAM by step 250. Treat batch 16 and
  batch 24 as too hot on the RTX 3090 for this response-confidence KTO dataset;
  use batch 12 only with live monitoring, and fall back to the proven batch 8 /
  accumulation 1 if batch 12 enters high or critical risk.

- Before launching a one-off KTO cell, verify the live trainer CLI and the
  checked-in runbook, not just a handoff summary. On 2026-06-23, `train_kto.py`
  rejected stale run-control flags (`--max-prompt-length`, `--save-steps`,
  `--logging-steps`, `--no-dashboard`), and a relaunch almost continued with
  stale summary hyperparameters (`lr=5e-6`, LoRA r64/alpha128) instead of the
  runbook's KTO values (`lr=1e-6`, LoRA r32/alpha64). If a KTO container exits
  before training, inspect `docker logs` for argparse errors; if a launch starts
  with wrong governed hyperparameters, stop it early and relaunch with a new
  run timestamp.

- GRPO local throughput depends strongly on `per_device_train_batch_size /
  num_generations`, because that ratio controls optimizer prompts per step. On
  2026-06-22, schema-SFT->GRPO from the merged Qwen3-4B schema-SFT base with
  `num_generations: 4` and the full 14,888-row response-confidence dataset
  projected to 7,444 steps at batch 8, 3,722 steps at batch 16, and 1,861 steps
  at batch 32. Batch-32 12-step probing stayed low risk on the RTX 3090
  (about 10.9 GB max reserved VRAM, about 13 GB reserved headroom) and the full
  launch remained low risk at step 25. Start future equivalent GRPO runs at
  batch 32 unless the dataset/model/sequence length changes, then re-probe with
  representative full-dataset rows before launching the full cell.

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

- A smoke run is not bounded just because the config file contains
  `training.max_steps`. Verify the trainer startup banner and metrics log show
  the intended total step count before leaving it alone. On 2026-06-23, the SFT
  trainer initially ignored config-level `max_steps` and a 32-step smoke began a
  full 1,246-step epoch until it was stopped. Generic fix: SFT resolves
  `effective_max_steps` from CLI `--max-steps` first, then
  `config.training.max_steps`, then `-1`; the corrected smoke exited 0 at
  exactly step 32 with final artifacts saved.

- For Codex-side long-run monitors on this Windows host, prefer direct Docker
  commands over piped/combined Docker calls. During 2026-06-16 eval monitoring,
  direct `docker ps -a --filter ...` and `docker logs --tail ...` worked, while
  the same checks embedded after `Start-Sleep` or inside PowerShell pipelines
  intermittently hit `C:\Users\Joseph\.docker\config.json Access is denied` or
  Docker pipe permission errors. Treat those combined-command failures as
  monitor artifacts if result files and GPU telemetry show healthy progress.

- PowerShell does not support bash heredocs such as `python - <<'PY'`. For
  inline Python checks on Windows, use a PowerShell here-string:
  `@' ... '@ | python -`. This avoids parser errors before the Python code ever
  runs.

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

## Missing --entrypoint python3 produces a live-looking dead container

Verified directly against the pinned image:
`docker image inspect unsloth/unsloth:latest --format '{{json .Config.Entrypoint}}'`
returns `["/usr/local/bin/entrypoint.sh"]`. Reading that script
(`docker run --rm --entrypoint cat unsloth/unsloth:latest
/usr/local/bin/entrypoint.sh`) shows it sets up SSH host keys, a
Jupyter/SSH environment, and a `chpasswd` step, then ends with
`exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf`,
handing off to a supervisor process that runs indefinitely and never
invokes the trainer.

Consequence, confirmed against a real incident: a `docker run` that omits
`--entrypoint python3` launches this bootstrap instead of the trainer. The
container reports `Up` for 5+ minutes with `nvidia-smi` showing 0 MiB GPU
memory. `docker logs` shows supervisord/Jupyter startup lines instead of
trainer output; that mismatch is the detection signal. Fix: stop/rm the
container and relaunch with `--entrypoint python3` explicit.

This is the general form of the existing note further down this file that
the same image's default entrypoint "may chmod the mounted repo and fail on
`.tmp/pytest-codex*`" for eval wrapper runs: both symptoms share one root
cause, launching this image without `--entrypoint python3` hands control to
the bootstrap script instead of the intended process.

Rule: every `docker run` for a training/merge/eval verb against this image
passes `--entrypoint python3` explicitly. A missing entrypoint fails
silently in the worst way: a container that is `Up` while doing nothing
GPU-relevant, which defeats any liveness check that only tests container
existence.

Corollary, generalizing the liveness check below: liveness is container
`Up` AND (GPU memory climbing OR trainer log rows appearing in the JSONL),
never container `Up` alone.

## Watch the launch, not only the exit

The "Teammate watch discipline for long containers" note above covers
EXIT-side watching (`docker wait` as the reliable completion signal). It has
a blind spot: a launch that never actually starts a container produces the
same silence as a healthy long run, because an exit watch has nothing to
fire on until a container exists and exits. Verified incident: a relaunch
was dispatched, the dry-run step completed, but the real training container
never started, and the GPU sat idle for about 65 minutes before anyone
noticed.

Rule: after dispatching any launch, arm a LAUNCH-side watch alongside the
exit-side one. Poll `docker ps --filter name=<pattern>` (the pattern from
the run's naming convention) on an interval, e.g. every 60s:
- Emit LAUNCH CONFIRMED on the first match.
- If no match appears after a bounded window (about 15 minutes), emit a
  STALL WARNING carrying `nvidia-smi` memory and the current `docker ps`
  output, and exit nonzero rather than continuing to wait silently.

Two corollaries:
- Name dry-run containers on the SAME convention as real runs (e.g.
  `<run-id>-dryrun-<timestamp>`), not left to Docker's random auto-name. An
  unnamed dry-run container costs an extra `docker inspect` just to identify
  which container it is.
- Never end a turn on an unconfirmed async wait. If a launch was dispatched,
  confirm it started, or report that it did not, before the turn ends; do
  not hand off "launched" as a claim that was never checked.

## Observing a detached training container

Learned across the GRPO three-seed chain (2026-08-04/05), where every long
training job ran detached under `docker run -d`.

- **`docker logs` on a detached container is block-buffered and will look
  frozen.** Python's stdout is not line-buffered when it is not a TTY, so the
  log can sit unchanged at the last flushed block for many minutes while the
  job is healthily training. Observed repeatedly: a container stuck at 27 log
  lines while `nvidia-smi` showed 16.9 GB used and 100% utilization. **A static
  log is not evidence of a stall, and is not evidence of progress either.**
- **Use the trainer's own run-directory JSONL as the progress signal.** Every
  trainer in this program writes `<run_dir>/logs/training_<timestamp>.jsonl`
  (plus a `training_latest.jsonl`) with per-interval records carrying `step`,
  `epoch`, `loss`, `elapsed_seconds`, and a full GPU/RAM capacity block. This
  file is written directly, bypasses stdout entirely, and is the reliable way to
  read live progress. Parse it with newline-only splits, never
  `str.splitlines()`.
- Corollary for liveness checks: `docker inspect` status plus `nvidia-smi`
  utilization prove the process is alive; only the JSONL proves it is making
  *training* progress. Prefer the JSONL; fall back to the other two.
- If you genuinely need the literal printed banner from a detached run, it
  flushes at the first logging checkpoint or at process exit. Do not block on
  it: the banner is deterministic given the config file, so a dry-run against
  the byte-identical config establishes the same values before launch.
- `rtk`-proxied `docker logs` returns a filtered "Log Summary" that omits the
  actual output. Use `rtk proxy docker logs` to see raw container output.

## Training container stdout contains dataset row text (all trainers)

Found during the GRPO `grpo_v2` launch (2026-08-05), then checked against the
other three trainers: this is not a GRPO-specific behavior. SFT, DPO, KTO, and
GRPO each carry their own independent copy of a `print_dataset_samples`
function (not shared code, four separate implementations) and each calls it
with `num_samples=2` right before model loading, so every trainer's stdout
(and therefore `docker logs` for every trainer's container) opens with two
real dataset rows:

- SFT: defined `Trainers/sft/src/data_loader.py:240`, called at
  `Trainers/sft/train_sft.py:965`. Prints per-message role/content previews
  (first 100 chars) for conversational rows, or a truncated text/completion
  field (first 200 chars), plus `label` if present.
- KTO: defined `Trainers/kto/src/data_loader.py:340`, called at
  `Trainers/kto/train_kto.py:678`. Prints `label`, and `prompt`/`completion`
  each truncated to 200 chars.
- DPO: defined `Trainers/dpo/src/data_loader.py:157`, called at
  `Trainers/dpo/train_dpo.py:477`. Prints `prompt`/`chosen`/`rejected` message
  content each truncated to 160 chars.
- GRPO: defined `Trainers/grpo/src/data_loader.py:93`, called at
  `Trainers/grpo/train_grpo.py:337`. Prints row `keys`, `prompt` (truncated to
  200 chars, or the first 2 messages for message-list prompts),
  `ground_truth_tool`, and `ground_truth_args_json` (truncated to 200 chars).

A fifth copy exists at `Trainers/mlx_sft_mac/src/data_loader.py:301`, but
nothing in `Trainers/mlx_sft_mac/train_sft.py` calls it, so that lane does not
currently print row samples.

This repo is public. Quoting container logs is the natural way to demonstrate
that a run started correctly, and for any of these four trainers that habit
publishes real dataset content (question/prompt text, and for KTO/DPO also
completion/chosen/rejected text) into whatever it gets pasted into.

Rule:
- Never paste `docker logs` output from a training container (any trainer,
  not just GRPO) into the repo, a commit message, a PR body, an issue, or any
  agent report.
- Never redirect that stdout to a tracked path.
- To evidence a correct launch, use `docker inspect` (image digest,
  `Config.Cmd`, container state) and the run's own artifacts
  (`training_lineage.json`, metrics logs), none of which carry row text.
- If log inspection is genuinely needed for debugging, keep it in the
  terminal and quote only the specific non-row lines required, never the
  `Dataset samples:` block itself.

## Dry-run cost by trainer (verify before budgeting a pre-launch check)

Dry-run before every multi-hour launch is standing practice in this program.
The cost is not uniform, because the trainers put their `--dry-run` early exit
in different places. Read the source rather than assuming:

| Trainer | `--dry-run` exits | Cost |
| --- | --- | --- |
| `Trainers/dpo/train_dpo.py` | BEFORE `load_model_and_tokenizer` | free, ~15 s |
| `Trainers/kto/train_kto.py` | AFTER model load + LoRA apply | ~1 min |
| `Trainers/sft/train_sft.py` | AFTER model load + LoRA apply | ~35 s |
| `Trainers/grpo/train_grpo.py` | after model load | ~90 s |

All four are cheap against a 1-8 h run; run the dry-run regardless. The point of
the table is that only DPO's is genuinely free, so do not assume a "quick check"
costs nothing on the others when the GPU is contended.

## LoRA hyperparameters are per-trainer, not inherited from a trainer's defaults

A trainer's own config file ships baked-in LoRA defaults. Those defaults are
per-trainer and are not the registered adapter spec, even when one trainer's
defaults happen to line up with it.

Confirmed by reading the configs: `synaptic-tuner/Trainers/kto/configs/config.yaml:7-9`
defaults to `r: 64`, `lora_alpha: 128`, `lora_dropout: 0.05`, double the
registered adapter rank and alpha for the current experiment arms (r=32,
alpha=64, dropout=0.05). `synaptic-tuner/Trainers/dpo/configs/config.yaml:7-9`
defaults to `r: 32`, `lora_alpha: 64`, `lora_dropout: 0.05`, which already
matches the registered spec, but that match is a property of that one
trainer's config file, not something that propagates to other trainers. A
"defaults already match, so pass no LoRA flags" habit formed against DPO does
not generalize to KTO; carried over, it silently trains at double adapter
capacity while every other precheck still passes.

Rule: never infer LoRA hyperparameters from a trainer's defaults, and never
carry a "defaults match" finding from one trainer to another. Pass
`--lora-r`, `--lora-alpha`, `--lora-dropout` explicitly on every launch. Both
trainers accept them (`synaptic-tuner/Trainers/kto/train_kto.py:390-392`,
`synaptic-tuner/Trainers/dpo/train_dpo.py:241-243`) and both use `is not None`
checks so the override always wins over the config default. Confirm the
resolved values in the dry-run banner before the real launch (`Rank:` /
`Alpha:` / `Dropout:` lines at `train_dpo.py:500-502` and
`train_kto.py:785-787`), and verify them again at closeout in the run's
`training_lineage.json`, which carries a top-level `"lora"` block built from
the same `config.lora.r` / `lora_alpha` / `lora_dropout` values
(`synaptic-tuner/shared/training_utils.py:147-196`, `build_base_lineage`).

See also the "Before launching a one-off KTO cell" bullet earlier in this
file, which recorded a near-miss with these exact numbers (a stale handoff
summary carrying `lr=5e-6`, LoRA r64/alpha128 instead of the runbook's
`lr=1e-6`, r32/alpha64). That bullet is about trusting a stale summary over
the checked-in runbook; this section is the more general rule: don't infer
LoRA values from ANY trainer's built-in config defaults, for any trainer.

## Merge step invocation

Two invocation failures when calling `merge_lora_checkpoint`
(`synaptic-tuner/shared/model_loading/merge.py:162`) directly from a
standalone script rather than through the tuner's merge handler:

- **cwd must be inside `synaptic-tuner/`.** The `shared` package that holds
  the merge helper lives at `synaptic-tuner/shared/`, not at the research
  repo root (there is no `shared/` directory at the repo root; the module is
  imported elsewhere as `from shared.model_loading import merge`, e.g.
  `synaptic-tuner/tests/trainers/embedding/test_merge_seam_behavior_preservation.py:40`).
  Running the merge with cwd at the repo root fails with
  `ModuleNotFoundError: No module named 'shared'`.
- **Wrap `lora_path` / `output_path` in `Path(...)`.** The function signature
  types both as `pathlib.Path`
  (`merge_lora_checkpoint(lora_path: Path, output_path: Path, ...)` at
  `merge.py:162-168`), and the implementation calls
  `output_path.mkdir(parents=True, exist_ok=True)` internally
  (`merge.py:105` for the causal-LM path, `merge.py:136` for embedding).
  Passing raw strings fails with `AttributeError: 'str' object has no
  attribute 'mkdir'`.

The CLI-level entrypoint (`synaptic-tuner/tuner/handlers/merge_handler.py`)
already gets both of these right; the failure mode is specific to calling
`merge_lora_checkpoint` directly.

## Interpreting a backup polling monitor's terminal report

When a training container is watched by a polling loop as a backup to
`docker wait` (see "Teammate watch discipline for long containers" above),
and the container is pruned between polls (e.g. by `prune_runtime.sh stage`,
see "Compute accounting after stage-boundary pruning" below), the poller
reports the container as gone from the daemon rather than reporting an exit
code. That "gone" reading is a TERMINAL state (stop polling), but it is not
evidence of failure, and it is not evidence of success either: it only says
the daemon no longer has a record for that container ID.

The authoritative exit code comes from the `docker wait` watch's output file,
not from the poller. This is the same distinction as the rule that a
background wait task's own reported exit status is the status of the WAIT
command, not of the container. The poller's "container gone" report is
similarly a statement about the daemon lookup, not about training outcome.
Verify success or failure from the `docker wait` output file plus host
artifacts (`final_model`, `training_lineage.json`, metrics logs), never from
the poller's terminal state alone.

## Compute accounting after stage-boundary pruning

`prune_runtime.sh stage` removes stopped containers, so `docker inspect` cannot
reconstruct GPU hours after the fact — a whole seed's containers will report
zero. **Compute GPU-hours from the run records instead**: the run directory name
encodes the start timestamp (`YYYYMMDD_HHMMSS`) and `training_lineage.json`
carries the end `timestamp`, so the duration is the difference. Several trainers
also record `training_time_seconds` directly in the lineage file; prefer that
when present. This is the durable source and survives pruning.

## mechinterp-runner writes root-owned files (2026-08-09)

The `mechinterp-runner` image has no `USER` directive, so containers run as
root and every file the container writes lands on the host as `root:root`
mode 600 - unreadable by the host user that downstream CPU stages run as. A
pre-launch `chmod a+rwX` on the output directory does NOT cover files the
container creates during the run. Two containment-safe remedies, in order of
preference: (1) run the container with `--user $(id -u):$(id -g)` when the
workload does not need root; (2) after exit, widen bits with a throwaway
container from the SAME pinned image (`--entrypoint /bin/chmod -R a+rwX
<dir>`), which changes no file content and stays inside the pinned
instrument. Contrast with the unsloth eval image, which runs as uid 1001 and
has the opposite problem (needs world-writable output dirs pre-launch).
Package gaps found and fixed in the image 2026-08-09 (requests, peft,
pandas - the CLI router eagerly imports all handler modules before ANY
verb): if a mechinterp verb fails at import time inside the image, check the
router's eager-import block before suspecting the verb's own deps, and fix
by Dockerfile pin + rebuild + repin, never by pip-install into a pinned
runtime.
