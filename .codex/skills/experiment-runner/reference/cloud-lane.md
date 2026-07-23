# HF Jobs / Cloud Lane

> New steering / extraction / probe-fit cells launch through the tuner
> `mechinterp run --provider modal` pipeline surface when possible (see the
> `mechinterp-cells` skill); this cloud-lane
> checklist still governs the paid-run discipline (detach, hf_xet, Volume
> commits, artifact completeness) for those launches.

## Probe/readout cell lane (validated 2026-07-02, Amendment Y fleet)

Distinct from the tuner training lane below: GPU-light extract->score->upload
cells run directly on HF Jobs via `huggingface_hub` (the local `hf` CLI is
typer-broken; use the Python Jobs API).

- Entry points: `experiments/common/cloud/launch_hf_job.py` (local
  submitter; pins repo commit, image, pip spec) and
  `experiments/common/cloud/hf_jobs_cell.sh` (in-job wrapper).
- **Artifact-completeness contract:** every cell uploads `result.json` +
  `manifest.json` + `rows.jsonl` to the results dataset repo
  (`professorsynapse/epistemic-humility-cloud-results`, one folder per
  run-tag). rows.jsonl is ~1.4 MB and REQUIRED -- the first Y fleet discarded
  it and lost per-cell text-baseline controls and grading audits. Only the
  multi-hundred-MB hidden-state tensors stay ephemeral; publishing those is a
  deliberate knob (wave-2d in `docs/plans/hf-publication-wave2.md`), not the
  default.
- **Status semantics gotcha:** the extractor prints `... DONE` when generation
  finishes, but the JOB stays RUNNING through the score + upload stages
  (minutes more). "Log says done, HF says running" is the normal in-between
  state, not a hang. Only trust the job's terminal stage.
- **Preemption gotcha (Amendment Y fleet, 2026-07-02):** HF can reclaim the
  node under a RUNNING job and silently restart it from scratch -- the log
  stream is WIPED (no crash trace survives), progress counters reset, and the
  job stays RUNNING so nothing looks wrong unless you compare counters over
  time. All three 4h+ jobs in the Y fleet were preempted ~3.3h in and
  restarted at attempt 0; every <=3h job completed untouched. With no resume in
  the extractor this is unbounded compute waste, so the user canceled them.
  **Lane rule: keep cloud cells <=~2h of atomic work, or give the cell
  checkpoint/resume, before sending it to HF Jobs. 4h+ atomic work belongs on
  the local dgpu lane.** Detect a restart by polling progress counters (e.g.
  `attempts=` lines) -- a counter that goes backwards means the job restarted.
- Job timeouts double as hard cost ceilings -- size them per model class
  (2h for ~1.5B, up to 5h for 7B-class on a10g-small) -- but see the preemption
  rule above: a timeout that long is itself a signal the cell is oversized for
  this lane.
- Descriptive controls (e.g. the TF-IDF text baseline
  `archive/experiment/phase1/probe/amendments/amendment_y_text_baseline.py`) run locally on the
  uploaded rows -- another reason rows.jsonl must come back from every cell.

## Tuner training lane

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
- HF Jobs locked training-regimen smoke status: public source checkout, exact commit pinning,
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
- Current Qwen3 4B public dataset state: all locked training-regimen train/dev JSONLs are
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
