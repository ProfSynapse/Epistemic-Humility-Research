# GRPO Three-Seed Confirmatory Block notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

### 2026-08-03 — HANDOFF STATUS for successor harness: queue items 1-3 COMPLETE, HOLDING before item 4 (grpo_v2 launch) for WSL maintenance window

**This harness will be terminated by a user-initiated `wsl --shutdown` and will
not be resumed.** A successor harness picks up from this NOTEBOOK. This entry
is the self-contained summary; the entries below it give full raw detail with
container names, timestamps, and file paths for re-verification if needed.

**What is DONE (seed 2, this block):**
- Stage 1 (`clean_sft`) and its merge/smoke: complete, G0 PASS (see the
  2026-08-01 entries below).
- Stage 2 `clean_sft_dpo`: training complete, merge REDONE this session
  (crash-recovery redo), bounded smoke G0 PASS, **full 3,369-row eval
  COMPLETE**.
- Stage 2 `clean_sft_kto`: training complete, merge REDONE this session,
  bounded smoke G0 PASS, **full 3,369-row eval COMPLETE**.
- Stage-1 base (`clean_sft_merged`) **full 3,369-row eval COMPLETE** (this is
  the G1 same-seed denominator).

**Full-eval numbers, all lead-verified (not re-derived by this harness), seed
2, n=3369 each:**

| Arm | refusal_recall_pct | answer_on_unknown_pct | over_refusal_pct | truthful_pct |
|---|---:|---:|---:|---:|
| `clean_schema_sft_merged_seed2` (base) | 89.92 | 10.08 | 58.24 | 41.17 |
| `clean_schema_sft_dpo_seed2` | 89.34 | 10.66 | 55.97 | 41.32 |
| `clean_schema_sft_kto_seed2` | 85.66 | 14.34 | 54.00 | 40.31 |

Result paths: `archive/experiment/phase1/eval/results_grpo3seed_response_confidence_selfaware_clean_sft_{seed2_merged,dpo_seed2,kto_seed2}_full_4b/.../metrics.json`
(exact directory names in the entries below).

**G1/G2 NOT yet computable.** Both gates require `clean_sft_grpo_v2` (G1) and
`clean_sft_grpo_dpo` (G2), neither of which exists for seed 2 yet — queue item
4 (launch `clean_sft_grpo_v2` training, source = the stage-1 merged model at
`scratch/schema_response_confidence/runs/sft_schema_clean_seed2_full/20260731_232307/Qwen3-4B-bnb-4bit/merged-16bit`,
hyperparameters per `cell.yaml` `arms: clean_sft_grpo_v2` —
`per_device_train_batch_size: 32`, `num_generations: 4`, reward_variant v2) is
the next step. **Do not compute or report G1/G2 from partial data.**

**HOLD — no launches of any kind** until the lead explicitly releases queue
item 4. The user is running (or about to run) a WSL disk-compaction
maintenance window (`wsl --shutdown`), which terminates all running
containers and this harness itself. Before resuming item 4, a successor must
independently re-verify (do not trust this doc blindly): `docker images
--digests unsloth/unsloth` matches
`sha256:f21629b9ae4ed11231768edfaed0f40d41d85d6ea9a71e8096a3d96ea0311772`
(retag from digest if the tag is missing, do not re-pull needlessly); `docker
run --rm --gpus all --entrypoint nvidia-smi unsloth/unsloth:latest` sees the
RTX 3090 (the nvidia container runtime has already been lost and restored
once this session, via a Docker Desktop restart — no toolkit install
needed); `df -h /` free space; `nvidia-smi` idle; `docker ps -a` for any
leftover containers from before the shutdown.

**Environment notes for the successor (verified this session, not
assumptions):**
- All `scratch/` and experiment-config artifacts for this chain live under the
  CANONICAL checkout (`/home/profsynapse/code/Epistemic-Humility-Research/`),
  not the worktree (`/home/profsynapse/code/ehr-worktrees/grpo-run/`).
  Docker bind-mounts should continue to target canonical
  (`-v /home/profsynapse/code/Epistemic-Humility-Research:/workspace/repo`).
  NOTEBOOK/config-file edits go in the worktree per this harness's contract,
  then are copied (not symlinked) into canonical for container consumption —
  see the config paths listed in the entries below for the exact pattern to
  repeat for the `clean_sft_grpo_v2` config.
- The `docker-wait` background-watch wake notification on this host has been
  unreliable for long (>20min) containers even though the underlying job
  completes cleanly — this is a notification-plumbing issue, not a stalled
  GPU. **Always `docker inspect <name> --format '{{.State.Status}} exit=... started=... finished=...'`
  explicitly at the start of every turn**, regardless of whether a wake
  arrived, before deciding a container is still running.
- A non-GPU container `cc-test-pg` (postgres:17-alpine) has been running from
  elsewhere in the session throughout; it is not part of this chain and does
  not use the GPU.
- Merge output-path naming convention (not auto-derived by any handler,
  verified by hand against seed-1 session-note precedent): `<run_path>/Qwen3-4B-clean-sft-<stage>/merged-16bit`
  for DPO/KTO merges, `<run_path>/Qwen3-4B-bnb-4bit/merged-16bit` for the
  stage-1 (foundation) merge.
- Full-eval configs for DPO/KTO arms load the merged **clean-SFT base**, not
  the merged-DPO/merged-KTO checkpoint, with the DPO/KTO LoRA as
  `arms[].adapter` — the merged-DPO/merged-KTO checkpoints built this session
  exist solely as GRPO-stage (stage-3) training sources, never as their own
  eval target.

Ran `scripts/ops/prune_runtime.sh stage` after the KTO full eval (3 containers
removed, 516.2MB reclaimed). `docker ps -a` clean of this chain's containers
at handoff (one unrelated `cc-test-pg` still running).

### 2026-08-03 — KTO full eval COMPLETE (lead-verified); queue item 3 done, HOLDING

`eh-grpo3seed-2-clean_sft_kto-full_eval-20260803T153224Z` exited 0 at
16:00:50Z (started 15:32:31Z, ~28m); re-confirmed via `docker inspect`
independently before recording. Lead-verified numbers, not re-derived:

Results at
`archive/experiment/phase1/eval/results_grpo3seed_response_confidence_selfaware_clean_sft_kto_seed2_full_4b/clean_schema_sft_kto_seed2__selfaware/`
(re-confirmed present: `metrics.json` 1.4K, `scored_rows.jsonl` 2.6M,
`bootstrap_ci.json` 227B). n=3369, `refusal_recall_pct` 85.66,
`answer_on_unknown_pct` 14.34, `over_refusal_pct` 54.00, `truthful_pct` 40.31.

Queue item 3 (full evals: stage-1 base, DPO, KTO) is complete. Ran
`scripts/ops/prune_runtime.sh stage` (3 containers removed, 516.2MB
reclaimed). Per lead instruction: finalizing this NOTEBOOK draft as a
self-contained handoff (see the entry above), then reporting draft-final to
the lead, then **HOLDING completely — no launches of any kind** — for the
user's WSL disk-compaction maintenance window. This harness will be
terminated by that window and will not be resumed; a successor picks up
queue item 4 (`clean_sft_grpo_v2` launch) after the lead releases it.

### 2026-08-03 — DPO full eval COMPLETE (lead-verified); KTO full eval LAUNCHED

`eh-grpo3seed-2-clean_sft_dpo-full_eval-20260803T150428Z` exited 0 at
15:31:31Z (started 15:04:36Z, ~27m); re-confirmed via `docker inspect`
independently before recording. Lead-verified numbers, not re-derived:

Results at
`archive/experiment/phase1/eval/results_grpo3seed_response_confidence_selfaware_clean_sft_dpo_seed2_full_4b/clean_schema_sft_dpo_seed2__selfaware/`
(re-confirmed present: `metrics.json` 1.4K, `scored_rows.jsonl` 2.6M,
`bootstrap_ci.json` 227B). n=3369, `refusal_recall_pct` 89.34,
`answer_on_unknown_pct` 10.66, `over_refusal_pct` 55.97, `truthful_pct` 41.32.

Launched KTO full eval immediately per lead instruction:
`eh-grpo3seed-2-clean_sft_kto-full_eval-20260803T153224Z`, started
~15:32:24Z, config
`experiments/grpo-three-seed-confirmatory/configs/eval_grpo3seed_response_confidence_selfaware_clean_sft_kto_seed2_full_local_4b.yaml`.
Preflight: digest matched, disk 233G free, GPU idle. After this completes and
is verified: report + HOLD, no `clean_sft_grpo_v2` launch, pending the user's
WSL disk-compaction maintenance window (`wsl --shutdown` will kill everything
running).

### 2026-08-03 — Stage-1 base full eval COMPLETE (G1 denominator, lead-verified); DPO full eval LAUNCHED

`eh-grpo3seed-2-clean_sft-full_eval-20260803T133950Z` exited 0 at 14:02:05Z
(started 13:40:00Z, ~22m). This harness's own `docker wait` background watch
was slow to wake (known host issue, not a stall — GPU was not stuck, the
notification mechanism itself lagged); the lead's independent watch caught
completion and verified results directly, so the numbers below are
lead-verified, not re-derived by this harness:

Results at
`archive/experiment/phase1/eval/results_grpo3seed_response_confidence_selfaware_clean_sft_seed2_merged_full_4b/clean_schema_sft_merged_seed2__selfaware/`
(re-confirmed present on disk by this harness: `metrics.json` 1.4K,
`scored_rows.jsonl` 2.7M, `bootstrap_ci.json` 230B). n=3369.
**G1 same-seed denominator (seed 2):** `refusal_recall_pct` 89.92,
`answer_on_unknown_pct` 10.08, `over_refusal_pct` 58.24, `truthful_pct` 41.17.

Standing host note: the docker-wait wake mechanism on this host is
unreliable for long containers even when GPU work itself completes cleanly.
Going forward: always `docker inspect` the container explicitly at the start
of the next turn regardless of whether a wake notification arrived, per lead
instruction.

Launched DPO full eval immediately per lead instruction (revised queue order:
DPO full eval -> KTO full eval -> report + HOLD before grpo_v2, because a user
WSL disk-compaction maintenance window (`wsl --shutdown`) is coming at that
boundary and nothing may be in flight when it starts).

### 2026-08-03 — Queue item 3 (full evals) LAUNCHED: stage-1 base first

Both stage-2 G0 bounded smokes passed (entries below). Built three full
3,369-row eval configs, cloned from the seed-1 precedents found via
`bin/search` (KG-search-first, per project rule) rather than guessed:

- Stage-1 base: `experiments/grpo-three-seed-confirmatory/configs/eval_grpo3seed_response_confidence_selfaware_clean_sft_seed2_merged_full_local_4b.yaml`,
  cloned from
  `archive/experiment/phase1/eval/config/eval_amendment_e_response_confidence_selfaware_clean_sft_seed1_merged_full_local_4b.yaml`.
- DPO: `experiments/grpo-three-seed-confirmatory/configs/eval_grpo3seed_response_confidence_selfaware_clean_sft_dpo_seed2_full_local_4b.yaml`,
  cloned from
  `archive/experiment/phase1/eval/config/eval_amendment_e_response_confidence_selfaware_clean_sft_dpo_seed1_corrected_base_full_local_4b.yaml`.
- KTO: `experiments/grpo-three-seed-confirmatory/configs/eval_grpo3seed_response_confidence_selfaware_clean_sft_kto_seed2_full_local_4b.yaml`,
  cloned from
  `archive/experiment/phase1/eval/config/eval_amendment_e_response_confidence_selfaware_clean_sft_kto_seed1_corrected_base_full_local_4b.yaml`.

Important lineage detail carried from the seed-1 precedent (not invented):
the DPO/KTO full-eval configs load the merged CLEAN-SFT base
(`sft_schema_clean_seed2_full/20260731_232307/.../merged-16bit`) with the
DPO/KTO LoRA as `arms[].adapter` — they do NOT evaluate the merged-DPO/
merged-KTO checkpoints built in the two entries above. Those merges exist
solely as GRPO-stage (queue item 4/stage-3) training sources. All three
configs written to worktree + canonical, no offset/limit override (full
3,369-row file per cell.yaml `eval_population: selfaware-full-3369`).

Preflight: digest match, `df -h /` 233G free, GPU idle. One unrelated non-GPU
container (`cc-test-pg`, postgres) running from elsewhere in the session —
not mine, no GPU use, no interference.

**Launched (LONG container, lead notified immediately per contract):**
`eh-grpo3seed-2-clean_sft-full_eval-20260803T133950Z`, started ~13:39:50Z,
stage-1 base config above. Expected ~41min per seed-1 precedent (E note
`:1613->:1648`). Background `docker wait` watch set; lead holds an
independent watch.

### 2026-08-03 — Seed-2 clean_sft_kto merge REDONE, bounded smoke G0 PASS

**Merge.** Container `eh-grpo3seed-2-clean_sft_kto-merge-20260803T133138Z`,
started 13:31:45Z, finished 13:34:23Z (2m38s), exit 0. Same merge mechanism as
DPO above, naming convention confirmed against seed-1 precedent
(`docs/sessions/20260624T183052Z-grpo-centered-stacking-plan.md:224`). Output
at
`scratch/schema_response_confidence/runs/schema_clean_sft_kto_seed2_full/20260801_213332/Qwen3-4B-clean-sft-kto/merged-16bit/`:
`config.json` present, 2 safetensors shards (4737.1M + 2935.2M = 7.6G total).
Disk 240G -> 233G free.

**Bounded smoke.** Config
`experiments/grpo-three-seed-confirmatory/configs/eval_grpo3seed_response_confidence_selfaware_clean_sft_kto_seed2_merged_smoke_local_4b.yaml`,
cloned from the seed-1 KTO-merged sanity config
(`archive/experiment/phase1/eval/config/eval_amendment_f_response_confidence_selfaware_clean_sft_kto_merged_seed1_sanity_local_4b.yaml`),
offset 2240 / limit 192 unchanged, written to worktree + canonical. Container
`eh-grpo3seed-2-clean_sft_kto-smoke-20260803T133456Z`, started 13:35:02Z,
finished 13:37:31Z (2m29s), exit 0, 0 errors / 1 benign NCCL-teardown warning.
Results:
`archive/experiment/phase1/eval/results_grpo3seed_response_confidence_selfaware_clean_sft_kto_seed2_merged_smoke_4b/`.

Verified numbers (n=192, 97 known / 95 unknown): 192/192 coverage
(`n_with_confidence` 192, `n_missing_confidence` 0), `enable_thinking`
uniformly `False`, thinking-tag-substring hits = 0,
`stated_confidence_retry_exhausted` count 0. Behavioral: `refusal_recall_pct`
86.32, `answer_on_unknown_pct` 13.68, `over_refusal_pct` 62.89, `truthful_pct`
50.52, `mean_stated_confidence` 0.8240, `brier_vs_response_appropriateness`
0.3510.

G0 `bounded_smoke_coverage`: PASS for both stage-2 arms now (lead-adjudicated).
Ran `scripts/ops/prune_runtime.sh stage` (2 containers removed, 322MB).
Proceeding to queue item 3: full 3,369-row evals (stage-1 base, clean_sft_dpo,
clean_sft_kto).

### 2026-08-03 — GO signal received; seed-2 clean_sft_dpo merge REDONE, bounded smoke G0 PASS

Lead verified the nvidia Docker runtime restored (user restarted Docker
Desktop; fresh backend re-pulled the pinned image by digest and retagged it;
lead confirmed `docker run --rm --gpus all --entrypoint nvidia-smi
unsloth/unsloth:latest` sees the RTX 3090). Note for future recovery: the
image store did not survive the Docker Desktop restart, so an "Unable to find
image" mid-chain recovers via pull-by-digest + retag, never trust `:latest`
from the registry alone.

Preflight re-confirmed independently before launch: digest
`sha256:f21629b9ae4ed11231768edfaed0f40d41d85d6ea9a71e8096a3d96ea0311772`
matches; `nvidia-smi` idle 0MiB/24576MiB; `df -h /` 248G free; `docker ps -a`
0 running.

**Merge.** Container `eh-grpo3seed-2-clean_sft_dpo-merge-20260803T132341Z`,
started 13:23:50Z, finished 13:25:38Z (1m48s), exit 0. Same
`merge_lora_checkpoint(lora_path=.../final_model, output_path=.../Qwen3-4B-clean-sft-dpo/merged-16bit,
max_seq_length=2048, load_in_4bit=True)` mechanism as stage 1, run inside the
pinned container (`--user root --gpus all --ipc=host --entrypoint python3`,
`PYTHONPATH=/workspace/repo/synaptic-tuner`). Output-path naming convention
(`Qwen3-4B-clean-sft-dpo/merged-16bit`) confirmed against the seed-1 precedent
(`docs/sessions/20260624T183052Z-grpo-centered-stacking-plan.md:104`), not
guessed. Output at
`scratch/schema_response_confidence/runs/schema_clean_sft_dpo_seed2_full/20260801_183028/Qwen3-4B-clean-sft-dpo/merged-16bit/`:
`config.json` present, 2 safetensors shards (4737.1M + 2935.2M = 7.6G total).
Disk 248G -> 240G free (~8G, matches budget estimate). One benign Triton
kernel import warning in logs, non-fatal.

**Bounded smoke (G0 `bounded_smoke_coverage`).** Config
`experiments/grpo-three-seed-confirmatory/configs/eval_grpo3seed_response_confidence_selfaware_clean_sft_dpo_seed2_merged_smoke_local_4b.yaml`,
cloned from the seed-1 DPO-merged sanity config
(`archive/experiment/phase1/eval/config/eval_amendment_f_response_confidence_selfaware_clean_sft_dpo_merged_seed1_sanity_local_4b.yaml`)
with only `model_tag`/`model_name`/`results_dir`/`arms` changed; offset 2240 /
limit 192 unchanged. Written to both the worktree and canonical (bind-mount
root). Container `eh-grpo3seed-2-clean_sft_dpo-smoke-20260803T132727Z`, started
13:27:35Z, finished 13:30:01Z (2m26s), exit 0, 0 errors / 1 benign NCCL-teardown
warning. Results:
`archive/experiment/phase1/eval/results_grpo3seed_response_confidence_selfaware_clean_sft_dpo_seed2_merged_smoke_4b/`.

Verified numbers (n=192, 97 known / 95 unknown): 192/192 rows scored, 192/192
coverage (`n_with_confidence` 192, `n_missing_confidence` 0), `enable_thinking`
uniformly `False`, thinking-tag-substring hits in `generated_answer` = 0 (field
counted directly, no content read/copied per data containment),
`stated_confidence_retry_exhausted` count 0. Behavioral: `refusal_recall_pct`
88.42, `answer_on_unknown_pct` 11.58, `over_refusal_pct` 63.92, `truthful_pct`
50.52, `mean_stated_confidence` 0.7838, `brier_vs_response_appropriateness`
0.3192.

G0 `bounded_smoke_coverage`: PASS (lead-adjudicated, numbers above). G0
`merge_first_lineage` and `training_completed_clean`: PASS (re-verified from
`training_lineage.json` before the merge — see prior entry). Ran
`scripts/ops/prune_runtime.sh stage` after this boundary (2 stopped containers
removed, 322MB reclaimed). Proceeding to queue item 2: KTO merge redo + bounded
smoke.

### 2026-08-03 — Fourth executor: state re-verification, image-tag fix, nvidia Docker runtime blocker (HOLD, lead-confirmed)

Fourth execution harness takeover. Read AMENDMENT.md, cell.yaml, gates.yaml,
NOTEBOOK.md, and the clean-mainline runbook per dispatch before touching
anything. Zero GPU compute burned this entry.

**Re-verified from artifacts (not trusting predecessor record):**
- `clean_sft_dpo` seed-2 `final_model/` intact:
  `adapter_model.safetensors` 252.1M; `training_lineage.json` confirms
  `base_model` = seed-2 merged source
  (`.../sft_schema_clean_seed2_full/20260731_232307/Qwen3-4B-bnb-4bit/merged-16bit`,
  satisfying G0 `merge_first_lineage`), batch_size 2 / grad_accum 4 / lr 5e-6 /
  beta 0.1 / seed 2, final_step 1868, final_loss 0.0462, training_time 4947.2s
  (1h22m27s), `runtime.status: completed`.
- `clean_sft_kto` seed-2 `final_model/` intact: `adapter_model.safetensors`
  252.1M; lineage confirms same merged source, batch_size 12 / grad_accum 1 /
  lr 1e-6 / beta 0.1 / seed 2, final_step 2491, final_loss 0.0877,
  training_time 6036.9s (1h40m37s), `runtime.status: completed`. Capacity note:
  `peak_gpu_memory_reserved_pct` 95.92% (23.02GB/24GB), `oom_risk_level: high`
  logged, min headroom 0.98GB — tighter than seed-1's 89.22% at the same
  batch-12 config, but completed with no OOM and no fallback to batch 8 was
  needed.
- Stage-1 merged source
  (`.../sft_schema_clean_seed2_full/20260731_232307/Qwen3-4B-bnb-4bit/merged-16bit/`):
  intact, `config.json` present, 2 safetensors shards, 7.6G total.
- No leftover truncated DPO merge directory — confirms the crash-truncated
  merge was deleted as the entry below states.
- `df -h /`: 248G free / 1007G (above the 50G precheck floor). `nvidia-smi`:
  idle, 0MiB/24576MiB. `docker ps -a`: 0 running before this entry.
- Environment note: all scratch/config artifacts for this chain live under the
  CANONICAL checkout (`/home/profsynapse/code/Epistemic-Humility-Research/scratch/schema_response_confidence/`),
  not the worktree — confirmed via `training_lineage.json` `run_directory`
  fields resolving to canonical, and the worktree has no `scratch/` at all
  (fresh, as AMENDMENT.md predicts). Continuing to bind-mount Docker at
  canonical for GPU work (matches all existing artifact paths, avoids copying
  8GB+ near a disk that just overflowed); NOTEBOOK drafting stays confined to
  the worktree, uncommitted, per this harness's contract. Lead-confirmed
  correct.

**Image-tag fix (lead-endorsed):** first merge launch attempt failed —
`unsloth/unsloth:latest` had lost its tag pointer, present only by digest/
IMAGE ID `f21629b9ae4e` (`docker images --digests` showed `<none>` for TAG).
Digest re-verified byte-identical to the pinned reference
(`.skills/experiment-runner/reference/local-runtime.md:82-86`):
`sha256:f21629b9ae4ed11231768edfaed0f40d41d85d6ea9a71e8096a3d96ea0311772`.
Retagged the existing image (`docker tag f21629b9ae4e unsloth/unsloth:latest`)
rather than re-pulling 41.7GB; digest confirmed unchanged after retag.

**BLOCKER — HOLD, per lead instruction 2026-08-03:** second merge launch
attempt failed at container-create with `could not select device driver ""
with capabilities: [[gpu]]`. `docker info` shows `Runtimes: io.containerd.runc.v2
runc` — no `nvidia` runtime registered. `nvidia-ctk` binary absent, no
`nvidia-container-toolkit` in `dpkg -l`, no `/etc/docker/daemon.json`.
`docker.service` shows `dockerd` restarted 2026-08-02 09:14:18 EDT (inside the
crash-cleanup window below) and the image was re-pulled at 13:11:18 that same
day — the daemon came up fresh post-crash without the nvidia container
runtime ever being re-registered. Host `nvidia-smi` still works fine (driver/
GPU healthy); this is purely the Docker-level GPU integration. Zero GPU compute
burned — the container never started (exit 128 at driver-select, not a
training step).

Escalated to the lead rather than installing `nvidia-container-toolkit` and
restarting the Docker daemon myself: that is a host-wide change (affects any
container on the box) and needs the user's sudo. Lead confirmed: tag-restore
endorsed; disk-surveyor (another active agent this session) is idle and not
working this; the nvidia-runtime loss is crash fallout from the same window
recorded below; do not install packages or restart the daemon — escalated to
the user. **HOLDING** until the lead sends a go signal after the runtime is
restored and GPU visibility is verified inside the pinned container, then
resume the queue from item 1 (DPO merge redo).

### 2026-08-03 — Disk-full crash, runtime restore, and wall-clock guardrail re-baseline (LEAD RULING, user-approved)

The root volume hit 100% on 2026-08-02 while the third execution harness was
merging the seed-2 clean_sft_dpo checkpoint. Consequences, all now remediated:

- The in-progress merge output was truncated (shard 2 short by ~555MB against
  the reference shard size) and has been deleted; the merge will be redone
  from the intact `final_model/` adapter. Training artifacts for both stage-2
  arms (adapters, lineage, logs, checkpoints) were verified intact.
- The crash cleanup removed ALL docker containers and the pinned
  `unsloth/unsloth` training image. The image was re-pulled BY DIGEST and
  verified: `sha256:f21629b9ae4ed11231768edfaed0f40d41d85d6ea9a71e8096a3d96ea0311772`,
  restoring the exact registered runtime. Container history (docker inspect
  provenance for completed containers) is lost; the NOTEBOOK entries above and
  on-disk lineage files remain the record.
- ~162G reclaimed in a lead-supervised cleanup (registry-verified regenerable
  merges and re-downloadable caches only; no chain artifacts, eval results, or
  probe data touched). A standing storage-hygiene policy and prune script
  landed as PR #386, including a free-space precheck before any merge or
  training launch.

GUARDRAIL RE-BASELINE (ruled by lead, approved by user 2026-08-03): the
registered seed-2 pause threshold of 42h was written against wall-clock. Actual
GPU compute through stage 2 training is ~3.5h; the overrun is entirely harness
stalls (two executor wake failures, ~18h idle) plus the crash outage, not
runaway compute. The threshold's intent was to catch runaway compute, so the
budget is re-baselined to GPU-COMPUTE-HOURS with the SAME ceilings: pause if
seed-2 compute exceeds 42h or total chain compute exceeds 83h. Wall-clock is
no longer a pause trigger; stall time is tracked and reported but does not
count against the budget. Ruled before any further results are seen; no
outcome gate (G0/G1/G2) is affected.

### 2026-08-01 — Seed-2 clean_sft_dpo (stage 2) LAUNCHED

Container `eh-grpo3seed-2-clean_sft_dpo-20260801T183028Z`, launched 18:30:28Z,
pinned digest re-verified before launch. Lead re-derived the launch args from
`docker inspect` of the running container: `--model-name` points at the seed-2
MERGED checkpoint
(`.../sft_schema_clean_seed2_full/20260731_232307/Qwen3-4B-bnb-4bit/merged-16bit`,
satisfying G0 `merge_first_lineage`), `--beta 0.1`, `--seed 2`,
`--learning-rate 5e-6`, batch 2 / grad-accum 4, LoRA r32/a64/d0.05, 1 epoch,
training file the frozen `dpo_response_confidence_train.jsonl` (14,943 rows,
matches the frozen G0 audit constant). Output root
`scratch/schema_response_confidence/runs/schema_clean_sft_dpo_seed2_full`,
run-timestamp `20260801_183028`. Note carried from seed-1 precedent: the
DPO/KTO trainers expose no `--lora-random-state` flag, so LoRA init uses the
trainer baseline (3407) for these stages; the seed-mirroring ruling applies
only where a config file carries `lora.random_state` (SFT/GRPO). Seed-1
behaved identically, so this is not a new degree of freedom.

### 2026-08-01 — Seed-2 clean_sft (stage 1) COMPLETE: train + merge + bounded smoke, G0 PASS

Closes out stage 1 for seed 2. Two watch-discipline stalls occurred during
this stage (recorded honestly, no GPU time lost either time — both times the
GPU sat idle 0MiB/0% while this harness was mid-turn or between turns, not
stuck mid-job): the predecessor harness wedged after training finished
(recovered at takeover, entry above), and this harness itself then let a
completed `docker wait` go unactioned for roughly 8 hours after the merge
step before the lead's status check prompted resumption. New standing rule
adopted going forward: check `docker inspect` on every watched container
before ending any turn, and act immediately if it has already exited rather
than waiting on the wake notification.

**Merge.** Container `eh-grpo3seed-2-clean_sft-merge-20260801T091239Z`
(launched 09:12:39Z, exited 0 at 09:14:07Z), pinned digest re-verified before
launch (`sha256:f21629b9ae4ed11231768edfaed0f40d41d85d6ea9a71e8096a3d96ea0311772`).
Ran `shared.model_loading.merge.merge_lora_checkpoint(lora_path=.../final_model,
output_path=.../Qwen3-4B-bnb-4bit/merged-16bit, max_seq_length=2048,
load_in_4bit=True)` inside the container (mechanism and output-path
convention reconstructed from `synaptic-tuner/shared/model_loading/merge.py`
and `tuner/handlers/merge_handler.py:169`, since no standalone scriptable
merge CLI exists — `MergeHandler` is interactive-menu-only). Log confirms
`Unsloth: Merge process complete.` Output at
`scratch/schema_response_confidence/runs/sft_schema_clean_seed2_full/20260731_232307/Qwen3-4B-bnb-4bit/merged-16bit/`:
`config.json` present (valid merged model, not an adapter), 2 safetensors
shards, 7.6G total — same shard-count/size pattern as the seed-1 merge.

**Bounded smoke (G0 `bounded_smoke_coverage`).** Config
`experiments/grpo-three-seed-confirmatory/configs/eval_grpo3seed_response_confidence_selfaware_clean_sft_seed2_merged_smoke_local_4b.yaml`,
cloned from the seed-1 merged-smoke config
(`archive/experiment/phase1/eval/config/eval_amendment_e_response_confidence_selfaware_clean_sft_seed1_merged_smoke_local_4b.yaml`)
with only `model_tag`/`model_name`/`results_dir` changed to the seed-2 merged
path; `offset: 2240` / `limit: 192` (selfaware-mixed-192 per cell.yaml) and
all prompt/generation/vllm settings carried unchanged. Container
`eh-grpo3seed-2-clean_sft-smoke-20260801T103120Z`, digest re-verified
immediately before launch (same pinned digest as above), `--live-vllm`,
exited 0 at 10:33:47Z. Results:
`archive/experiment/phase1/eval/results_grpo3seed_response_confidence_selfaware_clean_sft_seed2_merged_smoke_4b/`.

Lead-verified numbers (n=192, 97 known / 95 unknown): 192/192 rows scored,
192/192 `generated_answer` + `stated_confidence` coverage, 0 retry-exhausted,
0 thinking-tag hits, `enable_thinking` uniformly false.
`refusal_recall_pct` 89.47, `answer_on_unknown_pct` 10.53, `over_refusal_pct`
68.04, `refusal_rate_pct` 78.65, `correct_on_known_pct` 45.16, `truthful_pct`
51.56.

G0 `bounded_smoke_coverage`: PASS (lead-adjudicated). G0
`training_completed_clean` and `merge_first_lineage`: PASS (verified above and
in the takeover entry). Stage 1 for seed 2 is complete; proceeding to stage 2,
`clean_sft_dpo`, sourced from this merged checkpoint per `merge_first_lineage`.

### 2026-08-01 — TAKEOVER: predecessor harness stalled after seed-2 clean_sft training completed; verified and resumed at merge step

The prior execution harness wedged sometime after the seed-2 `clean_sft`
training container reached a clean exit and was terminated by the lead; this
harness resumes the chain from recorded state, per dispatch. No G0 implication
from the stall itself — it is a harness/watch-loop failure, not an instrument
or data problem, and it burned zero extra GPU time (verified below).

Re-verified from artifacts rather than trusting the predecessor's own record:
- `docker inspect eh-grpo3seed-2-clean_sft-20260731T232235Z` ->
  `Status: exited, ExitCode: 0`, `StartedAt: 2026-07-31T23:22:35Z`,
  `FinishedAt: 2026-07-31T23:49:14Z` (26m39s wall, consistent with the
  `training_lineage.json` `training_time_seconds: 1526.8`).
- Run dir
  `scratch/schema_response_confidence/runs/sft_schema_clean_seed2_full/20260731_232307/`
  contains `final_model/adapter_model.safetensors` (252.1M),
  `final_model/adapter_config.json`, `training_lineage.json` (`stage:
  training`, `runtime.status: completed`, `final_step: 1495`, `final_loss:
  0.4281`), and `capacity_features.json`. G0 `training_completed_clean`: PASS.
- `nvidia-smi`: RTX 3090, 0MiB/24576MiB, 0% util, idle at takeover time
  (2026-08-01T09:12Z) — GPU was sitting idle the whole stall, not stuck
  mid-job. Zero GPU time lost to the stall itself.
- `docker images --digests unsloth/unsloth` ->
  `sha256:f21629b9ae4ed11231768edfaed0f40d41d85d6ea9a71e8096a3d96ea0311772`,
  still exact match to the pinned digest.

Wall-clock accounting against the signed budget guardrails (seed-2 block
~42h from the 2026-07-31T23:22Z launch, ~83h total): stage-1 train+merge+smoke
for seed 1 measured 2.4h. From launch (23:22Z) to takeover (09:12Z) is ~9h50m
elapsed, of which only ~27m was GPU training time — the remaining ~9h23m
(23:49Z training-end to 09:12Z takeover) is dead stall time with the GPU idle,
not additional work. Recorded honestly against budget rather than absorbed
silently; still well inside the ~42h seed-2 guardrail even counting the full
stall.

Resumed at the next un-done step per `launch_order`: merge. No merge script
exists as a standalone CLI (`tuner/handlers/merge_handler.py`'s `MergeHandler`
is interactive-menu-only, not scriptable headless); confirmed the seed-1
mechanism instead via `synaptic-tuner/shared/model_loading/merge.py`
(`merge_lora_checkpoint(lora_path, output_path, max_seq_length=2048,
load_in_4bit=True)`, family defaults to `causal_lm`) and the output-path
convention from `merge_handler.py:169` (`run_path / get_base_model_name(lora_path)
/ "merged-16bit"`), which matches the seed-1 artifact path exactly
(`.../sft_schema_clean_seed1_full/20260623_123624/Qwen3-4B-bnb-4bit/merged-16bit`).

Launched: container `eh-grpo3seed-2-clean_sft-merge-20260801T091239Z`, pinned
image digest re-verified before launch
(`sha256:f21629b9ae4ed11231768edfaed0f40d41d85d6ea9a71e8096a3d96ea0311772`),
`--user root --gpus all --ipc=host --entrypoint python3`, `PYTHONPATH=
/workspace/repo/synaptic-tuner` (mirrors how `train_sft.py` inserts
`synaptic-tuner/` onto `sys.path` at import time), running:

```python
from pathlib import Path
from shared.model_loading.merge import merge_lora_checkpoint
lora_path = Path("scratch/schema_response_confidence/runs/sft_schema_clean_seed2_full/20260731_232307/final_model")
output_path = Path("scratch/schema_response_confidence/runs/sft_schema_clean_seed2_full/20260731_232307/Qwen3-4B-bnb-4bit/merged-16bit")
merge_lora_checkpoint(lora_path, output_path, max_seq_length=2048, load_in_4bit=True)
```

`docker wait` running in background; will record merge result, then launch the
192-row bounded smoke (G0 `bounded_smoke_coverage`) before the stage-1 entry
is considered complete.

### 2026-07-31 — Seed-2 clean_sft (stage 1) LAUNCHED, after a launch-mechanism fix

Preflights re-confirmed after the lead's ruling: `git pull` in this worktree
showed the ruling commit already local (worktree and lead share the same local
repo; the ruling reached me via the local branch, not a remote fetch —
confirmed `d49bc6b2` present, no conflicts with my hard-stop entry above it).
`nvidia-smi` re-checked idle (0MiB/24576MiB, 0% util) immediately before
launch.

Built
`experiments/grpo-three-seed-confirmatory/configs/sft_schema_clean_response_confidence_seed2_full.yaml`,
a seed-2 clone of the archived
`sft_schema_clean_response_confidence_seed1_full.yaml`, all values unchanged
except `seed: 2` and `lora.random_state: 2` (lead ruling). Launched via
`docker run -d --user root --gpus all --ipc=host --entrypoint python3
... unsloth/unsloth:latest synaptic-tuner/Trainers/sft/train_sft.py --config
<that yaml> --no-dashboard --quiet`. Container
`eh-grpo3seed-2-clean_sft-20260731T231802Z` exited 1 immediately:
`AttributeError: 'NoneType' object has no attribute 'loader'` in
`train_sft.py:590-597` — `importlib.util.spec_from_file_location` cannot build
a loader for a non-Python file, because `--config` in `train_sft.py` has
**always** meant "import this file as a Python module and call `Config()`",
never a YAML loader. Confirmed via `git log -p` on `train_sft.py`: this
`spec_from_file_location(...)` branch is unchanged across the file's entire
history. The `.yaml` file I built from carries a header comment claiming
"Auto-converted ... for config-format uniformity (YAML, like the GRPO
trainer) ... Verified to load byte-identically ... Consumed by: train_sft.py
--config <this>.yaml" — that claim does not hold against the current trainer
code.

Cross-checked the REAL seed-1 invocation against the actual session notes
(`docs/sessions/20260623T093654Z-probe-scaled-response-confidence-retrain.md:500-504`),
not the archived runbook (which is itself headed "Status: prepared, not
launched" — a template, not a verified record). The real seed-1 launch used
`--config archive/experiment/phase1/grpo/configs/
sft_schema_clean_response_confidence_seed1_full_config.py` — a `.py` file.
That file no longer exists on disk: `git log --all --full-history
--diff-filter=A` traced it to commit `aa11b49e` ("Amendment J: GRPO-v3
proper-scoring confidence reward", an unrelated PR), which batch-deleted the
working `_config.py` files across this entire SFT-config family and replaced
them with the untested `.yaml` "auto-converted" versions in the same commit.
This is a repo-wide gap: every schema-response-confidence SFT `.yaml` config
under `archive/experiment/phase1/grpo/configs/` is currently unusable via
train_sft.py's `--config` flag, not just this one.

Fix: restored the exact original file via `git show
aa11b49e^:experiment/phase1/grpo/configs/
sft_schema_clean_response_confidence_seed1_full_config.py`. Diffed its values
against my `.yaml` attempt field-by-field — identical (model_name, dataset
path, batch_size 10 / grad_accum 1, learning_rate 2e-4, lora r=32/alpha=64/
dropout=0.05, num_epochs 1, chat_template_kwargs enable_thinking=false, etc.),
confirming the earlier `.yaml` conversion was faithful in content, only broken
in format/loading mechanism. Wrote
`experiments/grpo-three-seed-confirmatory/configs/sft_schema_clean_response_confidence_seed2_full_config.py`
as a `Config()` Python module, identical to the restored seed-1 file except
`training.output_dir` -> `.../sft_schema_clean_seed2_full`, `lora.random_state:
2`, `seed: 2`. No cell.yaml/gates.yaml pinned value touched; no hyperparameter
changed; only the config-delivery file format was fixed to match what
train_sft.py's `--config` flag has always actually required.

Relaunched: container `eh-grpo3seed-2-clean_sft-20260731T232235Z`, image digest
`sha256:f21629b9ae4ed11231768edfaed0f40d41d85d6ea9a71e8096a3d96ea0311772`
(re-verified before launch). Confirmed via logs: config loaded, run directory
`scratch/schema_response_confidence/runs/sft_schema_clean_seed2_full/20260731_232307`
created, model loading started (Unsloth 2026.5.9, Qwen3-4B-bnb-4bit, RTX 3090,
bf16, 4-bit). Training in progress at time of writing; `docker wait` running in
background. Seed-1 measured wall-clock for this stage (train+merge+smoke) was
2.4h (E note :488->:535); will record actual duration and artifact path/size
when it completes.

Elapsed against budget guardrails: essentially zero training time burned
before this entry (the two failed-fast attempts cost seconds, not compute).

### 2026-07-31 — LEAD RULING: lora.random_state mirrors the seed number; chain unblocked

Adjudication of the hard stop below. Ruling made BEFORE any outcome data
exists, on instrument-construction grounds only; nothing signed pins
`lora.random_state` (cell.yaml's `lora:` block fixes only r/alpha/dropout), so
this is protocol interpretation, not a gate change.

Ruling: seed-2 configs set `lora.random_state: 2` and seed-3 configs set
`lora.random_state: 3`, mirroring `seed:`. Rationale: (1) every seed-1 config
deviates from the tuner template default (3407) to `random_state: 1 == seed`,
so the convention carried from seed-1 evidence is "random_state mirrors the
seed", not the literal value 1; (2) the amendment's purpose is a full per-seed
lineage replicate — freezing LoRA init across seeds would test only data-order
robustness and weaken what a G1 replication (or failure) means; (3) the
alternative readings (literal 1, or template 3407) would make seed-1 itself
inconsistent with the convention chosen. The executor records the actual
`seed`/`lora.random_state` pair per config in its per-stage entries so the
choice is auditable.

Also ruled on the staleness flag below: AMENDMENT.md's banner and predictions
scoreboard are corrected in this branch to reflect the signed state recorded in
experiment.yaml (bookkeeping only; no design content changed). gates.yaml is
left byte-identical because it is sha256-pinned at sign; its `status: proposed`
header comments are superseded by experiment.yaml's `status: signed`, which is
authoritative.

### 2026-07-31 — HARD STOP before first launch: lora.random_state seed-threading ambiguity

Execution harness dispatched to run the registered seed-2/seed-3 chain. Read, in
order: AMENDMENT.md, cell.yaml, gates.yaml,
archive/experiment/phase1/grpo/amendment_e_clean_mainline_runbook.md.

Documentation-staleness note (not a blocker, flagged for the lead to fix):
AMENDMENT.md's top banner still reads "Status: DRAFT — NOT SIGNED. Do not
launch," its bottom "Predictions scoreboard" table still shows both PI/
orchestrator rows as empty placeholders, and gates.yaml's own header fields
read `status: proposed` / `adjudicated_by: null` / `adjudicated_date: null`.
Cross-checked against experiment.yaml (status: signed, registered: true, real
non-empty prediction/falsifier text, instrument.pins.cell.yaml =
c3026109d42c8fe13755b30466d7f482885d56c50de6836e92558fdb4070a864,
instrument.pins.gates.yaml =
7c79a41894a1fc64df01f07bbb197f8c25239d8625e3d9f3d8bbc97d3e51c0fa — both
verified byte-identical via sha256sum against the current cell.yaml/gates.yaml
in both the main checkout and this worktree), experiments/registry.json (same
signed state), git log (`65accc43 GRPO three-seed confirmatory: SIGNED
(2026-07-31, user approval in session)`), and the merged
`gh pr view 379` (title "GRPO three-seed confirmatory: signed amendment",
MERGED). All five agree the block is genuinely signed; only the two prose
banners and the gates.yaml header comments were never rewritten by the sign
tooling.

Preflight results (all pass):
- `docker info` Server block: nvidia runtime registered (`Runtimes: nvidia runc
  io.containerd.runc.v2`), Server Version 29.3.1, reachable via
  DOCKER_HOST=unix:///var/run/docker.sock.
- `docker images --digests unsloth/unsloth` ->
  sha256:f21629b9ae4ed11231768edfaed0f40d41d85d6ea9a71e8096a3d96ea0311772,
  exact match to the pinned digest.
- `nvidia-smi`: RTX 3090, 0MiB/24576MiB used, 0% util, no running processes —
  GPU idle.
- G0 dataset audit (re-run myself, not reused from the dispatch claim):
  sft_response_confidence_train_clean.jsonl = 14943 rows; source_label counts
  known=7981, unknown=6414, discard(ambiguous)=548; unique response_confidence
  targets=2489; range [0.3508, 0.9]. dpo_response_confidence_train.jsonl =
  14943 lines. kto_response_confidence_train.jsonl = 29886 lines.
  grpo_train.jsonl = 14888 lines, grpo_dev.jsonl = 1655 lines (per
  grpo_manifest.json and wc -l). All match cell.yaml `frozen_audit` and
  AMENDMENT.md "Datasets" exactly. G0 dataset-audit check: PASS.
- No existing scratch/schema_response_confidence/runs/*seed2* or *seed3*
  directories — confirms nothing from this block has launched yet; idempotent
  resume check has nothing to resume.

STOP before any launch verb. Read the seed-1 configs to translate the
seed-threading mechanism
(archive/experiment/phase1/grpo/configs/sft_schema_clean_response_confidence_seed1_full.yaml,
grpo_schema_clean_sft_merged_seed1_full.yaml) and confirmed against trainer
source
(synaptic-tuner/Trainers/{sft,dpo,kto}/train_sft.py|train_dpo.py|train_kto.py):
every seed-1 config carries TWO independent randomness controls — a top-level
`seed:` field (threaded to `config.seed`, which becomes the HF Trainer's
`seed=`: data order / dropout / sampling) and a separate `lora.random_state:`
field passed only to `FastLanguageModel.get_peft_model(random_state=...)`,
which seeds the LoRA adapter's initial weight matrices. These are not linked
in code. For DPO/KTO, `--seed` is a CLI override but there is NO
`--lora-random-state` CLI flag (confirmed via `train_dpo.py --help` /
`train_kto.py --help`) — `lora.random_state` is config-file-only.

Every seed-1 config sets `lora.random_state: 1`, matching `seed: 1`; the
tuner's own baseline default (synaptic-tuner/Trainers/{sft,kto}/configs/
config.yaml) is `random_state: 3407`. This could mean "mirror the seed number
into random_state" was an intentional seed-1 convention, or it could be
coincidental use of the template default that happens to equal the seed
number. Neither AMENDMENT.md, cell.yaml (whose `lora:` block fixes only `r`,
`alpha`, `dropout`, with no `random_state` key), gates.yaml, nor the
clean-mainline runbook (whose commands pass `--seed 1` and never mention
`--lora-random-state` or an equivalent) resolves this. If seed 2/3 configs
clone seed-1 and only bump `seed:`, all three "seeds"' LoRA adapters would
start from byte-identical initial weight matrices — only the data-order/
dropout stream would vary. That is a materially weaker replicate than one
where LoRA init also varies per seed, and it changes what a G1 seed-artifact
failure would even mean. This is exactly the "seed-threading mechanism
ambiguous in the docs" stop condition named in the dispatch. Not resolved by
guessing; escalated to the lead. No training or eval verb has been run. Zero
GPU time spent (nvidia-smi still 0MiB at time of writing). Zero budget burned
against the ~64h / 42h-per-seed guardrail.

### 2026-07-31 — LAUNCH: seed-2 serial chain begins (signed block, user-approved)

Launch record written BEFORE any launch verb, per the launch-order rule.

Authority: amendment signed 2026-07-31 (`bin/exp sign`, merged to main in PR
#379); user approved the direction ("worth finishing this off so we can make
this paper neat and symmetrical"), scope ("Full symmetry"), and signing ("Sign
as drafted"). GPU freed 2026-07-31 ~22:54 UTC when the KTO seed-3 eval
container exited 0.

What launches now: the seed-2 serial chain in `cell.yaml` `launch_order`
(clean_sft -> clean_sft_dpo -> clean_sft_kto -> clean_sft_grpo_v2 -> four
stage-3 stacks), then the identical seed-3 chain. Every training/eval verb runs
inside the pinned container lane: `unsloth/unsloth:latest`, digest
`sha256:f21629b9ae4ed11231768edfaed0f40d41d85d6ea9a71e8096a3d96ea0311772`
(re-verified 2026-07-31: Docker Hub `latest` last pushed 2026-05-31, byte-
identical to the June seed-1 runtime), launched `--user root` from the
canonical checkout.

G0 stop-before-outcome discipline: dataset audit already re-verified against
the frozen Amendment E §3.3 numbers on 2026-07-31 (byte-identical deterministic
rebuild, all six numbers exact); merged-source check + 192-row bounded smoke
after every merge; any G0 failure is a hard stop and a report, never a retune.

Execution is delegated to a background harness agent under a report-only
contract: it launches, watches, records each step here, and adjudicates
NOTHING. G1/G2 adjudication is lead-only after both seeds' terminal evals
exist. Budget guardrails from the signed amendment: pause and report if the
seed-2 block exceeds ~42 h or the total exceeds ~83 h.

### 2026-07-31 — draft scaffolded, gates proposed, NOT signed

Drafting pass only. Nothing signed, nothing committed, nothing launched.

Scaffolded with `bin/exp new grpo-three-seed-confirmatory --title "GRPO
Three-Seed Confirmatory Block" --type training-run`. Filled `AMENDMENT.md`,
`cell.yaml`, `gates.yaml`, and the manifest's `question` / `checkpoint` /
`instrument.configs` / `inputs`. `bin/exp validate` passes (99 experiments, no
warning against this slug — `instrument.modules` is empty, so no persistence
declaration is required). `bin/exp regen` run after the manifest edits.

`prediction:` and `falsifier:` are deliberately left EMPTY in the manifest, and
the corresponding AMENDMENT.md sections carry explicit empty-slot markers. The PI
fills the prediction and the lead fills the orchestrator prediction at sign time;
`bin/exp sign` refuses while either field is blank, so the tooling enforces it.
The gates and falsifier in `gates.yaml` are marked `status: proposed` and are
drafting proposals for lead adjudication, not settled thresholds.

**Pre-sign feasibility probe: NOT YET DONE — blocking for sign.** The
experiment-runner reference requires confirming every arm is constructible from
data that exists before signing. `scratch/schema_response_confidence/` is
uncommitted and absent from this worktree, so the four training datasets could
not be inspected. Before sign, rebuild them from
`archive/experiment/phase1/grpo/build_schema_response_confidence_datasets.py
--include-ambiguous-middle` and record here: path, row count, and the clean-SFT
audit against the frozen Amendment E numbers (14,943 rows / 7,981 known / 6,414
unknown / 548 ambiguous / 2,489 unique targets / range [0.3508, 0.90],
`experiments/probe-scaled-response-confidence/AMENDMENT.md:199-206`). A mismatch
is a hard stop.

**Open items carried to the lead** (detail in AMENDMENT.md):

- Amendment G overlap. `best-stack-replication-scale-gate` (DRAFT) already
  registers the same seed-2/3 replication for the single best stack. This block
  is a strict superset; both cannot be signed as written.
- Lane. PROTOCOL v0.3 §3.4 scopes the 3090 as the dev/smoke lane, not the matrix
  lane (`archive/docs/protocols/phase1/PROTOCOL.md:543-545`). This block is a
  serial tens-of-hours matrix on the 3090. Flagged, not resolved.
- Intermediate-stage gate evals. Proposed: keep both the 192-row bounded smokes
  (already frozen by Amendment F §8, non-discretionary) and the full evals on the
  stage-1 base and stage-2 arms (they are terminal arms and the G1 denominator,
  not intermediates).
- Budget correction. Measured seed-1 full-eval wall-clock is 21–41 minutes per
  arm, not ~4 h; ~4 h is the total across all eight evals in a seed. The ~24 h
  training figure per seed holds (measured 26.2 h).
