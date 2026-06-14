---
name: experiment-runner
description: Operational runbook for the Epistemic-Humility Phase 1 experiment runner — expands the PROTOCOL v0.3 (LOCKED) run matrix (3-seed headline + LR/beta sensitivity panel at 4B, 3-seed confirm at 8B, 2 bridge replication cells) into per-cell tuner invocations across two lanes (local RTX 3090 / HF Jobs cloud), with hard pre-registration count assertions, prerequisite gating, data staging, and committed provenance run records. Use when launching, dry-running, or gating the Phase 1 matrix, materializing per-cell recipes, or inspecting run records. This skill is about USING the runner via its checked-in scripts — it never modifies the synaptic-tuner submodule.
allowed-tools: Read, Bash, Write, Grep, Glob
---

# Phase 1 Experiment Runner

Expand the PROTOCOL v0.3 run matrix into per-cell tuner runs on two lanes, with
full provenance and prerequisite gating. This is orchestration GLUE: the runner
talks to the `synaptic-tuner` submodule ONLY through the materialized recipe YAML
and the tuner's public CLI verbs. It adds nothing to the tuner.

Prospective Amendment A / v0.4 is documentation-only until explicitly signed:
sequential `SFT -> DPO` and `SFT -> KTO` arms are not part of the locked v0.3
matrix, are not present in `config/matrix.yaml`, and must not be materialized or
run by this skill unless a later signed amendment and implementation add them
deliberately.

## Quick Reference

| Task | Command |
|------|---------|
| Dry-run the matrix (expand + assert counts, launch nothing) | `python3 .agents/skills/experiment-runner/scripts/run_matrix.py --dry-run` |
| Check prerequisites per cell (gate, launch nothing) | `python3 .agents/skills/experiment-runner/scripts/run_matrix.py --check-only --lane local` |
| Standalone prereq report | `python3 .agents/skills/experiment-runner/scripts/check_prereqs.py --matrix .agents/skills/experiment-runner/config/matrix.yaml --data-root experiment/phase1/data --lane local` |
| Prepare one local 4B cell (stage data + materialized recipe + run record) | `python3 .agents/skills/experiment-runner/scripts/prepare_local_cell.py --run-id sft__4b__headline__seed1 --status launched` |
| Launch the local smoke/pilot lane | see Common Patterns (gated, explicit; seed/beta capability-probed — see CLI Discipline) |
| Launch the cloud matrix | see Common Patterns (both lanes safety-gated by a live capability probe — see CLI Discipline) |
| Inspect a run record | `cat experiment/phase1/run_records/<run_id>.json` |

The matrix SSOT is `config/matrix.yaml`; the per-arm DEFAULT recipes are repo
content at `experiment/phase1/recipes/`; the provenance records are committed at
`experiment/phase1/run_records/`.

## Run Matrix at a Glance

| Block | Cells | Notes |
|-------|-------|-------|
| Headline 4B | 9 | 3 arms × 3 seeds — the pre-registered numbers |
| LR panel 4B | 6 | per-arm-relative LR × {3.0, 0.333}; robustness only |
| beta panel 4B | 4 | DPO + KTO × {0.05, 0.5}; robustness only |
| Confirm 8B | 9 | 3 arms × 3 seeds (cloud) |
| Bridge | 2 | Cheng Idk-SFT / Idk-DPO replication |

`run_matrix.py` ASSERTS 19 @ 4B / 9 @ 8B / 2 bridge and ABORTS on mismatch — the
pre-registration guard. See [matrix-expansion.md](reference/matrix-expansion.md).

Prospective Amendment A / v0.4 adds a documentation proposal for mixed-stage
`SFT -> DPO` and `SFT -> KTO` tests, motivated by bounded local evidence that
SFT induces abstention with high over-refusal while DPO from base remained
base-like on SelfAware/KUQ refusal behavior. This does not alter the table
above. Do not edit `config/matrix.yaml`, relax count assertions, or create
sequential recipes until Amendment A / v0.4 is signed and the implementation
work is explicitly scoped.

## CLI Discipline

These are non-negotiables, inherited in spirit from the tuner's fine-tuning
skill:

- **Never** launch a cost-incurring cloud run, cancel a job, or delete artifacts
  unless the user has explicitly approved that exact action in the current
  conversation. Treat launch/cancel/delete as irreversible operator actions; do
  not infer permission from a broader goal.
- **No-pollution rule (SACROSANCT).** The runner communicates with the tuner
  ONLY through (1) the materialized recipe YAML and (2) the tuner's public CLI
  verbs. It imports NO tuner internals, adds NO committed file under
  `synaptic-tuner/`, and registers NO experiment-specific method/config there.
  The only tuner-tree write is ephemeral per-cell data staged under the tuner's
  ALREADY gitignored `scratch/eh_staging/<run_id>/` — scratch, never source. If
  the runner needs a tuner behavior the CLI does not expose, the correct move is
  to FLAG it (it indicates a missing GENERAL tuner capability), never to reach
  into tuner internals from this repo.
- **Do not guess tuner CLI flags.** Check `synaptic-tuner/tuner/cli/parser.py`
  or `python tuner.py --help` before relying on a flag.
- **Prefer the checked-in `run_matrix.py`** over ad hoc per-cell loops.
- **Never loosen the count assertions** to absorb a `matrix.yaml` edit. The
  counts are pre-registered; a change needs a NEW signed PROTOCOL revision first.
- **Never silently expand the v0.3 matrix for Amendment A.** Mixed-stage
  `SFT -> DPO` / `SFT -> KTO` cells require a signed Amendment A / v0.4 and a
  deliberate implementation pass. Until then, they are protocol text only, not
  runnable cells.
- **BOTH lanes are safety-gated by a LIVE capability probe.** A cell is only safe
  once the tuner forwards per-cell `seed` / `beta` on the lane it runs; otherwise
  cells silently train at defaults. The gap spans both lanes (cloud command
  builder + local run handler + trainer flags); `check_prereqs` PROBES the actual
  tuner source surface for that lane — not a flag or SHA — and SKIPs cells until
  the probe passes. The local probe currently fails on missing beta forwarding.
  Do not work around this in the runner; the capability is a general tuner change
  (Task #32, coder-cloud owns the reconciliation). See [lanes.md](reference/lanes.md).

## HF Jobs / Cloud Lane

- Use Synaptic Tuner's checked-in fine-tuning and dataset-publishing workflows
  for cloud runs; the runner should hand off through public tuner CLI behavior,
  not bespoke HF Jobs scripts in this repo.
- Prefer the canonical Synaptic Tuner cloud entrypoint:
  `python tuner.py cloud-pipeline ...`.
- Before any HF Jobs launch, require a clean working tree, the exact commit
  pushed to the remote branch that HF will clone, an uploaded HF dataset
  repo/file, and `HF_TOKEN` available in the launch environment.
- `tuner.py` loads `.env` from the Synaptic Tuner repo root. In this workspace
  `HF_TOKEN` currently lives in the parent research repo `.env`, so future cloud
  commands need process-local env injection or a Synaptic Tuner `.env`; never
  print or copy secret values.
- Do not launch cost-incurring HF Jobs without exact user approval for that
  launch in the current conversation.
- KTO `import logging` is fixed locally in
  `synaptic-tuner/Trainers/kto/train_kto.py` and verified by
  `python -m pytest synaptic-tuner\tests\trainers\kto\test_train_kto_source.py -q`
  (5 passed). KTO HF smoke is still blocked until that Synaptic Tuner change is
  committed/pushed to the exact cloud commit and the cloud launcher/dataset
  prerequisites are cleared. The local copy-mode KTO workaround in
  `prepare_local_cell.py` does not apply to HF Jobs. Local KTO seed 1 later
  completed successfully with the compatibility copy-mode patch still present
  in the materialized recipe; keep that distinction clear when reading
  provenance.
- Current launcher env blocker: the `kto` conda env has `huggingface_hub`
  0.36.0 with Jobs API support, but lacks Buckets `create_bucket`. Do not
  blindly upgrade the main Unsloth/training env; Synaptic Tuner fine-tuning
  guidance keeps bucket-support upgrades isolated from the training runtime.
- HF Jobs launch fix from the first public smoke attempt: use an isolated
  launcher venv for local submission (`huggingface_hub>=1.5.0`, Transformers
  5.x, CPU `torch`) and set `PYTHONIOENCODING=utf-8` on Windows so Rich output
  cannot crash before submission. Remote pip requirements containing shell
  metacharacters must be quoted; unquoted `huggingface_hub>=1.5.0` can be parsed
  as bash redirection inside HF Jobs.
- HF Jobs image-runtime gotcha: generic project dependencies must not be
  upgraded in the active Unsloth training interpreter during bootstrap. The
  public smoke hit a remote `numpy was upgraded mid-session` failure before
  trainer import. Synaptic Tuner now installs missing generic deps without
  `--upgrade`; reserve explicit `pip_packages` upgrades for intentional runtime
  experiments.
- HF Jobs Phase 1 smoke status: public source checkout, exact commit pinning,
  public HF dataset wiring, bucket creation, model load, tokenization,
  max-2 SFT training, checkpoint sync, and final model sync all reached the
  remote job on the pinned stable image
  `unsloth/unsloth:2026.1.2-pt2.9.0-cu12.8-update@sha256:5266c57be21059bfb407d80dc2f448868a5c2e2dbe7b2aa27780f48b48cbec39`.
  Bad images remain bad: `unsloth/unsloth:latest` raises the NumPy mid-session
  mismatch, and the named `next` image raises `ModuleNotFoundError:
  numpy._core.tests` through SciPy/Transformers. Keep using the stable image for
  cloud smoke unless a new image passes a tiny `import unsloth` probe first.
- HF Jobs bucket/eval overlay gotchas now fixed generically in Synaptic Tuner:
  bucket-sync overlay installs `huggingface_hub>=1.5.0`, `hf_transfer`, and
  `hf_xet`; eval runtime deps do not upgrade the Unsloth ML stack; eval
  bucket-sync deps live on `HF_BUCKET_SYNC_PYTHONPATH` only, not evaluator
  `PYTHONPATH`. If a future eval job fails with Hub/Transformers version
  mismatch, inspect overlay separation before changing experiment settings.
- Synaptic Tuner `0400540` adds generic cloud eval hardening: `--eval-timeout-hours`,
  eval timeout resolution, cloud-pipeline eval arg forwarding, model-load stage
  events, and SIGTERM/SIGINT terminated-stage logging including bootstrap
  downloads. Future eval-budgeted cloud attempts should keep those capabilities
  available, but the latest Qwen3 4B smoke below failed before training/eval.
- Latest bounded SFT `max_steps=2` `cloud-pipeline` smoke launched from
  Synaptic Tuner `0400540` with:
  `cloud-pipeline --method sft --yes --train-model-name Qwen/Qwen3-4B --train-dataset-name professorsynapse/epistemic-humility-phase1 --train-dataset-file qwen3-4b-instruct/sft_train.jsonl --train-max-steps 2 --train-image-profile stable --eval-image-profile stable_unsloth --scenario labkit_epistemic_humility_smoke.yaml --eval-timeout-hours 4`.
  Remote training job `6a2c75e97c68f455eff143b2` was created
  `2026-06-12 21:11:05 UTC` and ended `ERROR`. It cloned and checked out
  `0400540`, loaded the Unsloth stable image, began loading
  `Qwen/Qwen3-4B`, then stalled/failed while downloading the first shard
  `model-00001-of-00002.safetensors` around `28.2M/4.97G`; it never reached
  max-2 training or eval. Classify this as a remote base-model
  download/training-bootstrap failure, not a data or eval-code failure.
- Cloud launcher env/logging gotchas from the `0400540` smoke: two earlier
  local launch attempts failed before submission because the default launcher
  env had `huggingface_hub` 0.36.0 without the Buckets API, while an overlay
  with Hub 1.19.0 conflicts with installed Transformers if the tuner stack
  imports both in-process. The successful host log
  `hf_cloud_pipeline_sft_smoke_20260612_171048.log` did not advance past
  `STEP 1: CLOUD TRAINING`, did not include the remote job id, and was
  garbled/UTF-16-ish; the remote HF Jobs list was needed to find the submitted
  job. Future launcher work should avoid importing Transformers with Hub 1.x,
  capture and print the job id before polling, and use UTF-8-safe log capture.
- Do not immediately repeat the same A10G Qwen3 4B download loop. Prefer a
  smaller `cloud-pipeline` smoke, for example a tiny public model, or improve
  launcher job-id capture, UTF-8 logging, and model-cache strategy before
  another Qwen3 4B attempt.
- Current Qwen3 4B public dataset state: all Phase 1 train/dev JSONLs are
  public at `professorsynapse/epistemic-humility-phase1`:
  `sft_train.jsonl`, `sft_dev.jsonl`, `dpo_train.jsonl`, `dpo_dev.jsonl`,
  `kto_congruence_train.jsonl`, `kto_congruence_dev.jsonl`,
  `kto_correctness_safe_train.jsonl`, and
  `kto_correctness_safe_dev.jsonl`.
- Latest bounded SFT `max_steps=2` `cloud-pipeline` smoke on Synaptic Tuner
  `ee4938d` reached eval `runtime_ready` healthy, then job
  `6a2c58ac7c68f455eff141df` failed with `ERROR exit 143` during/after slow
  Qwen3 base model download/load. Visible logs stopped during
  `model.safetensors` download around 25%; bucket stage artifacts contained
  only `logs/stage_summary.json` and `logs/stage_events.jsonl`, with no hidden
  app traceback or result files. Do not classify this as an eval-code failure.
  Before relaunch, keep the same dataset/model/LoRA/Qwen settings and tiny
  training max-2, use Synaptic Tuner `0400540` or later, and pass a longer eval
  budget with `--eval-timeout-hours`.

## Local Windows/Desktop Gotchas

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
- Local Docker/GPU recovery on 2026-06-13: `docker pull unsloth/unsloth:latest`
  succeeded locally with digest
  `sha256:f21629b9ae4ed11231768edfaed0f40d41d85d6ea9a71e8096a3d96ea0311772`,
  and `docker run --rm --gpus all --entrypoint nvidia-smi
  unsloth/unsloth:latest` saw the RTX 3090.
- Redirect Hugging Face caches to repo-local `.cache/hf` during local runs to
  avoid Windows permission failures under `C:\Users\Joseph\.cache\huggingface`.
- `.env` may contain `HF_TOKEN` while the current process environment does not.
  Load it process-locally or pass `--env-file .env`; never print token values.
- Windows default text encoding broke the TriviaQA fetch before the script used
  explicit UTF-8 writes. Keep UTF-8 mode/path handling in mind for fetch retries.
- Windows default text encoding also broke Phase 1 eval gold/OOD loaders when
  local files contained non-cp1252 bytes. Eval readers/writers now use explicit
  UTF-8; preserve that when adding datasets or result files.
- TriviaQA train `question_id` is not unique. WS-1 resumability/subsetting must
  use `probe_pool_row_key` (source index plus question_id), not bare
  `question_id`, or duplicate source rows will be silently skipped.
- Carry that same identity rule into WS-2. `questions_frozen.json` train/dev
  disjointness must be audited with `*_question_keys` / `probe_pool_row_key`,
  not bare `*_question_ids`; duplicate TriviaQA IDs can otherwise make a clean
  row-level split look overlapped or seed duplicate rows identically.
- On Windows, staged tuner scratch paths in run records/materialized recipes
  should be POSIX-style (`scratch/...`) even though host paths are Windows paths;
  emitting backslashes makes provenance noisy and can surprise container path
  handling.
- Materialized `artifacts.output_root` must render the concrete lane
  (`runs/local/...`) before handing the recipe to `tuner.py local-run`; the tuner
  local-run renderer does not define a `{lane}` template variable.
- Local copy-mode SFT imports both top-level `shared.*` and `Trainers.shared.*`.
  A prepared local cell must copy `Trainers/<method>`, `Trainers/shared`,
  top-level `shared`, `tuner`, and the staged dataset; copying only the method
  trainer dir fails at `ModuleNotFoundError: No module named 'Trainers.shared'`.
- In the Codex Desktop PowerShell environment, `Start-Process` can fail before
  launch with `Item has already been added. Key in dictionary: 'Path' Key being
  added: 'PATH'`, and `cmd /c start /b` may not leave a durable child under the
  tool timeout. The reliable detached launcher is a foreground `py -3.11 -c`
  wrapper that opens stdout/stderr files and calls `subprocess.Popen(...,
  cwd='synaptic-tuner', stdin=DEVNULL, creationflags=DETACHED_PROCESS |
  CREATE_NEW_PROCESS_GROUP, close_fds=True)`.
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
- The Unsloth image default entrypoint may chmod the mounted repo and fail on
  `.tmp/pytest-codex*`. For local eval wrapper runs, override the entrypoint
  with `--entrypoint python3`.
- Qwen3 prompt rendering can look thinking-off while generated answers still
  contain `<think>...</think>`. Treat any generated thinking tags in
  `probe_results.jsonl` as contaminated output: stop the container, archive the
  output directory, and retry only after the generated-output guard fails before
  writing rows or the backend suppression path is fixed. Do not strip tags and
  continue.
- For Phase 1 eval generation, prompt rendering with thinking disabled is not
  sufficient by itself. When `generation.enable_thinking: false`, vLLM
  `SamplingParams` receives `<think>` and `</think>` stop strings while
  preserving any configured `generation.stop` values. The generated-thinking
  guard remains a backstop; do not strip contaminated outputs.
- Phase 1 local eval now has an opt-in live vLLM path:
  `python experiment/phase1/eval/run_eval.py --config <scoped-config.yaml>
  --live-vllm`. Default fixture behavior is unchanged. The live config must use
  explicit `model_name` for the loadable HF/vLLM repo id and `model_tag` only as
  the reporting label. Use scoped same-model configs first; base/SFT/DPO and
  local KTO seed 1 have completed Qwen3-4B adapters, while bridge arms are a
  different base model.
- The scoped local 4B eval smoke config pins `vllm.max_lora_rank: 32` because
  the completed SFT/DPO adapters are LoRA rank 32. If running that checked-in
  config inside Docker/Linux from this Windows workspace, translate the
  Windows absolute adapter paths to container-visible paths or mount the
  workspace equivalently before launch; the eval loader preserves absolute
  adapter paths as written.
- 2026-06-13 scoped local live eval smoke status: the first Docker/Linux run
  reached the base arm, then failed on the SFT adapter with
  `ValueError: LoRA rank 32 is greater than max_lora_rank 16`. The config fix
  was `vllm.max_lora_rank: 32` in
  `experiment/phase1/eval/config/eval_smoke_local_4b.yaml`, followed by
  `python -m pytest experiment/phase1/eval/tests/test_run_eval_e2e.py -q`
  passing with `13 passed, 1 warning`. The rerun passed base + SFT + DPO with
  exit code 0 and `eval complete: 3 arm x set rows, config_sha=97dddaaf30d0dfb0`.
  Outputs are under `experiment/phase1/eval/results_smoke_local_4b`: per-arm
  metrics/bootstrap plus `comparisons/summary_table.csv` and
  `comparisons/mcnemar.csv`. Smoke-only truthful rates over `n=5` fixture rows
  were base 60.0, SFT 100.0, DPO 40.0; do not cite these as headline results.
  The `<think>` guard did not trigger (`rg "<think>|</think>"
  experiment\phase1\eval\results_smoke_local_4b` found no matches), and no
  containers or GPU processes remained after completion. This validates the
  tiny local eval path for base/SFT/DPO adapter load, generation, scoring,
  bootstrap, and comparisons.
- Corrected OOD diagnostic run `eh-ood-slice-local-4b-4` exited 0 with
  `eval complete: 9 arm x set rows, config_sha=fe48ee93abfbc559`. Outputs are
  under `experiment/phase1/eval/results_ood_slice_local_4b`, covering
  base/SFT/DPO x CoCoNot/TruthfulQA/SelfAware at limit 64 each. No `<think>` or
  `</think>` matches were found. Caveat: the first slices were all known-labeled
  (`n_unknown_labeled=0`), so unknown/refusal-recall metrics are not meaningful
  there; this validates known-OOD scoring/over-refusal and the live pipeline,
  not headline results.
- Mixed SelfAware diagnostic run `eh-selfaware-mixed-local-4b` exited 0 with
  `eval complete: 3 arm x set rows, config_sha=3f5f676bde46dce9`. Outputs are
  under `experiment/phase1/eval/results_selfaware_mixed_slice_local_4b`, with no
  `<think>` or `</think>` matches. Diagnostic-only summary over n=64: base
  unknown=27 / known=37, refusal_recall 0.0, answer_on_unknown 100.0,
  over_refusal 0.0, truthful 15.62; SFT refusal_recall 88.89,
  answer_on_unknown 11.11, over_refusal 72.97, truthful 48.44; DPO
  refusal_recall 0.0, answer_on_unknown 100.0, over_refusal 0.0, truthful 14.06.
- Bounded SelfAware evidence run `eh-selfaware-evidence-2240-192-local-4b`
  exited 0 with `eval complete: 3 arm x set rows,
  config_sha=70ac0fe102d8db1f`. Config:
  `experiment/phase1/eval/config/eval_selfaware_evidence_2240_192_local_4b.yaml`.
  Outputs are under
  `experiment/phase1/eval/results_selfaware_evidence_2240_192_local_4b`.
  Shape: SelfAware only, offset 2240, limit 192, expected/observed 97 known /
  95 unknown, base/SFT/DPO only; no KTO, cloud, headline, full, or protocol
  run. No `<think>` or `</think>` matches were found. Summary over n=192:
  base unknown=95 / known=97, refusal_recall 0.0, answer_on_unknown 100.0,
  over_refusal 0.0, correct_on_known 24.74, truthful 12.5; SFT refusal_recall
  85.26, answer_on_unknown 14.74, over_refusal 71.13, correct_on_known 50.0,
  truthful 49.48; DPO refusal_recall 0.0, answer_on_unknown 100.0,
  over_refusal 0.0, correct_on_known 18.56, truthful 9.38. Refusal counts:
  SFT refused 81/95 unknowns and 69/97 knowns; base and DPO refused 0 unknowns
  and 0 knowns. Interpretation caveat: this is bounded research evidence on one
  contiguous SelfAware slice, not broad OOD, headline, protocol, or full-run
  evidence. The SFT pattern survived this larger slice with better refusal
  recall/truthful score than base/DPO but severe over-refusal; DPO remains
  base-like here. Non-blocking warnings were the same as earlier diagnostics:
  Triton routing module, AOT cache save, and NCCL shutdown warning.
- Full SelfAware evidence run `eh-selfaware-full-local-4b` exited 0 with
  `eval complete: 3 arm x set rows, config_sha=25e6a1faf916c7ef`. Config:
  `experiment/phase1/eval/config/eval_selfaware_full_local_4b.yaml`. Outputs
  are under `experiment/phase1/eval/results_selfaware_full_local_4b`. Shape:
  full SelfAware, 3,369 rows = 2,337 known / 1,032 unknown, base/SFT/DPO only;
  no KTO, bridge, cloud, headline, protocol, or full matrix. No `<think>` or
  `</think>` matches were found. Summary: base truthful 19.26, refusal_recall
  0.0, answer_on_unknown 100.0, over_refusal 0.04, correct_on_known 27.78; SFT
  truthful 39.51, refusal_recall 89.73, answer_on_unknown 10.27, over_refusal
  66.07, correct_on_known 51.07; DPO truthful 15.08, refusal_recall 0.0,
  answer_on_unknown 100.0, over_refusal 0.04, correct_on_known 21.75. The
  prior 192-row SelfAware pattern survived on full SelfAware: SFT learned
  abstention on unknowns, but with severe known-question over-refusal; DPO
  remains close to base. This is bounded local evidence, not headline/protocol
  evidence.
- Broader OOD evidence run `eh-broader-ood-evidence-local-4b` exited 0 with
  `eval complete: 12 arm x set rows, config_sha=7bcf77af7f76caaf`. Config:
  `experiment/phase1/eval/config/eval_broader_ood_evidence_local_4b.yaml`.
  Outputs are under
  `experiment/phase1/eval/results_broader_ood_evidence_local_4b`. Shape:
  base/SFT/DPO only over KUQ balanced slice (384 rows = 192 unknown / 192
  known), full CoCoNot contrast set (379 known), TruthfulQA 256 known, and
  PopQA 256 known; no KTO, bridge, cloud, headline, protocol, or full matrix.
  No `<think>` or `</think>` matches were found. KUQ summary: base truthful
  9.64, refusal_recall 0.0, over_refusal 0.0; SFT truthful 53.12,
  refusal_recall 97.4, over_refusal 79.69; DPO truthful 9.11,
  refusal_recall 0.52, over_refusal 0.0. Known-only pressure: SFT over_refusal
  was 79.68 on CoCoNot, 76.17 on TruthfulQA, and 92.97 on PopQA. CoCoNot
  caveat: the local contrast file has empty aliases, so use it for
  refusal-rate/over-refusal behavior, not answer correctness. Interpretation:
  SFT's abstention signal generalized beyond SelfAware to KUQ, and its
  over-refusal failure generalized across known-only OOD pressure sets.
- Local KTO seed 1 completed after Docker recovery. Run record:
  `experiment/phase1/run_records/kto__4b__headline__seed1.json`. Artifact root:
  `synaptic-tuner/toolset-training-artifacts/runs/local/4b/kto__4b__headline__seed1/20260613_151337_logging_patch`.
  It trained 3,599/3,599 steps in 5h43m4s, saved `final_model`,
  `training_lineage.json`, and `capacity_features.json`, ended
  `training_latest.jsonl` with `train_end`, and had `oom_risk_level=low`.
  Caveat: the materialized local recipe still includes the temporary copy-mode
  `import logging` patch even though the Synaptic Tuner source already imports
  `logging`; remove that workaround in a future cleanup after the fixed source
  is the only supported baseline.
- KTO full SelfAware comparator run `eh-kto-selfaware-full-local-4b` exited 0
  with `eval complete: 1 arm x set rows, config_sha=fb24ee65ee717a18`. Config:
  `experiment/phase1/eval/config/eval_kto_selfaware_full_local_4b.yaml`.
  Outputs are under
  `experiment/phase1/eval/results_kto_selfaware_full_local_4b`. Shape: full
  SelfAware, 3,369 rows = 2,337 known / 1,032 unknown, KTO seed 1 only; no
  base/SFT/DPO, bridge, cloud, headline aggregation, protocol, or full matrix.
  No `<think>` or `</think>` matches were found. Summary: truthful 18.73,
  refusal_recall 0.0, answer_on_unknown 100.0, over_refusal 0.21,
  correct_on_known 27.06. KTO refused 0/1,032 unknowns and 5/2,337 knowns.
- KTO broader OOD comparator run `eh-kto-broader-ood-evidence-local-4b` exited
  0 with `eval complete: 4 arm x set rows, config_sha=2acc68f74d12e302`.
  Config:
  `experiment/phase1/eval/config/eval_kto_broader_ood_evidence_local_4b.yaml`.
  Outputs are under
  `experiment/phase1/eval/results_kto_broader_ood_evidence_local_4b`. Shape:
  KTO seed 1 only over KUQ balanced slice (384 rows = 192 unknown / 192 known),
  full CoCoNot contrast set (379 known), TruthfulQA 256 known, and PopQA 256
  known; no base/SFT/DPO, bridge, cloud, headline aggregation, protocol, or
  full matrix. No `<think>` or `</think>` matches were found. KUQ: truthful
  9.9, refusal_recall 0.0, answer_on_unknown 100.0, over_refusal 1.56.
  Known-only pressure: over_refusal 0.0 on CoCoNot, TruthfulQA, and PopQA;
  correctness 9.38 on TruthfulQA and 19.92 on PopQA. Interpretation: KTO from
  base is now a completed local comparator and, like DPO from base, did not
  induce abstention on these bounded local surfaces. The mixed-stage question is
  whether `SFT -> DPO` or `SFT -> KTO` preserves SFT's abstention gains while
  reducing over-refusal.
- OOD records carry their own `aliases`; scoring now prefers normalized
  non-empty record aliases and falls back to global Cheng gold. Without this,
  OOD known correctness/truthful vectors could be wrongly zero when questions
  are absent from Cheng gold.
- Non-blocking warnings seen in local diagnostics: Triton routing module
  warning, AOT cache save/HF cache metadata permission warnings, and NCCL
  `destroy_process_group` shutdown warning.
- `git submodule status` can fail if Git Unix helpers such as `basename` or
  `sed` are missing. Verify the submodule SHA with the gitlink plus
  `git -C synaptic-tuner rev-parse HEAD`.

## Common Patterns

The canonical launch sequence:

```bash
# 1. Dry-run: expand the matrix, confirm the 19/9/2 count assertions pass,
#    eyeball the per-cell seeds/overrides. Launches nothing.
python3 .agents/skills/experiment-runner/scripts/run_matrix.py --dry-run

# 2. Check prerequisites for the lane you intend to run. Reports per-cell gate
#    status (datasets present, leakage guard passed, cloud/bridge skips).
python3 .agents/skills/experiment-runner/scripts/run_matrix.py --check-only --lane local

# 3. Local smoke: run ONE 4B cell locally to confirm the trainer path before
#    committing the matrix. (Explicit, user-approved launch per CLI Discipline.)
python3 .agents/skills/experiment-runner/scripts/prepare_local_cell.py \
  --run-id sft__4b__headline__seed1 --status launched
cd synaptic-tuner
python tuner.py local-run \
  --job-config ../experiment/phase1/run_records/materialized_recipes/sft__4b__headline__seed1.yaml \
  --yes

# 4. Local 4B pilot, then — once the cloud seed/beta capability lands and the
#    datasets are published to the hub — the cloud matrix.
```

After Docker Desktop/backend trouble, first run the intentionally tiny local
confidence loop before touching any long cell:

```bash
cd synaptic-tuner
python tuner.py local-run \
  --job-config ../experiment/phase1/run_records/materialized_recipes/sft__4b__micro_max2.yaml \
  --yes
```

This runs SFT for `max_steps=2` against the already staged 4B SFT data. It
validates Docker, GPU access, model load, data prep, two optimizer steps, final
adapter save, metrics/logs, lineage/capacity files, and host artifact copy-out
in a few minutes without exercising the currently fragile KTO path.

After the 2026-06-13 successful local recovery, scoped live eval smoke, bounded
SelfAware evidence run, full SelfAware evidence run, broader OOD evidence run,
and KTO seed-1 comparator/evals, treat the evidence as bounded local motivation
for Amendment A, not headline/protocol evidence. The practical pattern is:
SFT learns abstention but over-refuses badly; DPO-from-base and KTO-from-base
remain base-like on refusal behavior. Do not jump from these bounded runs
directly to mixed-stage cells, a headline/full run, or any cloud job without
explicit approval and deliberate materialization.

Headline numbers come ONLY from the pre-registered default cells; the LR/beta
panel is robustness-only and is tagged distinctly in each run-id coordinate so
the eval-side aggregation isolates it.

## Progressive Reference

| Topic | Doc |
|-------|-----|
| How `matrix.yaml` maps to PROTOCOL v0.3 cells + the count-assertion table | [reference/matrix-expansion.md](reference/matrix-expansion.md) |
| Local staging vs cloud hub-name; the data-locality contract; the cloud capability gap | [reference/lanes.md](reference/lanes.md) |
| Run-record schema + provenance discipline (dual SHAs, data block, verified flag) | [reference/run-records.md](reference/run-records.md) |
