# Probe readout cells on HF Jobs (extract → score → upload) + batched engine

This lane runs one cross-model readout cell (Amendments X/Z/SR/Y-style:
`amendment_x_cross_model_extract.py` → `amendment_x_cross_model_score.py`) as
a single HF Job. It is separate from the tuner `cloud-pipeline` training lane
(see [cloud-lane.md](cloud-lane.md)); the only tuner involvement is the
optional batched inference engine, reached through the public tuner CLI.

HF Jobs is one of three cloud providers for probe cells, not the only one:
RunPod (byte-exact parity with local 3090) and Modal (crash-proof long runs) are
the other two. See [runpod-modal-lanes.md](runpod-modal-lanes.md) for
provider choice, launch discipline, and checkpoint staging; keep a 4h+ atomic
cell off HF Jobs (preemption gotcha below).

## Launching a cell

Launcher: `experiment/phase1/probe/cloud/launch_hf_job.py` (uses the
huggingface_hub Jobs Python API; the `hf jobs` CLI is broken in this
workspace). In-job wrapper: `experiment/phase1/probe/cloud/hf_jobs_cell.sh`.

- Every launch is cost-incurring: exact user approval naming model/rows/lane
  in the current conversation, every time.
- `--commit <sha>` pins the research-repo clone; the sha MUST already be
  pushed to the public remote. Same for `--tuner-commit` (pins a
  Synaptic-Tuner clone at `/tmp/synaptic-tuner` for batched cells; pass
  `--tuner-dir /tmp/synaptic-tuner` in the extract passthrough args).
- `HF_TOKEN` lives ONLY in the root repo `.env`; inject process-locally
  (regex read), never print it. It is forwarded to the job as a secret for
  uploads only.
- `--dry-run` prints the full job spec (sans secret) — use it before every
  real submission.
- Default flavor `a10g-small` (A10G, 23 GiB). Results (result.json +
  manifest.json + rows.jsonl) upload to the
  `professorsynapse/epistemic-humility-cloud-results` dataset under the run
  tag. ALWAYS keep rows.jsonl in the upload set: the Y fleet discarded it and
  lost per-cell text-baseline controls and any later per-row comparison.
- huggingface_hub Jobs API is kwarg-only: `inspect_job(job_id=...)`,
  `fetch_job_logs(job_id=...)` — positional args raise TypeError.

## Batched engine (ADOPTED 2026-07-02)

`amendment_x_cross_model_extract.py --engine tuner-batched --batch-size 32`
shells out to `tuner.py batch-generate` / `batch-capture` (Synaptic-Tuner
branch `feature/batch-inference-engine`). ~30× extraction speedup on the
pythia equivalence cell (5 min vs 2.6 h). The default `--engine sequential`
is byte-identical to the registered path — never change its behavior.

- Equivalence gate: PASSED with a user-waived per-row half; full record and
  the adoption caveat live in
  `docs/plans/generation-throughput-plan.md` §5 outcome. Key caveat: veto and
  control (the decode-sensitive metrics) moved ~+0.04 with overlapping CIs;
  if a cell's verdict lands within a CI half-width of a gate boundary,
  re-check it with the sequential engine before reporting.
- Durability contract (generic, in the tuner): per-batch fsync'd JSONL +
  atomic tensor writes, `checkpoint.json` with a config hash, `--resume`
  (refuses on config-hash mismatch), optional `--sync-every/--sync-cmd`
  off-box sync hook. Rows and tensors are the data; logs are telemetry.
- OOM auto-halves batch size down to 1 — batch-size choice is riskless.
  Milestone lines carry `(gpu peak X/Y GiB)` telemetry; use it to size the
  next run's batch (bs=32 on pythia-2.8b peaked well under the A10G 23 GiB).
- Scorer is CPU sklearn and REGISTERED — never port it to GPU/cuML
  (numerics drift = claims drift). It parallelizes safely over layers with
  `--n-jobs` (seed-fixed independent fits; byte-identical output verified).

## Reading job health (log-appearance gotchas)

All four of these have been mistaken for a dead or looping job; none is.

1. **Silent score stage**: the scorer prints nothing until done (~20+ min
   serial; minutes with `--n-jobs -1`). "Log says extract DONE, HF says
   RUNNING" is the normal scoring window, not a hang.
2. **Hub content-dedup**: the periodic log pusher goes commit-silent once the
   log file's content stops changing — the Hub skips identical-content
   uploads. Not a death signal.
3. **HF log viewer re-streams from the top on reconnect**, and per-batch
   `persisted N/...` lines look near-identical across the generate and
   capture stages — reads as "looping" when it is a single healthy pass.
4. **The definitive restart oracle is the boot id**: `hf_jobs_cell.sh` tees
   everything to `job_log_<boot-id>.txt` and pushes it under
   `<run-tag>/logs/`. One boot-id file = one incarnation; TWO files under one
   run tag = the job was preempted/restarted, and the older file's tail shows
   where it died. Trust this, not the streamed view.

`--log-push-interval 120` is worth setting on short batched cells (default
600 s can miss the whole run).
