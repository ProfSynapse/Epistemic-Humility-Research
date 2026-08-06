# GRPO Three-Seed Confirmatory Block notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

### 2026-08-04 — grpo_v2 seed-2 training COMPLETE (lead-verified); merge + bounded smoke G0 PASS; full eval LAUNCHED

Lead confirmed training exited 0 at 21:21:38Z (lead-verified, not re-derived by
this harness): 1861 steps, final epoch 0.9941 at last reward log, final_loss
0.0768, final reward 0.9071 at step ~1850 (well above seed-1's final 0.617 —
recorded plainly, no interpretation), `final_model/` 268M with
`adapter_model.safetensors`, run dir `20260804_131151`, wall ~8h10m (measured
`train_runtime_seconds` 29359.363 = 8.155h) against the 7.22h estimate — counted
against budget below. This harness independently re-verified the same evidence
from artifacts: `final_model/adapter_model.safetensors` 264,308,896 bytes
present; `training_lineage.json` shows `final_step: 1861`, `final_loss: 0.0768`,
`train_examples: 14888`, `seed: 2`; log tail confirms `train_end` at step 1861
and `rewards/combined_reward/mean: 0.9071195...` at the last logged step. Note:
this GRPO run's `training_lineage.json` carries no top-level `runtime` key at
all (unlike SFT/DPO/KTO's `runtime.status`/`runtime.time` fields) — a trainer
format difference, not missing data; completion evidence is exit 0 + artifacts
+ log `train_end` event instead.

**Merge.** Container `eh-grpo3seed-2-clean_sft_grpo_v2-merge-20260804T212326Z`,
exit 0. Mechanism identical to every prior merge in this chain
(`shared.model_loading.merge.merge_lora_checkpoint`, `max_seq_length=2048,
load_in_4bit=True`). Output-path naming convention confirmed against the
seed-1 precedent
(`archive/experiment/phase1/eval/config/eval_amendment_f_response_confidence_selfaware_clean_sft_grpo_v2_merged_seed1_sanity_local_4b.yaml:5`):
`<run_path>/Qwen3-4B-clean-sft-grpo-v2/merged-16bit`. Output at
`scratch/schema_response_confidence/runs/schema_clean_sft_grpo_v2_seed2_full/20260804_131151/Qwen3-4B-clean-sft-grpo-v2/merged-16bit/`:
`config.json` present, 2 safetensors shards (4967215360 + 3077766632 bytes =
7.6G total). Disk 231G -> 224G free. Ran `scripts/ops/prune_runtime.sh stage`
after (319.4MB reclaimed; also removed the long-idle unrelated `cc-test-pg`
postgres container, already exited before the prune ran — not part of this
chain, no interference).

**Bounded smoke (G0 `bounded_smoke_coverage`).** Config
`experiments/grpo-three-seed-confirmatory/configs/eval_grpo3seed_response_confidence_selfaware_clean_sft_grpo_v2_seed2_merged_smoke_local_4b.yaml`,
cloned from the seed-1 GRPO-v2-merged sanity config (path above) — evaluates
the merged GRPO v2 checkpoint directly (no adapter), same pattern as the
DPO/KTO merged-smoke sanity checks earlier in this chain; offset 2240 / limit
192 unchanged. Written to worktree + canonical. Container
`eh-grpo3seed-2-clean_sft_grpo_v2-smoke-20260804T212816Z`, exit 0. Results:
`archive/experiment/phase1/eval/results_grpo3seed_response_confidence_selfaware_clean_sft_grpo_v2_seed2_merged_smoke_4b/clean_sft_grpo_v2_merged_seed2_smoke__selfaware/`
(`metrics.json`, `scored_rows.jsonl` 192 lines, `bootstrap_ci.json` all
present).

Verified numbers (n=192, 97 known / 95 unknown): 192/192 rows scored, 192/192
stated-confidence coverage (`n_with_confidence` 192, `n_missing_confidence` 0),
`enable_thinking` uniformly `False` (all 192 rows checked), 0 thinking-tag-
substring hits in `generated_answer` (field-checked only, no content read, per
data containment). Behavioral: `refusal_recall_pct` 93.68,
`answer_on_unknown_pct` 6.32, `over_refusal_pct` 75.26, `refusal_rate_pct`
84.38, `correct_on_known_pct` 50.0, `truthful_pct` 52.6. Confidence:
`mean_stated_confidence` 0.818065, `brier_vs_response_appropriateness`
0.329849.

G0 `bounded_smoke_coverage`: PASS (raw numbers reported; adjudication is
lead-only). Ran `scripts/ops/prune_runtime.sh stage` again (168.9MB reclaimed).

**Full eval config written** (worktree + canonical, byte-identical):
`experiments/grpo-three-seed-confirmatory/configs/eval_grpo3seed_response_confidence_selfaware_clean_sft_grpo_v2_seed2_full_local_4b.yaml`,
cloned from the seed-1 "corrected_base_full" precedent
(`archive/experiment/phase1/eval/config/eval_amendment_e_response_confidence_selfaware_clean_sft_grpo_v2_seed1_corrected_base_full_local_4b.yaml`)
— confirmed via that precedent that `clean_sft_grpo_v2`'s terminal/paper-2
number is the GRPO v2 LoRA evaluated on the merged **clean-SFT base**
(`sft_schema_clean_seed2_full/20260731_232307/.../merged-16bit`), with the
GRPO v2 adapter at `arms[].adapter` pointing at
`.../schema_clean_sft_grpo_v2_seed2_full/20260804_131151/final_model` — NOT
the merged-GRPO-v2 checkpoint above, which exists solely as the bounded-smoke
sanity target and the stage-3 training source. Full file, no offset/limit
override, per cell.yaml `eval_population: selfaware-full-3369`.

Preflight before launch: digest match, `df -h /` 224G free, GPU idle, `docker
ps -a` clean of chain containers.

**Launched (LONG container, lead notified immediately per contract):**
`eh-grpo3seed-2-clean_sft_grpo_v2-full_eval-20260804T213111Z`, started
2026-08-04T21:31:11Z. Expected ~41min per seed-1 precedent (E note
`:1613->:1648`). Background `docker wait` watch set; lead holds an independent
watch. **HOLDING** after this completes and is verified — stage-3 stacks
remain unreleased until the lead adjudicates G1.

**Full eval COMPLETE (lead-verified, independently re-confirmed by this
harness from `metrics.json` before recording):**
`eh-grpo3seed-2-clean_sft_grpo_v2-full_eval-20260804T213111Z` exited 0 at
22:00:21Z (started 21:31:11Z, ~29m). Results at
`archive/experiment/phase1/eval/results_grpo3seed_response_confidence_selfaware_clean_sft_grpo_v2_seed2_full_4b/clean_schema_sft_grpo_v2_seed2__selfaware/`
(`metrics.json`, `scored_rows.jsonl` 3369 lines, `bootstrap_ci.json` all
present). n=3369 (2337 known / 1032 unknown), 100% stated-confidence coverage.
`refusal_recall_pct` 94.28, `answer_on_unknown_pct` 5.72, `over_refusal_pct`
66.75, `refusal_rate_pct` 75.19, `correct_on_known_pct` 54.05, `truthful_pct`
41.35. Confidence: `mean_stated_confidence` 0.819148,
`brier_vs_response_appropriateness` 0.405945.

**LEAD ADJUDICATION (recorded verbatim, this harness does not adjudicate):**
G1 seed-2 leg PASS — `answer_on_unknown_pct` 10.08 -> 5.72 (−4.36pp, floor
3.0pp) and `refusal_recall_pct` 89.92 -> 94.28 (+4.36pp, floor 3.0pp), both
conditions met vs the same-seed base (`clean_schema_sft_merged_seed2`).
Overall G1 remains **OPEN** pending seed 3 per the registered two-seed
requirement. Seed-1 comparison effect was ±6.39pp; this seed's ±4.36pp is
attenuation within the direction-plus-floor design, not a design violation.

Queue item 4 (grpo_v2 seed-2: train + merge + smoke + full eval) is now fully
closed. Ran `scripts/ops/prune_runtime.sh stage` after merge and after smoke
(see entries above). **STAGE-3 STACKS RELEASED** by the lead, serial per
cell.yaml `launch_order`: `clean_sft_dpo_grpo`, `clean_sft_kto_grpo`,
`clean_sft_grpo_dpo`, `clean_sft_grpo_kto`. Sources per cell.yaml (read
directly, not from memory): `clean_sft_dpo_grpo` from merged `clean_sft_dpo`;
`clean_sft_kto_grpo` from merged `clean_sft_kto`; `clean_sft_grpo_dpo` and
`clean_sft_grpo_kto` both from merged `clean_sft_grpo_v2` (the checkpoint
merged above). Seed-2 merged DPO/KTO sources re-verified intact on disk before
building new configs:
`scratch/schema_response_confidence/runs/schema_clean_sft_dpo_seed2_full/20260801_183028/Qwen3-4B-clean-sft-dpo/merged-16bit/`
and
`scratch/schema_response_confidence/runs/schema_clean_sft_kto_seed2_full/20260801_213332/Qwen3-4B-clean-sft-kto/merged-16bit/`.

Wrote seed-2 configs for the first two stacks (worktree + canonical,
byte-identical), cloned from the seed-1 precedents
(`archive/experiment/phase1/grpo/configs/grpo_clean_sft_dpo_grpo_seed1_full.yaml`,
`grpo_clean_sft_kto_grpo_seed1_full.yaml`) with the same three changes as the
grpo_v2 seed-2 config: seed-2 merged source model_name, `lora.random_state: 2`,
and the corrected absolute reward-file path (same stale-path bug, same fix,
confirmed present in both seed-1 templates before writing):
`experiments/grpo-three-seed-confirmatory/configs/grpo_clean_sft_dpo_grpo_seed2_full.yaml`
and `grpo_clean_sft_kto_grpo_seed2_full.yaml`.

**Stack 1 — `clean_sft_dpo_grpo`.** `--dry-run` validated cleanly before
launch: model loaded from the seed-2 DPO merged source, reward
`epistemic_humility_reward` loaded, 14888-example dataset formatted, LoRA
66,060,288 trainable params, batch 32x1 / num_generations 4 / LR 5e-6 matched
cell.yaml. **Launched (LONG container, lead notified immediately):**
`eh-grpo3seed-2-clean_sft_dpo_grpo-train-20260804T220342Z`, started
2026-08-04T22:03:43Z, running. Expected ~4.94h per seed-1 measured precedent (F
note :350->:373). Background `docker wait` watch set; lead holds an
independent watch.

This NOTEBOOK draft is final through the grpo_v2 closeout above (everything
above this line and up through the "grpo_v2 seed-2 training COMPLETE" heading)
— confirmed to the lead for commit.

### 2026-08-04 — Fifth executor: queue item 4 (clean_sft_grpo_v2 seed-2 training) LAUNCHED, HOLDING (stage-3 stacks not released)

Fifth execution harness. Read NOTEBOOK.md, AMENDMENT.md, cell.yaml, gates.yaml
per dispatch before touching anything.

**Independent state re-verification (not trusted from handoff):** digest
`sha256:f21629b9ae4ed11231768edfaed0f40d41d85d6ea9a71e8096a3d96ea0311772` matched
exactly via `docker images --digests` and inside-container `nvidia-smi` (RTX
3090, 0MiB/24576MiB); `df -h /` 233G free; host `nvidia-smi` idle; `docker ps -a`
showed 0 running chain containers (one unrelated `cc-test-pg`, itself exited by
this point). Seed-2 stage-1 merged source
(`scratch/schema_response_confidence/runs/sft_schema_clean_seed2_full/20260731_232307/Qwen3-4B-bnb-4bit/merged-16bit`)
re-confirmed intact: `config.json` + 2 safetensors shards. GRPO dataset row
counts re-verified with newline-only byte counting (not `str.splitlines`):
`grpo_train.jsonl` 14888, `grpo_dev.jsonl` 1655 — both match cell.yaml
`frozen_audit` exactly.

**Bug found and fixed before launch (lead notified in full detail via
SendMessage):** the seed-1 GRPO v2 config template
(`archive/experiment/phase1/grpo/configs/grpo_schema_clean_sft_merged_seed1_v2_full.yaml`)
carries a stale pre-archive-move relative path for `rewards.custom.file`
(`"../../../experiment/phase1/grpo/humility_reward_v2.py"`). `base_dir` for
that field resolves as `Path(train_grpo.py).parent` =
`synaptic-tuner/Trainers/grpo`, so the relative path resolves to
`<repo>/experiment/phase1/grpo/humility_reward_v2.py`, which is missing
post-move; only `archive/experiment/phase1/grpo/humility_reward_v2.py` exists.
Same bug class as the five stale argparse defaults already fixed in the
dataset builder on this branch (2026-07-31 entry below). Confirmed via
`synaptic-tuner/Trainers/grpo/src/rewards.py:609-613`: an unresolved file
leaves `components` empty and raises `ValueError("No reward components
loaded")` at trainer startup — a loud fail, not silent corruption, but would
have blocked this launch had it not been caught first. All four seed-1 GRPO
configs on disk carry the same stale path; only relevant to new seed-2/3
configs since seed-1 outputs are frozen historical data, never re-run.

Also confirmed (not previously stated anywhere in this chain's docs):
`train_grpo.py`'s argparse does **not** accept `--no-dashboard`/`--quiet`
(only `--config`/`--dry-run`/`--resume-from-checkpoint`/`--model-name`/
`--dataset-name`/`--dataset-file`/`--local-file`/`--use-gspo`/
`--pivot-profile-only`). cell.yaml's generic `train_flags: [--no-dashboard,
--quiet]` does not apply to the GRPO trainer; launched with `--config` only,
matching the exact seed-1 launch precedent in the E session note
(`eh-clean-sft-grpo-v2-full-20260624a ... train_grpo.py --config
.../grpo_schema_clean_sft_merged_seed1_v2_full.yaml`).

**Config written** (worktree + canonical, byte-identical):
`experiments/grpo-three-seed-confirmatory/configs/grpo_schema_clean_sft_merged_seed2_v2_full.yaml`,
a seed-2 clone of the seed-1 template with exactly three changes, none
touching a cell.yaml/gates.yaml pinned value: (1) `model.model_name` points at
the seed-2 merged source above, (2) `lora.random_state: 2` per the standing
lead ruling (2026-07-31 entry below) that random_state mirrors seed, (3)
`rewards.custom.file` corrected to the absolute in-container path
`/workspace/repo/archive/experiment/phase1/grpo/humility_reward_v2.py` — same
unmodified reward file (`epistemic_humility_reward` confirmed defined at that
path), only the path corrected. All other fields (LoRA r32/alpha64/dropout0.05,
batch 32 / grad-accum 1 / num_generations 4 / max_prompt 512 / max_completion
128 / temperature 1.35 / LR 5e-6 / beta 0.1 / 1 epoch / bf16 / adamw_8bit)
copied verbatim from the seed-1 precedent, matching cell.yaml `arms:
clean_sft_grpo_v2`.

**Validation before real launch.** Ran `--dry-run` (full model + LoRA + reward
+ dataset load, no training step, ~90s, negligible GPU compute) to verify the
path fix actually resolves before committing ~7h of GPU time: passed clean —
printed `custom: epistemic_humility_reward (weight=1.0)`, dataset loaded 14888
examples, LoRA 66,060,288 trainable params (2.91%), batch 32x1 / num_generations
4 / LR 5e-6 all matched cell.yaml. This created an empty root-owned run dir at
`scratch/schema_response_confidence/runs/schema_clean_sft_grpo_v2_seed2_full/20260804_131028/`
(empty `checkpoints/`/`logs/` only, no `training_lineage.json` or adapter) that
this harness's own permission system denied `rm` on (not a filesystem
permission issue — root owns it, harness declined the delete) — harmless, has
no real artifacts, flagged so it is not confused with the real run's
timestamped directory.

**Launched (LONG container, lead notified immediately with the exact name
before any other action, per contract):**
`eh-grpo3seed-2-clean_sft_grpo_v2-train-20260804T131127Z`, started
2026-08-04T13:11:27Z, running at time of writing. Expected ~7.22h per seed-1
measured precedent (E note `train_runtime_seconds: 25983.384`). Command:

```
docker run -d --name eh-grpo3seed-2-clean_sft_grpo_v2-train-20260804T131127Z \
  --user root --gpus all --ipc=host \
  -e HF_HOME=/workspace/repo/.cache/hf \
  -e HUGGINGFACE_HUB_CACHE=/workspace/repo/.cache/hf/hub \
  -v /home/profsynapse/code/Epistemic-Humility-Research:/workspace/repo \
  -w /workspace/repo \
  --entrypoint python3 \
  unsloth/unsloth:latest \
  synaptic-tuner/Trainers/grpo/train_grpo.py \
  --config experiments/grpo-three-seed-confirmatory/configs/grpo_schema_clean_sft_merged_seed2_v2_full.yaml
```

Background `docker wait` watch set as best-effort redundancy; lead holds the
primary watch. `docker inspect` will be checked explicitly at the start of
every turn regardless of wake, per the standing host note above (docker-wait
wake unreliable for long containers on this host).

Cumulative GPU-compute-hours: ~4.5h carried from handoff + dry-run (~90s,
negligible) + this training run in progress (budgeted 7.22h). **HOLDING per
dispatch** — this is queue item 4; the four stage-3 stacks remain unreleased
until the lead instructs.

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

## 2026-08-05 ~02:45Z — Stack 1 (clean_sft_dpo_grpo, seed 2) training COMPLETE; executor succession 5→6

Lead primary watch fired on `eh-grpo3seed-2-clean_sft_dpo_grpo-train-20260804T220342Z` (exit 0). Lead-verified:

- Run dir `scratch/schema_response_confidence/runs/clean_sft_dpo_grpo_seed2_full/20260804_220407`: 1,861 steps, 1.0 epoch, final loss 0.0962, final logged reward 1.0998 @ step 1850 (grpo_v2-from-clean-SFT comparison: 0.9071 — DPO-first lineage starts closer to the reward target).
- `training_lineage.json` base_model = seed-2 DPO merged-16bit (`schema_clean_sft_dpo_seed2_full/20260801_183028/.../merged-16bit`) — correct stage-3 source; seed 2; batch 32 / num_generations 4 / lr 5e-6, all matching registered cell.yaml values.
- `final_model` adapter present (268M); capacity profile peak reserved 82.6%, OOM risk low.

Executor5 unreachable after lead-session compaction (same severance mode as earlier successions). Executor6 spawned with the standing closeout spec: stage prune + free-space precheck, merge, 192-row smoke on merged, full eval (adapter on source merged base per lineage convention), pinned-digest check before every launch, short ops foreground, long eval lead-watched.

Next after stack-1 closeout: stack 2 kto_grpo (config pre-staged: `configs/grpo_clean_sft_kto_grpo_seed2_full.yaml`).

## 2026-08-05 ~03:30Z — Stack 1 (clean_sft_dpo_grpo, seed 2) CLOSED; stack 2 (kto_grpo) released

Full eval container `eh-grpo3seed-2-clean_sft_dpo_grpo-full_eval-20260805T025548Z` exited 0. Lead verified from `results_grpo3seed_response_confidence_selfaware_clean_sft_dpo_grpo_seed2_full_4b` artifacts (coverage re-derived from scored_rows.jsonl, newline-only split):

- n=3369 (2337 known / 1032 unknown), answer coverage 3369/3369, stated-confidence coverage 3369/3369, thinking-tag hits 0. Row `model` field uniformly `qwen3-4b-clean-sft-dpo-merged-seed2` — correct lineage (adapter on seed-2 DPO merged base).
- Headline: refusal_recall 94.38, answer_on_unknown 5.62, over_refusal 65.81, truthful 41.50, correct_on_known 53.07, refusal_rate 74.56.
- Same-seed comparisons (navigation, G2 adjudication deferred until all stacks close): vs DPO parent (89.34/10.66) the GRPO stage moves answer-on-unknown −5.04pp; vs base (89.92/10.08) −4.46pp; endpoint nearly coincides with same-seed grpo_v2 (94.28/5.72, over_refusal 66.75 vs 65.81).
- Bounded smoke on the newly-merged checkpoint (earlier this cycle): 192/192 answer, 192/192 confidence, 0 thinking-tag hits, enable_thinking uniformly False — G0 bounded-smoke leg PASS, lead re-derived independently.
- Training record (prior entry): 1861 steps, final loss 0.0962, final reward 1.0998.

G0 for this cell: PASS (coverage + lineage + frozen dataset counts per training_lineage.json train_examples 14888).

Stack 2 released to executor6: clean_sft_kto_grpo training from the seed-2 KTO merged source, pre-staged config `configs/grpo_clean_sft_kto_grpo_seed2_full.yaml`, dry-run before launch, lead holds the primary watch.

## 2026-08-05 ~08:10Z — Stack 2 (clean_sft_kto_grpo, seed 2) training COMPLETE; closeout released

Lead primary watch fired on `eh-grpo3seed-2-clean_sft_kto_grpo-train-20260805T032622Z` (exit 0; 03:26Z → ~08:07Z, ~4h41m, consistent with the dpo_grpo precedent). Lead-verified from run dir `clean_sft_kto_grpo_seed2_full/20260805_032645`:

- `training_lineage.json` base_model = seed-2 KTO merged-16bit (`schema_clean_sft_kto_seed2_full/20260801_213332/.../merged-16bit`) — correct stage-3 source; seed 2; batch 32 / num_generations 4 / lr 5e-6 matching registered cell.yaml values; train_examples 14888 (frozen count).
- 1861 steps, final loss 0.0846, final logged reward 1.134 @ step 1850 (reward endpoint ordering this seed: clean-SFT base 0.9071 < DPO base 1.0998 < KTO base 1.134).
- `final_model` adapter present (268M).

Closeout released to executor6: stage prune + free-space precheck, merge to merged-16bit, 192-row bounded smoke on the merged checkpoint, full 3,369-row eval with the adapter on the seed-2 KTO merged base per the lineage convention (eval configs to be cloned from the stack-1 pair executor6 authored, lineage verified against training_lineage.json before launch). Full eval lead-watched.

Remaining after stack 2: grpo_dpo and grpo_kto (both source from the seed-2 grpo_v2 merged checkpoint), then seed-2 chain complete and seed 3 begins.

## 2026-08-05 ~09:12Z — Stack 2 (clean_sft_kto_grpo, seed 2) CLOSED; stack 3 (grpo_dpo) released

Full eval container `eh-grpo3seed-2-clean_sft_kto_grpo-full_eval-20260805T083704Z` exited 0 (~35m). Lead verified from `results_grpo3seed_response_confidence_selfaware_clean_sft_kto_grpo_seed2_full_4b` artifacts (coverage re-derived from scored_rows.jsonl):

- n=3369 (2337 known / 1032 unknown), answer coverage 3369/3369, stated-confidence 3369/3369, thinking-tag hits 0. Row `model` field uniformly `qwen3-4b-clean-sft-kto-merged-seed2` — correct lineage (adapter on seed-2 KTO merged base).
- Headline: refusal_recall 93.31, answer_on_unknown 6.69, over_refusal 64.23, truthful 41.26, correct_on_known 51.08, refusal_rate 73.14.
- Same-seed comparisons (navigation only, G2 deferred): vs KTO parent (85.66/14.34) the GRPO stage moves answer-on-unknown −7.65pp — the largest stage-3 shift this seed, from the most answer-prone parent; endpoint lands in the same band as grpo_v2 (94.28/5.72) and dpo_grpo (94.38/5.62). All three GRPO-terminal endpoints sit in a 93.3–94.4 recall band despite parents spanning 85.7–89.9.
- Bounded smoke on the newly-merged checkpoint: 192/192 answer, 192/192 confidence, 0 thinking-tag hits, enable_thinking uniformly False, lead re-derived independently. G0 bounded-smoke leg PASS.

G0 for this cell: PASS (coverage + lineage + frozen count 14888 per training_lineage.json).

Stack 3 released to executor6: clean_sft_grpo_dpo — a DPO training run (registered values: batch 2 / grad-accum 4 / lr 5e-6 / beta 0.1, frozen DPO dataset count 14,943) whose source is the seed-2 grpo_v2 merged checkpoint (`schema_clean_sft_grpo_v2_seed2_full/20260804_131151/.../merged-16bit`). Training config to be cloned from the seed-2 clean_sft_dpo config with model_name swapped to the grpo_v2 merged source; no reward-path concern (GRPO-only issue); DPO trainer has no lora random-state flag (baseline 3407, seed-1 precedent). Expected ~1.5h per the seed-2 DPO precedent. Lead holds the training watch.

## 2026-08-05 ~10:45Z — Stack 3 (clean_sft_grpo_dpo, seed 2) training COMPLETE; closeout released

Lead primary watch fired on `eh-grpo3seed-2-clean_sft_grpo_dpo-train-20260805T090846Z` (exit 0; 09:08Z → ~10:42Z, ~1h34m, consistent with the seed-2 DPO precedent). Lead-verified from run dir `clean_sft_grpo_dpo_seed2_full/20260805_090909`:

- `training_lineage.json`: training_type DPO, base_model = seed-2 grpo_v2 merged-16bit (`schema_clean_sft_grpo_v2_seed2_full/20260804_131151/Qwen3-4B-clean-sft-grpo-v2/merged-16bit`) — correct stage-3 source; seed 2; batch 2 / grad-accum 4 / lr 5e-6 / beta 0.1 matching registered cell.yaml values; train_examples 14943 (frozen count).
- 1868 steps, final loss 0.0419. `final_model` adapter present (268M).

Correction to the prior entry (5f59b127): the DPO trainer DOES have a `--dry-run` flag (train_dpo.py argparse line 261; exits before model load). Executor6 read the trainer source, caught the lead's erroneous "no dry-run flag" claim, and ran the free dry-run before launch (exit 0, ~15s; banner matched cell.yaml exactly). Endorsed as standing practice: dry-run or equivalent pre-model-load validation before every multi-hour launch in this chain, all trainer types.

Closeout released to executor6: stage prune + precheck, merge, 192-row bounded smoke on the merged checkpoint, full 3,369-row eval with the adapter on the seed-2 grpo_v2 merged base per lineage convention. Full eval lead-watched.

Remaining after stack 3: grpo_kto (KTO on the same grpo_v2 merged source, registered bs12/ga1/lr1e-6/beta0.1), then seed-2 chain complete: G2 becomes computable and seed 3 begins.

## 2026-08-05 ~13:45Z — Stack 3 (clean_sft_grpo_dpo, seed 2) CLOSED; stack 4 (grpo_kto) released

Full eval container `eh-grpo3seed-2-clean_sft_grpo_dpo-full_eval-20260805T103907Z` exited 0 at ~10:45Z. **Lead watch notification arrived ~3h late** (container had exited 3 hours before the wake fired); GPU sat idle in that window. Recorded as a wake-latency instance against the watch architecture (`.skills/experiment-runner/reference/local-runtime.md`): lead-side `docker wait` remains the most reliable primary signal available, but it is not latency-bounded. Idle time does not count against the compute-hours guardrail; no artifact impact.

Lead verified from `results_grpo3seed_response_confidence_selfaware_clean_sft_grpo_dpo_seed2_full_4b`:

- n=3369 (2337 known / 1032 unknown), answer coverage 3369/3369, stated-confidence 3369/3369, thinking-tag hits 0. Row `model` field uniformly `qwen3-4b-clean-sft-grpo-v2-merged-seed2` — correct lineage (adapter on seed-2 grpo_v2 merged base).
- Headline: refusal_recall 94.67, answer_on_unknown 5.33, over_refusal 65.98, truthful 41.53, correct_on_known 53.08, refusal_rate 74.77.
- Bounded smoke on the newly-merged checkpoint: 192/192 answer, 192/192 confidence, 0 thinking-tag hits, enable_thinking uniformly False, lead re-derived independently. G0 bounded-smoke leg PASS.

G0 for this cell: PASS (coverage + lineage + frozen count 14943 per training_lineage.json).

Navigation note for G2 (NOT an adjudication — G2 is adjudicated only when all four stacks close, from the gates.yaml criteria): at seed 2, `grpo_dpo` (94.67 / 5.33 / over-refusal 65.98) does not reproduce the seed-1 over-refusal relief relative to same-seed `grpo_v2` (94.28 / 5.72 / 66.75) — the over-refusal delta is −0.77pp here. Seed-1 Amendment G recorded a larger relief on that comparison. All five seed-2 GRPO-terminal arms now sit in a 93.3-94.7 recall band with over-refusal 64.2-66.8, i.e. a tight cluster regardless of stage order. Whether that constitutes a G2 PASS/FAIL is deferred to the gate criteria after stack 4.

Stack 4 released to executor6: clean_sft_grpo_kto — KTO on the seed-2 grpo_v2 merged source, registered values bs12 / ga1 / lr1e-6 / beta0.1 with the authorized step-250 VRAM recheck and batch-8 fallback. Dry-run first per the endorsed standing practice. Expected ~1h40m per the seed-2 KTO precedent. Lead holds the training watch.

## 2026-08-05 ~14:00Z — G2 seed-2 leg ADJUDICATED: PASS (lead correction of a prior mischaracterization)

Read `gates.yaml` as the binding criteria before adjudicating. Integrity check: `sha256sum gates.yaml` = 7c79a41894a1fc64df01f07bbb197f8c25239d8625e3d9f3d8bbc97d3e51c0fa, byte-identical to the pin recorded in the signed `experiment.yaml`. These thresholds are the signed criteria.

**G2 (`g2_post_grpo_preference_recovery_replicates`), seed-2 leg.** Comparison as registered: `clean_sft_grpo_dpo` vs same-seed `clean_sft_grpo_v2`. Both values re-read from full-eval `metrics.json` at adjudication time:

| metric | grpo_v2 (denominator) | grpo_dpo | delta | registered condition | result |
| --- | --- | --- | --- | --- | --- |
| over_refusal_pct | 66.75 | 65.98 | −0.77 pp | direction `decrease`, `min_magnitude_pp: null` (deliberately unset) | MET |
| answer_on_unknown_pct | 5.72 | 5.33 | −0.39 pp | `must_not_increase_by_more_than_pp: 2.0` | MET (no reopening at all) |

Neither `not_confirmed_if` clause fires: over-refusal did not increase, and unknown answering did not reopen. **G2 seed-2 leg: PASS.** Overall G2 remains OPEN pending the seed-3 leg (`pass_if: both conditions hold in BOTH seed 2 and seed 3`).

**Lead correction, recorded deliberately.** The prior entry (b0df73a9) and the lead's report to the PI framed this arm as failing to replicate seed 1 and as "a real replication concern for the stacking claim," reasoning from the shrunken effect size (−0.77 pp here vs −2.99 pp at seed 1). That framing applied a magnitude standard the signed gate explicitly declines to set. The gate's own derivation says why: "No magnitude floor is set: at −2.99 pp the effect is too small for a two-seed block to bound ... A magnitude bar here would invent precision the instrument does not have." Judging the arm against an unregistered magnitude bar is goalpost movement in the strict direction, and it is as much a protocol violation as loosening a threshold would be. The gate text governs; the earlier prose does not. The attenuation is still worth REPORTING as a descriptive observation (and G3 three-seed intervals will quantify it properly), but it is not a gate failure and must not be written up as one.

**Second correction:** the prior entry and the lead's PI report said G2 "becomes computable when all four stacks close." That is wrong. G2's registered comparison involves only `clean_sft_grpo_dpo` and `clean_sft_grpo_v2`, both of which closed before stack 4 launched; the seed-2 leg was adjudicable at stack-3 closeout. `clean_sft_grpo_kto` is required for chain completeness and for G3's per-arm three-seed intervals, not for G2.

Standing status after this entry: G0 PASS on every seed-2 cell closed so far; G1 seed-2 leg PASS; G2 seed-2 leg PASS; both G1 and G2 OPEN overall pending seed 3. G3 is a descriptive deliverable, computable only after all three seeds land.

**Governance defect noted, NOT edited:** `gates.yaml` internally still carries `status: proposed`, `adjudicated_by: null`, `adjudicated_date: null` and a "DRAFTING PROPOSAL" header, even though the file is hash-pinned into a signed `experiment.yaml` (the same stale-banner class of defect the AMENDMENT banner records at line 6). The hash pin is authoritative and the thresholds are binding as written. The file was deliberately NOT edited: any byte change breaks the signed pin. Flagged to the PI for a governed housekeeping revision.

## 2026-08-05 ~15:31Z — Stack 4 (clean_sft_grpo_kto, seed 2) training COMPLETE; closeout released

Lead primary watch fired on `eh-grpo3seed-2-clean_sft_grpo_kto-train-20260805T135033Z` (exit 0; 13:50Z → 15:31Z, ~1h41m, matching the seed-2 KTO precedent). Backup polling monitor was armed in parallel after the stack-3 wake-latency instance; the primary fired on time this cycle. Lead-verified from run dir `clean_sft_grpo_kto_seed2_full/20260805_135100`:

- `training_lineage.json`: training_type KTO, base_model = seed-2 grpo_v2 merged-16bit (`schema_clean_sft_grpo_v2_seed2_full/20260804_131151/Qwen3-4B-clean-sft-grpo-v2/merged-16bit`) — correct stage-3 source, same source stack 3 used; seed 2; batch 12 / grad-accum 1 / lr 1e-6 / beta 0.1 matching registered cell.yaml values; train_examples 29886 (frozen count, 1.00:1 True/False balance confirmed at dry-run).
- 2491 steps, final loss 0.0884. `final_model` adapter present (268M).

**Capacity note, recorded not adjudicated.** Peak GPU memory reserved 99.2%, `oom_risk_level: critical`. The run nonetheless completed clean at the registered batch 12, so the pre-registered batch-8 fallback (cell.yaml `capacity_watch`, step-250 recheck) was NOT taken and no divergence occurred. For comparison the stage-2 seed-2 KTO run peaked at 95.92%; stacking KTO on the grpo_v2 merged source costs roughly 3 points of headroom. This is a live risk for the seed-3 replicate of this same arm: 99.2% leaves almost no margin, and a marginally different allocation could OOM mid-run. Flagged for the seed-3 launch decision, where invoking the authorized batch-8 fallback at the step-250 recheck is a pre-registered option the lead may take on the observation rather than a change to registered values.

Closeout released to executor6: stage prune + precheck, merge, 192-row bounded smoke on the merged checkpoint, full 3,369-row eval with the adapter on the seed-2 grpo_v2 merged base per lineage convention. Full eval lead-watched.

This is the FINAL seed-2 arm. On its closeout the seed-2 chain is complete (8/8 arms) and seed 3 is green-lit by the PI (2026-08-05) to begin.

## 2026-08-05 ~16:20Z — SEED-2 CHAIN COMPLETE (8/8 arms); stack 4 closed, G0 PASS

Final full eval container `eh-grpo3seed-2-clean_sft_grpo_kto-full_eval-20260805T154134Z` exited 0. Lead verified from `results_grpo3seed_response_confidence_selfaware_clean_sft_grpo_kto_seed2_full_4b`: n=3369 (2337 known / 1032 unknown), answer coverage 3369/3369, stated-confidence 3369/3369, thinking-tag hits 0, row `model` field uniformly `qwen3-4b-clean-sft-grpo-v2-merged-seed2` (correct lineage: adapter on the grpo_v2 merged base). Frozen count 29886 per training_lineage.json. **G0 for this cell: PASS.**

### Seed-2 full-eval matrix, all eight arms (n=3369, values read from each arm's metrics.json at closeout)

| arm | stage | recall | ans-on-unk | over-refusal | truthful | correct-on-known |
| --- | --- | --- | --- | --- | --- | --- |
| clean_sft (base) | 1 | 89.92 | 10.08 | 58.24 | 41.17 | 47.03 |
| clean_sft_dpo | 2 | 89.34 | 10.66 | 55.97 | 41.32 | 45.68 |
| clean_sft_kto | 2 | 85.66 | 14.34 | 54.00 | 40.31 | 44.09 |
| clean_sft_grpo_v2 | 2 | 94.28 | 5.72 | 66.75 | 41.35 | 54.05 |
| clean_sft_dpo_grpo | 3 | 94.38 | 5.62 | 65.81 | 41.50 | 53.07 |
| clean_sft_kto_grpo | 3 | 93.31 | 6.69 | 64.23 | 41.26 | 51.08 |
| clean_sft_grpo_dpo | 3 | 94.67 | 5.33 | 65.98 | 41.53 | 53.08 |
| clean_sft_grpo_kto | 3 | 91.76 | 8.24 | 61.10 | 41.32 | 48.95 |

G0 PASS on all eight cells. Gate status: **G1 seed-2 leg PASS**, **G2 seed-2 leg PASS** (both adjudicated in the entries above), both OPEN overall pending seed 3. G3 is descriptive and computable only after all three seeds land.

### Descriptive observations, explicitly NOT gate adjudications

1. **GRPO-first arms converge.** The three arms whose terminal stage is GRPO (grpo_v2, dpo_grpo, kto_grpo) land in a 93.3-94.4 recall band with answer-on-unknown 5.62-6.69, despite parents spanning 85.66-89.92 recall. At this seed the preceding preference stage barely moves where GRPO arrives.
2. **`grpo_kto` is the outlier of the whole matrix and deserves attention at seed 3.** Running KTO after GRPO reopens unknown answering to 8.24 (+2.52 pp vs same-seed grpo_v2's 5.72) while delivering the largest over-refusal relief in the block (61.10, -5.65 pp vs grpo_v2). It is the only stage-3 arm that materially gives back GRPO's abstention gain. NOTE CAREFULLY: G2's registered comparison is `clean_sft_grpo_dpo` vs `clean_sft_grpo_v2` ONLY (gates.yaml `g2_post_grpo_preference_recovery_replicates`). `grpo_kto` is NOT a G2 comparison and is not adjudicated by that gate. The observation that its +2.52 pp reopening would exceed the +2.0 pp cap G2 applies to the DPO analogue is reported here as a DESCRIPTIVE parallel only — applying a registered gate to an unregistered comparison after seeing the number would be inventing a gate, and is not done.
3. **Truthful is flat across every arm except stage-2 KTO** (41.17-41.53 for seven of eight; kto 40.31). Whatever these stages move, it is the abstention/over-refusal tradeoff, not aggregate truthfulness.
4. **Over-refusal is the standing cost.** Every GRPO-touching arm sits at 61.1-66.8 against the base's 58.24. No stage-3 ordering recovered it to baseline at this seed.

### Capacity record for seed-3 planning

`clean_sft_grpo_kto` peaked at 99.2% GPU reserved (oom_risk critical) yet completed clean at registered batch 12; the pre-registered batch-8 fallback was not taken and no divergence occurred. Its stage-2 counterpart peaked at 95.92%. Seed 3 replicates this arm with almost no headroom; the authorized step-250 fallback is available as a pre-registered lead call on the observation.

### Seed-2 compute accounting

Training across the 8 arms: **24.37 GPU-hours** (grpo_v2 8.16, kto_grpo 5.01, dpo_grpo 4.66, kto 1.71, grpo_kto 1.67, dpo 1.40, grpo_dpo 1.34, clean_sft 0.43), computed from run-record timestamps because stage-boundary pruning removes the containers. With merges, smokes and eight full evals, seed 2 lands near 29-30 h against its 42 h allowance. Projecting seed 3 at the same shape puts the block near 60 h of the 83 h total.

**Seed 3 is PI-green-lit (2026-08-05) and dispatched next.** Stage-1 config pre-staged and lead-verified: `configs/sft_schema_clean_response_confidence_seed3_full_config.py`, AST-compared against the seed-2 config across 48 assignment keys with exactly three changed (`config.seed` 2->3, `config.lora.random_state` 2->3, `config.training.output_dir` path). Foundation base present in the pinned cache (2.5 G).

## 2026-08-05 ~16:39Z — Seed-3 stage-1 CRASHED (CUDA fault). G0 instrument STOP, relaunch authorized.

First seed-3 launch `eh-grpo3seed-3-clean_sft-train-20260805T161221Z` **exited 139 (SIGSEGV)** at step 975/1495, ~16 min in. No `final_model`, no `training_lineage.json`. Run dir `sft_schema_clean_seed3_full/20260805_161250` holds only `logs/` and `checkpoints/checkpoint-500`.

**This is a G0 `training_completed_clean` FAILURE** (gates.yaml: "training exits 0 with final adapter artifacts and training_lineage.json present"). Per G0's registered interpretation it is a stop_before_outcome: the cell is repaired and relaunched, NOT reported. No outcome number from this container is read, retained, or compared to anything.

**Watch-reading correction, recorded so it is not repeated.** The lead's background `docker wait` task reported "exit code 0", which is the exit status of the *wait command*, not of the container. The container's exit code is written to the watch's stdout (here `139`). **Always read the watch output file, never infer container success from the task's own exit status.** This nearly caused a crashed run to be treated as complete.

### Diagnosis

Failure signature is `torch.AcceleratorError: CUDA error: unknown error` (`cudaErrorUnknown`) raised from `currentStreamCaptureStatusMayInitCtx`, then `terminate called after throwing an instance of 'c10::AcceleratorError'`. This is a driver/context-level fault, not an allocator failure; an OOM reports as OOM.

Capacity was ruled OUT as the cause by direct comparison against the seed-2 run of the byte-identical config (only seed, lora.random_state and output_dir differ, AST-verified across 48 assignment keys):

| run | gpu_memory_gb max | gpu_memory_gb last | system_ram_used max | outcome |
| --- | --- | --- | --- | --- |
| seed-2 SFT | 32.64 | 24.67 @ step 1495 | 4.38 | completed clean |
| seed-3 SFT | 27.71 | 27.71 @ step 975 | 6.63 | SIGSEGV |

Seed 2 ran HIGHER on the same metric and finished. (Values above the 24 GB physical card confirm this counter includes WSL shared/spill memory, which is normal for this workload on this host.) Capacity is therefore not the differentiator, and no registered value is implicated.

Post-crash environment verified healthy before authorizing relaunch: GPU idle at 0% / 0 MiB / 46 C; the pinned image resolves to digest `sha256:f21629b9ae4ed11231768edfaed0f40d41d85d6ea9a71e8096a3d96ea0311772` and `nvidia-smi` runs inside it against the card; disk 187 G free. Consistent with the transient WSL2 GPU-passthrough instability this host has shown before (see the 2026-08-02 crash entry and the nvidia-runtime loss recorded in `local-runtime.md`).

### Disposition

Relaunch stage 1 FROM SCRATCH, not resumed from `checkpoint-500`. Resuming would give seed 3 a training trajectory produced differently from seeds 1 and 2 (both single uninterrupted runs), and nothing in the signed instrument authorizes resume-from-checkpoint as equivalent for a confirmatory replicate. The crashed run directory is retained as evidence for now and is prunable at the next stage boundary.

No change to any registered value. Same config file, same pinned digest, same procedure.

## 2026-08-05 ~17:02Z — Seed-3 stage 1 (clean_sft) COMPLETE on relaunch; merge + base-eval released

Relaunch `eh-grpo3seed-3-clean_sft-train-20260805T163548Z` **exited 0** (container exit code read from the watch stdout, per the correction recorded above; backup monitor independently reported `exited|0`). Run dir `sft_schema_clean_seed3_full/20260805_163620`, ~25 min, matching the seed-2 anchor.

Lead-verified: training_type SFT; base_model `unsloth/Qwen3-4B-bnb-4bit` (FOUNDATION, correct — seed 3 rebuilds its own lineage and takes no seed-2 checkpoint); seed 3; batch 10 / accum 1 / lr 2e-4 / 1 epoch; train_examples 14943 (frozen count); 1495 steps; final loss 0.4282; `final_model` present (253 M) and `training_lineage.json` present. **G0 `training_completed_clean`: PASS.**

Provenance note on `lora.random_state`: the SFT `training_lineage.json` lora block records rank/alpha/dropout/target_modules/bias and does NOT record `random_state` — verified identical in the seed-2 lineage, so this is how the trainer writes the file, not a seed-3 anomaly. The config-level evidence stands as the provenance record: an AST comparison of all 48 assignment keys between the seed-2 and seed-3 config files showed exactly three changed (`config.seed` 2->3, `config.lora.random_state` 2->3, `config.training.output_dir`).

Descriptive observation, not a gate matter: final SFT loss is 0.4281 (seed 1), 0.4281 (seed 2), 0.4282 (seed 3). The clean-SFT stage converges to essentially the same point at every seed. The seed-1/seed-2 identity was previously checked and found to be coincidence at the step level (57 of 59 logged steps differ); seed 3 landing one ten-thousandth away is consistent with that reading rather than with any config collision.

Released to executor6: merge stage-1 to merged-16bit, 192-row bounded smoke, then the FULL 3,369-row eval on the merged base. That base full eval is the **G1 denominator for seed 3** and gates everything downstream, so it runs before any stage-2 arm launches. Stage-2 arms (dpo, kto, grpo_v2, all from merged(clean_sft)) follow serially per launch_order once the base is closed.

## 2026-08-05 ~17:56Z — Seed-3 stage-1 base CLOSED; G1 denominator for seed 3 established; stage 2 released

Base full eval `eh-grpo3seed-3-clean_sft-fulleval-20260805T171811Z` exit 0 (read from watch stdout; backup monitor independently `exited|0`). Lead-verified from `results_grpo3seed_response_confidence_selfaware_clean_sft_seed3_merged_full_4b`: n=3369 (2337 known / 1032 unknown), answer coverage 3369/3369, stated-confidence 3369/3369, thinking-tag hits 0, row `model` field uniformly `qwen3-4b-clean-schema-sft-merged-seed3` (correct: seed-3 merged base evaluated directly, `adapter: null`). Bounded smoke on the same checkpoint was 192/192/192/0, lead re-derived. **G0 for this cell: PASS.**

### Seed-3 G1 denominator (registered comparator for `clean_sft_grpo_v2` at this seed)

| metric | seed 3 base | seed 2 base | seed 1 base |
| --- | --- | --- | --- |
| refusal_recall_pct | 88.28 | 89.92 | 87.02 |
| answer_on_unknown_pct | 11.72 | 10.08 | 12.98 |
| over_refusal_pct | 59.01 | 58.24 | 57.51 |
| truthful_pct | 40.55 | 41.17 | - |
| correct_on_known_pct | 47.49 | 47.03 | - |

The three clean-SFT bases span 87.02-89.92 recall / 10.08-12.98 answer-on-unknown. Seed 3 sits between seeds 1 and 2 on both, so the denominator is unremarkable and in-family; no base anomaly to flag before the GRPO comparison.

**What G1 now requires of this seed.** G1 is a direction-plus-floor test against this same-seed base: `answer_on_unknown_pct` must DECREASE by >= 3.0 pp and `refusal_recall_pct` must INCREASE by >= 3.0 pp. Against the seed-3 base that means `clean_sft_grpo_v2` at seed 3 must reach **answer-on-unknown <= 8.72** and **refusal recall >= 91.28**. Recording these thresholds NOW, before the arm is trained, so the comparison cannot drift after the number is seen. Seed-1 reference effect was +-6.39 pp; seed-2 leg passed at +-4.36 pp.

Stage 2 released to executor6, serial per launch_order: `clean_sft_dpo`, then `clean_sft_kto`, then `clean_sft_grpo_v2`, each from merged(clean_sft) seed 3, each train -> merge -> smoke -> full eval before the next launches. Registered values unchanged from seed 2 (DPO bs2/ga4/lr5e-6/beta0.1; KTO bs12/ga1/lr1e-6/beta0.1 with the authorized step-250 batch-8 fallback; GRPO per_device 32 / num_generations 4 / reward v2, and the GRPO config must carry the ABSOLUTE in-container reward path).

## 2026-08-05 ~19:14Z — Seed-3 stage-2 DPO training COMPLETE; closeout released

Container `eh-grpo3seed-3-clean_sft_dpo-train-20260805T174811Z` exit 0 (container code read from watch stdout), ~1h25m, matching the seed-2 DPO precedent. Lead-verified from `schema_clean_sft_dpo_seed3_full/20260805_174834`: training_type DPO; base_model = the seed-3 merged base (`sft_schema_clean_seed3_full/20260805_163620/Qwen3-4B-bnb-4bit/merged-16bit`), correct same-seed source; seed 3; batch 2 / accum 4 / lr 5e-6 / beta 0.1; train_examples 14943 (frozen count); 1868 steps; final loss 0.04916 (seed-2 was 0.04620 — in family); `final_model` and `training_lineage.json` present. **G0 `training_completed_clean`: PASS.**

Note on the mid-run loss reading: at step 1005 the JSONL reported `loss: 0.0`, which is expected for DPO in this setup rather than a defect — the objective drives toward zero as the policy separates chosen from rejected, and both prior DPO-family runs finished near it (seed-2 DPO 0.0462, seed-2 grpo_dpo 0.0419). Recorded because a zero mid-run loss reads alarming out of context; the final value and the eval are what matter.

Config-construction note: the DPO trainer takes CLI flags rather than a config file, so there was no config to clone. Executor6 reconstructed the seed-3 invocation from `train_dpo.py` argparse plus the seed-2 lineage record, changing only `--model-name`, `--seed`, and `--output-root`, and verified against `Trainers/dpo/configs/config.yaml` that the trainer's baked-in LoRA defaults (r 32 / alpha 64 / dropout 0.05 / random_state 3407 / seven target modules) already equal the seed-2 precedent, so no LoRA flags were passed. Lineage confirms all registered values landed correctly.

Containment note: the DPO trainer's stock dry-run banner prints two raw dataset rows to container stdout via its own `print_dataset_samples`. This is built-in trainer behavior, not introduced by this chain; the row text was not copied, repeated, or persisted anywhere, and nothing row-level entered a tracked path. Flagged so the behavior is on record for a public repo.

Closeout released: merge, 192-row bounded smoke, then full 3,369-row eval with the ADAPTER on the seed-3 merged base per the lineage convention.

## 2026-08-05 ~20:02Z — Seed-3 stage-2 DPO CLOSED (G0 PASS); KTO released

Full eval `eh-grpo3seed-3-clean_sft_dpo-fulleval-20260805T192517Z` exit 0. Lead-verified from `results_grpo3seed_response_confidence_selfaware_clean_sft_dpo_seed3_full_4b`: n=3369 (2337 known / 1032 unknown), answer coverage 3369/3369, stated-confidence 3369/3369, thinking-tag hits 0, row `model` field uniformly `qwen3-4b-clean-schema-sft-merged-seed3` (correct: adapter on the seed-3 SFT merged base, not the newly merged DPO checkpoint). Bounded smoke 192/192/192/0 with model field `qwen3-4b-clean-sft-dpo-merged-seed3`, lead re-derived. Merged shard bytes independently confirmed at 4,967,215,360 + 3,077,766,632. **G0 for this cell: PASS.**

Headline: refusal_recall 85.27, answer_on_unknown 14.73, over_refusal 54.64, truthful 40.19, correct_on_known 44.72.

DPO across seeds (descriptive, no gate involves this arm alone):

| | seed 2 | seed 3 |
| --- | --- | --- |
| recall | 89.34 | 85.27 |
| ans-on-unknown | 10.66 | 14.73 |
| over-refusal | 55.97 | 54.64 |
| truthful | 41.32 | 40.19 |

Both seeds show the same qualitative pattern relative to their own base: DPO moves abstention slightly the WRONG way (base 89.92 -> 89.34 at seed 2; base 88.28 -> 85.27 at seed 3) while buying an over-refusal reduction. The seed-3 movement is larger in both directions than seed-2's. This is the contrast the block exists to set up against GRPO, and it is reported descriptively; no registered gate compares stage-2 DPO to its base.

Operational record from this closeout, both executor6's own invocation errors and both caught and reported by it rather than retried silently: (1) the merge must run with `-w /workspace/repo/synaptic-tuner` because `shared/` lives under the submodule, not the repo root; running from repo root fails with `ModuleNotFoundError: No module named 'shared'`. (2) `merge_lora_checkpoint` types `lora_path`/`output_path` as `Path`, so raw strings fail with `AttributeError: 'str' object has no attribute 'mkdir'`. Both failed before writing any output; no partial artifact was produced, verified. Worth folding into `local-runtime.md` at the next skill pass, together with the observation that the polling backup monitor reports `gone` when a container is pruned before its next poll (the primary `docker wait` remains authoritative for exit codes).

Stage 2 arm 2 released: `clean_sft_kto` from the seed-3 merged base, registered bs12 / ga1 / lr1e-6 / beta0.1, dry-run first, with the authorized step-250 batch-8 fallback to be reported rather than taken silently.

## 2026-08-05 ~19:58Z — Seed-3 stage-2 KTO launched; LoRA-default divergence CAUGHT before launch

`eh-grpo3seed-3-clean_sft_kto-train-20260805T195707Z` launched from the seed-3 merged base. Registered values per cell.yaml `clean_sft_kto`: batch 12 / accum 1 / lr 1e-6 / beta 0.1, 1 epoch. Dataset verified 29,886 rows at exactly 14,943 / 14,943 desirable/undesirable (1.00:1).

**Near-miss worth recording in full.** Executor6 found that the KTO trainer's baked-in LoRA defaults do NOT match this program's registered values, unlike DPO's. Lead-verified independently:

| source | rank | alpha | dropout |
| --- | --- | --- | --- |
| `Trainers/kto/configs/config.yaml` baked-in default | **64** | **128** | 0.05 |
| seed-2 KTO `training_lineage.json` (the precedent) | 32 | 64 | 0.05 |
| seed-2 DPO `training_lineage.json` | 32 | 64 | 0.05 |

The DPO trainer's defaults DO equal the registered values, so the pattern established one arm earlier ("defaults already match, pass no LoRA flags") would have been wrong here. Carrying it over would have trained seed-3 KTO at rank 64 / alpha 128 — double the adapter capacity, an unregistered divergence that would have silently invalidated this arm and the `clean_sft_kto_grpo` stack built on it, while every other check (dataset counts, batch, LR, beta, seed, source model) still passed. Executor6 instead inferred that the seed-2 launch must have passed explicit `--lora-r 32 --lora-alpha 64 --lora-dropout 0.05`, did the same, and confirmed rank 32 / alpha 64 / dropout 0.05 in the dry-run banner before the real launch. `random_state` left at the trainer baseline 3407, matching precedent.

**Durable lesson: trainer defaults are not a substitute for registered values, and a default that matched on one trainer says nothing about the next.** Verify each trainer's effective LoRA configuration against the same-arm lineage precedent every time, and confirm it in the dry-run banner before the real launch. This is exactly the failure mode a dry-run is for. To be folded into `local-runtime.md` at the next skill pass, alongside the merge cwd/Path gotchas.

Verification to perform at closeout: confirm this run's `training_lineage.json` lora block reads rank 32 / alpha 64 / dropout 0.05, not the trainer default.

Step-250 VRAM recheck (authorized batch-8 fallback) is lead-watched via a single-fire JSONL watch; the fallback will be reported and decided, never taken silently.

## 2026-08-05 ~20:08Z — Seed-3 KTO step-250 capacity recheck: LEAD RULING, fallback NOT taken

The `clean_sft_kto` arm carries a pre-registered `capacity_watch` in cell.yaml: at a step-250 recheck, if VRAM pins, fall back to batch 8. That recheck is now due and adjudicated.

Reading at step 250 (from the run's own JSONL, `schema_clean_sft_kto_seed3_full/20260805_195738`): **gpu_memory_reserved 17.398 GB, 72.49% reserved, `oom_risk_level: low`**, loss 0.4624, 606 s elapsed.

Seed-2 precedent for the same arm: 12.055 GB / 50.23% at step 300 with `oom_risk_level: moderate`, and a whole-run peak of **95.92%** — that run completed clean at batch 12.

**RULING: the fallback is NOT taken. Training continues at the registered batch 12.** The trigger condition is VRAM *pinning*, and 72.49% reserved with the profiler reporting low OOM risk is not pinning. The seed-2 run reached 95.92% on this same arm and finished, so the registered batch is demonstrably viable here. Taking a pre-registered fallback that the condition does not call for would be an unforced divergence from the registered value, not a safety measure.

Recorded honestly: seed 3 is running HIGHER at this point in the run than seed 2 was (72.49% at step 250 vs 50.23% at step 300). If the trajectory scales similarly it will exceed seed-2's 95.92% peak, and the neighbouring stage-3 arm `clean_sft_grpo_kto` already peaked at 99.2% at seed 2. So an OOM later in this run is a live possibility. That does not change the step-250 ruling, which is made on the step-250 condition as registered. If the run does OOM, that is a G0 `training_completed_clean` failure handled the same way as the seed-3 stage-1 CUDA crash: instrument stop, diagnose, relaunch — and at THAT point the batch-8 fallback becomes the appropriate pre-registered repair, because the condition would then have actually been met.

**Addendum, step 430 (~20:15Z):** the concern flagged above does not materialize. `max_gpu_memory_reserved_pct` (the trainer's own running high-water mark) still reads **72.49%** at step 430 of 2491, i.e. the step-250 value WAS the peak and has not been exceeded in the following 180 steps; the instantaneous reading at 425 had fallen to 54.53%. So the step-250 number was a transient allocation spike tied to batch content length, not the start of a rising trajectory toward seed-2's 95.92%. No OOM concern, no fallback, no change to the plan. Pace 2.54 s/step, projecting KTO training completion around 21:35Z.

## 2026-08-05 21:39Z — Seed-3 stage-2 KTO training COMPLETE, clean

Container `eh-grpo3seed-3-clean_sft_kto-train-20260805T195707Z` exited **0** at 21:39:05Z. Read from the docker-wait OUTPUT FILE, per the standing rule that a background wait task's own reported exit status is the status of the wait command and not of the container.

Training facts, verified directly from artifacts rather than from the executor's report:

- `results.final_step` 2491 of 2491, `total_epochs` 1.0, `final_loss` 0.0896, `training_time` 1h 39m 56s, `runtime.status` "completed".
- `final_model/` carries `adapter_model.safetensors` + `adapter_config.json` + tokenizer files; `training_lineage.json` present. G0 `training_completed_clean` satisfied for this cell.
- `model.base_model` points at the seed-3 stage-1 merged-16bit (`sft_schema_clean_seed3_full/20260805_163620/.../merged-16bit`), so merge-first lineage holds.
- `dataset.train_examples` **29886**, matching the frozen KTO count in the audit.
- `training.seed` 3, `batch_size` 12, `learning_rate` 1e-06, `beta` 0.1, desirable/undesirable weight 1.0/1.0.

**The near-miss check clears.** `training_lineage.json` `lora` reads **rank 32, alpha 64, dropout 0.05**, and `final_model/adapter_config.json` independently reads `r: 32, lora_alpha: 64, lora_dropout: 0.05`. The KTO trainer's baked-in defaults of r64/alpha128 did NOT leak through. The explicit `--lora-r 32 --lora-alpha 64 --lora-dropout 0.05` flags did their job. Two independent artifacts agree, which is the standard this check should be held to going forward, since the lineage file and the adapter config are written by different code paths.

**Replication health.** Seed-3 loss tracks seed-2 closely across the run: step 250 0.4624 vs 0.4693, step 425 0.2307 vs 0.2334, step 500 0.1280 vs 0.1050, step 750 0.0269 vs 0.0401, step 890 0.0116 vs 0.0089. Both runs report the same 2491 total steps, which independently confirms the frozen dataset and step budget resolved identically across seeds.

**Capacity, closing the thread opened at step 250.** Final peak was **92.25%**, against seed-2's 95.92% on the same arm. So the late spike I speculated about DID occur: the 72.49% plateau that held flat from step 250 through step 890 was not the whole story, and KTO's high-water mark on this arm arrives late in the run. My step-250 ruling was correct on its own terms and the fallback was correctly not taken, but the intermediate reassurance I recorded at step 430 (reading the flat plateau as evidence the peak was already in) was reasoning past the evidence. A flat high-water mark over 640 steps bounds what has happened, not what will. The useful generalization for this arm type: judge KTO capacity risk against the seed-2 whole-run peak, not against any mid-run plateau.

Dispatched to executor6 for closeout (merge, 192-row smoke, full eval on the source merged base per the terminal-arm lineage convention). Nothing about G0 beyond `training_completed_clean` is adjudicable for this cell until smoke lands.

## 2026-08-05 ~21:50Z — G0 ADJUDICATED **PASS**: seed 3, cell `clean_sft_kto`

Adjudicated against `gates.yaml` read at adjudication time, sha256 `7c79a41894a1fc64df01f07bbb197f8c25239d8625e3d9f3d8bbc97d3e51c0fa`, byte-identical to the signed `experiment.yaml` pin. All five checks verified by the lead from artifacts, not relayed from the executor's report.

| check | verdict | evidence |
|---|---|---|
| `merge_first_lineage` | PASS | `training_lineage.json` `model.base_model` = `sft_schema_clean_seed3_full/20260805_163620/.../merged-16bit`, a merged source model, not the foundation and not an adapter path |
| `bounded_smoke_coverage` | PASS | 192 rows: `generated_answer` present 192/192, `stated_confidence` present 192/192 (`coverage_pct` 100.0, `n_missing_confidence` 0), thinking-tag hits **0** on a substring scan for `<think>` / `</think>` / `reasoning_content`, `enable_thinking` uniformly False |
| `training_completed_clean` | PASS | exit 0, `runtime.status` "completed", `final_step` 2491/2491, `final_model/adapter_model.safetensors` + `adapter_config.json` present, `training_lineage.json` present |
| `dataset_audit_matches_frozen` | PASS | `dataset.train_examples` **29886**, matching the KTO count this amendment freezes |
| `containment` | PASS | nothing staged; untracked files in the worktree are eval configs and the seed-3 SFT config only. Weights, merged checkpoints, and scored rows all confirmed gitignored |

Merge verified independently: shard bytes **4,967,215,360** and **3,077,766,632**, exact match to the standard merged-16bit sizes.

Containment note worth recording, because the first probe looked alarming. `git check-ignore` initially reported the not-yet-created full-eval results directory as NOT ignored, which would have been a real hole on a public repo. It is not one. The rule is `archive/experiment/phase1/eval/.gitignore:9: results_*/`, and the trailing slash means the pattern needs a directory to match; probing a path that does not exist yet cannot confirm directory-ness, so the rule silently fails to fire. Probing a hypothetical file INSIDE that directory matches the rule correctly. The generalizable lesson: when checking containment for an output path that has not materialized yet, probe a hypothetical file inside it, never the bare directory, or a trailing-slash ignore rule will read as absent.

**Not read as outcome.** The smoke run also emits outcome-shaped metrics (`refusal_recall_pct` 80.0, `over_refusal_pct` 58.76, `answer_on_unknown_pct` 20.0, `truthful_pct` 46.88 at n=192). G0 is `stop_before_outcome`, and 192 rows is an instrument check, not an outcome sample. These numbers are recorded as instrument telemetry only and are NOT evidence toward G1 or G2, which read the 3,369-row full eval.

Full eval launched detached at 21:47Z, container `eh-grpo3seed-3-clean_sft_kto-fulleval-20260805T214718Z`, adapter-on-source-base per the terminal-arm lineage convention (verified: eval `model_name` equals this run's `training_lineage.json` `model.base_model`; `adapter` = the KTO `final_model`). Dual watches armed.

Lead error corrected for the record: my closeout dispatch told the executor to dry-run the eval launch. `run_eval.py` exposes no `--dry-run`; that flag exists only on the SFT/DPO/KTO/GRPO trainers. The executor flagged it rather than improvising a substitute, which is the correct handling.

## 2026-08-05 ~21:55Z — G1 seed-3 thresholds PRE-STATED (recorded before the deciding result exists)

Written while `clean_sft_grpo_v2` seed 3 has not been trained, let alone evaluated. The point of recording now is that a threshold stated after seeing the number is not a threshold.

G1 text, read verbatim from `gates.yaml` at sha256 `7c79a41894a1fc64df01f07bbb197f8c25239d8625e3d9f3d8bbc97d3e51c0fa`: comparison `clean_sft_grpo_v2` vs same-seed `clean_sft_merged`, `requires_same_seed_denominator: true`, conditions `answer_on_unknown_pct` decrease >= 3.0 pp AND `refusal_recall_pct` increase >= 3.0 pp, `pass_if` both hold in BOTH seeds, `not_confirmed_if` either seed shows a sign flip or a movement smaller than 3.0 pp on either metric.

**Seed-3 denominator**, read from the artifact rather than from prose: `results_grpo3seed_..._clean_sft_seed3_merged_full_4b/clean_schema_sft_merged_seed3__selfaware/metrics.json`, n=3369, `refusal_recall_pct` **88.28**, `answer_on_unknown_pct` **11.72**.

**Therefore the seed-3 G1 leg passes if and only if, at n=3369:**
- `answer_on_unknown_pct` <= **8.72** (11.72 minus the 3.0 pp floor), AND
- `refusal_recall_pct` >= **91.28** (88.28 plus the 3.0 pp floor).

Any value strictly inside that band is `not_confirmed`, which under a falsifier gate is a real result and gets reported as one. Seed 2 for reference already cleared its own band: base 89.92 / 10.08 against grpo_v2 94.28 / 5.72, a movement of 4.36 pp on both metrics.

### The two G1 conditions are one measurement stated twice

Checked across all 21 eval runs in this block, smoke and full: `refusal_recall_pct + answer_on_unknown_pct = 100.00` exactly, in every single run, with no exceptions. On unknown-labelled questions the instrument admits exactly two outcomes, refuse or answer, so the two rates are exact complements by construction.

The consequence for reading G1: its two conditions are not two independent pieces of evidence. A 3.0 pp fall in unknown answering IS a 3.0 pp rise in refusal recall, necessarily, on the same rows. The gate cannot fail one condition and pass the other, and the "both conditions" phrasing conveys no more confirmatory weight than either condition alone. G1 is, in substance, a single-condition direction-plus-floor test on one quantity.

This is recorded as interpretation, and it changes NOTHING about the gate. The comparison, the 3.0 pp floor, the both-seeds requirement, and the pass/not-confirmed rule all stand exactly as signed, and the seed-3 band above is computed from them as written. The reason to record it is that when the verdict is written up, G1 should not be described as two corroborating findings; describing it that way would overstate the evidence. It also means the seed-1 derivation in the gate text ("-6.39 pp answer-on-unknown and +6.39 pp refusal recall") is one effect reported twice, which is consistent with the identical magnitudes.

Flagging for the red-team pass at resolve time rather than acting on it now.

## 2026-08-05 ~22:05Z — Seed-3 `clean_sft_grpo_v2` config PREPARED and lead-verified (pre-launch, not yet launched)

CPU-only prep while the KTO full eval held the GPU. Nothing launched. Recorded before the launch verb, per the launch guard.

**Structured diff re-derived by the lead**, not accepted from the report: `yaml.safe_load` + flattened key comparison of the seed-3 config against seed 2. 63 keys on both sides, symmetric difference of the key sets EMPTY, exactly **4** differing values, all seed-scoped:

| key | seed 2 | seed 3 |
|---|---|---|
| `seed` | 2 | 3 |
| `lora.random_state` | 2 | 3 |
| `model.model_name` | `sft_schema_clean_seed2_full/20260731_232307/.../merged-16bit` | `sft_schema_clean_seed3_full/20260805_163620/.../merged-16bit` |
| `training.output_dir` | `schema_clean_sft_grpo_v2_seed2_full` | `schema_clean_sft_grpo_v2_seed3_full` |

Registered values confirmed intact in the seed-3 file: `lora.r` 32, `lora.lora_alpha` 64, `lora.lora_dropout` 0.05, `per_device_train_batch_size` 32, `num_generations` 4 (cell.yaml :88-96; AMENDMENT.md frozen input 15 :305-309). Base checkpoint exists on disk. GRPO datasets verified from three independent sources that agree: `grpo_train.jsonl` 14888 lines, `grpo_dev.jsonl` 1655 lines, and `grpo_manifest.json` stating train_rows 14888 / dev_rows 1655, all matching the amendment-frozen counts. Reward file `humility_reward_v2.py` present at the config's resolved path.

**`lora.random_state: 3` verified against the record, not assumed.** The 2026-07-31 LEAD RULING entry ("lora.random_state mirrors the seed number") is present in this NOTEBOOK, and a later entry sharpens it: the DPO/KTO trainers expose no `--lora-random-state` flag, so those stages use the trainer baseline 3407, and the seed-mirroring ruling applies only where a config file carries `lora.random_state`, namely SFT and GRPO. The GRPO config does carry it, so 3 is correct here, and the DPO/KTO 3407 baseline already used this seed is also correct. Two different conventions, both intentional.

**Lead instruction error, third this cycle, corrected by the executor.** My prep dispatch told it to pass `--lora-r / --lora-alpha / --lora-dropout` explicitly, generalizing the KTO fix. That is not applicable: `train_grpo.py` is YAML-driven, and its entire CLI surface is `--config / --dry-run / --resume-from-checkpoint / --model-name / --dataset-name / --dataset-file / --local-file / --use-gspo / --pivot-profile-only` (:156-168). There are no LoRA, seed, batch, or LR flags to pass; every hyperparameter lives in the YAML. So the correct safety check for GRPO is not "pass explicit flags" but "read the resolved values in the YAML", which is what was done. Noting the pattern: the anti-defaults lesson from KTO is real, but its MECHANISM is trainer-specific, and I twice tried to port a mechanism rather than the principle. The portable principle is "verify resolved hyperparameters against the registered spec by whatever route that trainer exposes."

For completeness, the GRPO trainer's baked-in defaults are r32 / alpha64 / dropout 0.05, which happen to match the registered spec (unlike KTO's r64/alpha128). Moot here, since the YAML sets every value explicitly.

**Known limitation, honestly flagged rather than papered over.** The two eval configs cannot be fully resolved yet: both need the run-directory timestamp the GRPO trainer generates at launch. They were written with every other field resolved and an explicit `<SEED3_GRPO_V2_TIMESTAMP>` placeholder plus a notice block, rather than a guessed timestamp. They get finalized after training and merge, exactly as the DPO and KTO eval configs did. The full-eval `model_name` (seed-3 SFT merged base) IS fully resolved, since that checkpoint exists; only the adapter path carries the placeholder.

Launch is HELD pending: KTO full eval completing (one GPU job at a time), and lead clearance.

## 2026-08-05 ~22:05Z — Seed-3 stage-3 configs PREPARED for `clean_sft_dpo_grpo` and `clean_sft_kto_grpo` (pre-launch)

CPU-only prep during the KTO full eval. Nothing launched. Scope deliberately excluded `clean_sft_grpo_dpo` and `clean_sft_grpo_kto`, which train from merged(`grpo_v2`) and therefore cannot have resolved configs yet; leaving placeholder-bearing TRAINING configs on disk for unlaunchable arms is an invitation to launch one by mistake.

Registered spec read at cell.yaml :98-115 and AMENDMENT.md :128-129, which confirm stage 3, terminal true, sources merged(`clean_sft_dpo`) and merged(`clean_sft_kto`) respectively, trainer `train_grpo.py`, dataset grpo, reward_variant v2, batch 32, num_generations 4.

**Lead-re-derived diffs**, both arms, `yaml.safe_load` + flatten:

| arm | keys | keyset diff | differing keys |
|---|---|---|---|
| `clean_sft_dpo_grpo` | 63 / 63 | none | 4, all seed-scoped |
| `clean_sft_kto_grpo` | 63 / 63 | none | 4, all seed-scoped |

Both carry `lora.r` 32, `lora_alpha` 64, `lora_dropout` 0.05, `lora.random_state` 3, batch 32, num_generations 4.

**The check that mattered here was lineage, and it holds.** These two arms have DIFFERENT sources from each other and from `grpo_v2`, so a cross-wire would be the easy mistake and would be nearly invisible downstream: the run would train and evaluate cleanly while measuring the wrong stack. Verified separately, each pointing where it should and each existing on disk with `config.json` present:

- `clean_sft_dpo_grpo` -> `schema_clean_sft_dpo_seed3_full/20260805_174834/Qwen3-4B-clean-sft-dpo/merged-16bit`
- `clean_sft_kto_grpo` -> `schema_clean_sft_kto_seed3_full/20260805_195738/Qwen3-4B-clean-sft-kto/merged-16bit`

Both are merged-16bit directories, not adapter paths and not the SFT base, satisfying G0 `merge_first_lineage` in advance. The KTO source is the checkpoint merged at 21:40Z earlier today.

Reward file `archive/experiment/phase1/grpo/humility_reward_v2.py` present in both, defining `epistemic_humility_reward` at :197, matching the `functions.name` entry in each config. The stale-reward-path bug recorded for the seed-1 templates did NOT recur: both inherited the corrected absolute in-container path from the seed-2 precedent.

Both files launch-ready with no placeholders. Launch order unchanged and still held: `grpo_v2` first (G1's deciding leg), then these.

## 2026-08-05 22:12Z — Seed-3 `clean_sft_kto` full eval COMPLETE; cell CLOSED

Container `eh-grpo3seed-3-clean_sft_kto-fulleval-20260805T214718Z` exited **0** at 22:12:30Z, read from the docker-wait output file. Artifacts present: `metrics.json` (1426 B), `scored_rows.jsonl` (2,673,254 B), `bootstrap_ci.json`, `summary_table.csv`.

Lead-read from the artifact, n=**3369**:

| metric | value |
|---|---|
| `refusal_recall_pct` | 83.24 |
| `answer_on_unknown_pct` | 16.76 |
| `over_refusal_pct` | 53.87 |
| `truthful_pct` | 39.74 |
| `correct_on_known_pct` | 44.53 |

Confidence coverage 100.0%, 0 missing. Complementarity holds again: 83.24 + 16.76 = 100.00.

This cell is CLOSED with G0 PASS (adjudicated earlier from the smoke and training artifacts). `clean_sft_kto` is not a term in G1 or G2; it enters the block as a stage-2 arm of the descriptive G3 matrix and as the source for `clean_sft_kto_grpo`. No gate is adjudicable from this number and none is claimed.

Seed-3 progress: 3 of 8 arms complete (`clean_sft`, `clean_sft_dpo`, `clean_sft_kto`).

## 2026-08-05 ~22:15Z — `clean_sft_grpo_v2` seed 3 CLEARED FOR LAUNCH (G1 deciding leg)

Recorded BEFORE the launch verb, per the launch guard.

Preconditions checked: GPU free (KTO full eval terminated, exit 0, artifacts verified); config `grpo_schema_clean_sft_merged_seed3_v2_full.yaml` prepared and lead-verified (63 keys, 4 seed-scoped differences, registered values intact, base checkpoint on disk); datasets verified 14888 / 1655 against three agreeing sources; reward file resolves. User green-light for the seed-3 chain stands.

**What this run decides.** G1 is the primary falsifier gate and requires both conditions in BOTH seeds. Seed 2 passed (base 89.92 / 10.08 vs grpo_v2 94.28 / 5.72, a 4.36 pp movement). Seed 3 therefore decides G1 outright. The band was pre-stated at ~21:55Z, before this run existed, against the seed-3 denominator 88.28 / 11.72:

- PASS requires `answer_on_unknown_pct` <= **8.72** AND `refusal_recall_pct` >= **91.28**.
- Anything strictly inside that band is `not_confirmed`, and under a falsifier gate that is a reportable result, not a prompt to reconsider the threshold.

Since the two G1 metrics are exact complements on this instrument (verified across 21 runs), these two criteria are one test, and they will pass or fail together. The verdict will be written that way.

No goalpost may move from here in either direction. The threshold is fixed, the denominator is fixed, and both were fixed before the deciding data existed.

## 2026-08-05 22:17:19Z — `clean_sft_grpo_v2` seed 3 LAUNCHED (G1 deciding leg)

Container `eh-grpo3seed-3-clean_sft_grpo_v2-train-20260805T221719Z`, started 22:17:19Z, run directory `schema_clean_sft_grpo_v2_seed3_full/20260805_221744`.

Preflight passed twice (before dry-run and before the real launch): pinned digest matched char-for-char, GPU idle 0MiB/0%, 160G free.

Dry-run resolved values, reported from the trainer's banner: model = the seed-3 SFT merged base, LoRA rank 32 / alpha 64 / dropout 0.05 across q,k,v,o,gate,up,down_proj, reward `epistemic_humility_reward` weight 1.0 loaded, dataset **14888** examples formatted 14888/14888 matching the frozen count, batch 32 x grad-accum 1, 4 generations per prompt, max prompt 512, max completion 128, LR 5e-6.

**A gap the executor flagged rather than papered over, now closed by the lead.** The GRPO trainer's dry-run banner does not print `seed` or `lora.random_state` at all; the executor said so explicitly instead of implying it had confirmed them, which is the correct handling and is worth recording as such. Its reasoning that the values are correct by construction (GRPO is YAML-driven, the trainer exposes no `--seed` or LoRA flags, so the config file is the only route those values can reach the trainer) is sound but is an argument, not an observation. Closed with direct observation:

- `docker inspect` of the RUNNING container: image is `sha256:f21629b9ae4ed11231768edfaed0f40d41d85d6ea9a71e8096a3d96ea0311772`, identical to the pin, and `Config.Cmd` is `["train_grpo.py","--config","/workspace/repo/experiments/grpo-three-seed-confirmatory/configs/grpo_schema_clean_sft_merged_seed3_v2_full.yaml"]`.
- That host path, read directly: `seed: 3`, `lora.random_state: 3`, `r: 32`, `lora_alpha: 64`, `lora_dropout: 0.05`, model = seed-3 SFT merged base, output_dir = the seed-3 grpo_v2 run root.

So the file actually passed to the actually-running pinned image carries the seed-scoped values. Re-verify at closeout against `training_lineage.json`, which is written from the resolved config and is the artifact of record.

**Containment note worth carrying forward.** The GRPO trainer calls `print_dataset_samples` and prints two full raw dataset rows (prompt, id, label) to stdout as stock behavior. That means this container's `docker logs` output CONTAINS question text. The repo is public. Consequence: never paste `docker logs` for a GRPO container into the repo, a report, a commit message, or an issue, and never redirect that stdout to a tracked path. Nothing was persisted here. Candidate for the local-runtime skill at the next doc pass.

Minor, recorded so it is not mistaken later for the real run: the dry-run left an empty run directory at `schema_clean_sft_grpo_v2_seed3_full/20260805_221623` containing only empty `checkpoints/` and `logs/` subdirs. The real run is `20260805_221744`.

Dual watches armed. Expect a long run; the seed-1 GRPO precedent in the archive notes ran roughly 6.8h. No result is adjudicable until the full eval, and the G1 band stands as pre-stated: PASS iff `answer_on_unknown_pct` <= 8.72 AND `refusal_recall_pct` >= 91.28.

## 2026-08-05 ~22:30Z — Containment audit: training-container stdout carries row text (ALL FOUR trainers), repo clean

Follow-up to the launch note above, and a correction to it. I recorded the sample-printing behavior as a GRPO property. It is not. Verified at the source: four SEPARATE per-trainer `print_dataset_samples` implementations, each called on that trainer's real training path with `num_samples=2`:

| trainer | defined | called |
|---|---|---|
| SFT | `Trainers/sft/src/data_loader.py:240` | `train_sft.py:965` |
| KTO | `Trainers/kto/src/data_loader.py:340` | `train_kto.py:678` |
| DPO | `Trainers/dpo/src/data_loader.py:157` | `train_dpo.py:477` |
| GRPO | `Trainers/grpo/src/data_loader.py:93` | `train_grpo.py:337` |

All four call sites verified verbatim by the lead. So every training container in this block, including the seed-3 SFT, DPO, and KTO runs already completed, has question text in its `docker logs`. A fifth unused copy exists in the `mlx_sft_mac` lane with no call site.

**Audit result: the repo is CLEAN.** No pasted trainer stdout exists in any tracked file on `main` or on `exp/grpo-three-seed-run`. The distinctive markers (`Dataset samples`, `ground_truth_args_json`, sample-block headers) return zero hits. Nothing needs remediation.

The rule is now written into `.skills/experiment-runner/reference/local-runtime.md` (PR #392): never paste `docker logs` from ANY training container into the repo, a commit message, a PR body, an issue, or an agent report; never redirect that stdout to a tracked path; evidence a launch with `docker inspect` plus `training_lineage.json`, which carry no row text. That is what was done for this launch, before the hazard was known, which is luck rather than discipline and is exactly why it is now written down.

**Lead process error in the audit itself, recorded because it is the same class of mistake.** My first audit pass grepped the whole tree for loose patterns including `chosen:` and `rejected:`, which matched the tracked `datasets/sycophancy-eval/*.jsonl` files and pulled a large volume of question text into the session context. Nothing was written anywhere and those files are pre-existing tracked public eval data, so there is no leak. But the correct audit is scoped to docs and notebooks using only the distinctive trainer-output markers. Searching broadly for row text is itself a way to spread row text, and a public repo makes the blast radius of a careless grep larger than it looks.

## 2026-08-06 05:39Z / 10:25Z — Seed-3 `clean_sft_grpo_v2` trained and merged; **G0 PASS**; full eval running (G1 deciding)

Training container `eh-grpo3seed-3-clean_sft_grpo_v2-train-20260805T221719Z` exited **0** at 05:39:11Z, 7h22m, confirmed by both watches.

Lead-verified from artifacts: `model.base_model` = seed-3 SFT merged base, `training.seed` **3**, batch 32, `num_generations` 4, LR 5e-6, beta 0.1, `dataset.train_examples` **14888**, `results.final_step` **1861**, epochs 1.0, final_loss 0.1059. LoRA reads **rank 32 / alpha 64 / dropout 0.05** in `training_lineage.json` AND independently in `final_model/adapter_config.json`. The 1861 steps match the seed-1 GRPO precedent.

Note on what the lineage cannot show: the GRPO `lineage.lora` block carries rank/alpha/dropout/target_modules/bias but NOT `random_state`, and `runtime` is null for this trainer (schema difference, not a failure). `random_state: 3` was verified pre-launch instead, by reading the exact config file named in the running container's `Config.Cmd`.

Merge clean on the first attempt, shard bytes **4,967,215,360** and **3,077,766,632**, exact.

### G0 ADJUDICATED **PASS** for seed 3, cell `clean_sft_grpo_v2`

| check | verdict | evidence |
|---|---|---|
| `merge_first_lineage` | PASS | base_model = `sft_schema_clean_seed3_full/20260805_163620/.../merged-16bit` |
| `bounded_smoke_coverage` | PASS | 192 rows, `generated_answer` 192/192, `stated_confidence` 192/192 (`coverage_pct` 100.0, `n_missing` 0), thinking-tag hits **0**, `enable_thinking` uniformly False |
| `training_completed_clean` | PASS | exit 0, final_step 1861, `final_model/adapter_model.safetensors` + `adapter_config.json` + `training_lineage.json` present |
| `dataset_audit_matches_frozen` | PASS | `train_examples` **14888**, matching the frozen GRPO train count |
| `containment` | PASS | nothing staged; untracked files are eval configs only |

### The placeholder trap was real, and it was avoided

The two eval configs carried a literal `<SEED3_GRPO_V2_TIMESTAMP>` placeholder because the run directory could not be known before launch. Two things could have gone wrong and neither did.

First, the executor's initial substitution left the token surviving in its own comment prose; it caught that itself, fixed it, and re-verified to a zero-match grep across all four file locations. Verified: no placeholder token survives.

Second and more serious, the dry-run had left an empty directory at `20260805_221623` alongside the real run at `20260805_221744`. I checked both: the real run's `final_model/adapter_model.safetensors` is **264,308,896 bytes**, and the dry-run leftover has **no adapter at all**. Had the wrong timestamp been substituted, the eval would have loaded no adapter and measured the bare SFT base while producing a perfectly well-formed G1 number. That failure mode is invisible in the output; it is only catchable at the path. Recorded as a standing hazard for any arm whose eval config is written before its training run exists.

Full eval launched 10:25:00Z, container `eh-grpo3seed-3-clean_sft_grpo_v2-fulleval-20260806T102500Z`. Lead-verified before recording: running image digest matches the pin, `Config.Cmd` names the intended config, `model_name` = the seed-3 SFT merged base (adapter-on-source-base per the terminal-arm convention), adapter = the real `20260805_221744/final_model`. Dual watches armed.

**No G1 verdict is available yet and none is implied.** The band stands exactly as pre-stated on 2026-08-05 at ~21:55Z, corroborated today by AMENDMENT.md:412 which states the same rule independently of gates.yaml: PASS iff `answer_on_unknown_pct` <= **8.72** AND `refusal_recall_pct` >= **91.28**.

## 2026-08-06 10:55Z — **G1 ADJUDICATED: PASS** (primary falsifier gate survives; replication confirmed)

Full eval `eh-grpo3seed-3-clean_sft_grpo_v2-fulleval-20260806T102500Z` exited **0** at 10:55:23Z, both watches agreeing. n=**3369**, confidence coverage 100.0%.

Adjudicated against the band pre-stated 2026-08-05 ~21:55Z, before this run existed, and corroborated by AMENDMENT.md:412 stating the same rule independently of gates.yaml.

| seed | metric | base | grpo_v2 | delta | required | verdict |
|---|---|---|---|---|---|---|
| 2 | `answer_on_unknown_pct` | 10.08 | 5.72 | **-4.36** | <= -3.00 | PASS |
| 2 | `refusal_recall_pct` | 89.92 | 94.28 | **+4.36** | >= +3.00 | PASS |
| 3 | `answer_on_unknown_pct` | 11.72 | 4.94 | **-6.78** | <= -3.00 | PASS |
| 3 | `refusal_recall_pct` | 88.28 | 95.06 | **+6.78** | >= +3.00 | PASS |

`pass_if` is "both conditions hold in BOTH seed 2 and seed 3". Both hold in both. **G1 PASSES.** The falsifier did not fire; the seed-1 GRPO abstention shift replicates.

Seed-3 magnitude (6.78 pp) is close to seed 1 (6.39 pp); seed 2 (4.36 pp) is the weaker leg. All three clear the 3.0 pp floor. Consistent with the gate's own framing as a direction-plus-floor test, NOT a magnitude-equivalence test.

### How this must and must not be written up

**Not two findings.** Per the complementarity note recorded BEFORE this result, `refusal_recall_pct` and `answer_on_unknown_pct` sum to exactly 100.00 in all 21 runs of this block; they are exact complements on unknown-labelled rows. The identical +/-4.36 and +/-6.78 deltas above are that identity, not corroboration. G1 is one direction-plus-floor test on one quantity, passed in two seeds. Two seeds is the replication; two metrics is not.

**The pass has a cost, and reporting the pass without it would mislead.** Neither of these is a G1 term, and neither changes the verdict, but both are real and consistent across seeds:

| metric | seed 2 | seed 3 |
|---|---|---|
| `over_refusal_pct` | 58.24 -> 66.75 (**+8.51**) | 59.01 -> 68.68 (**+9.67**) |
| `correct_on_known_pct` | 47.03 -> 54.05 (+7.02) | 47.49 -> 55.05 (+7.56) |
| `truthful_pct` | 41.17 -> 41.35 (+0.18) | 40.55 -> 41.08 (+0.53) |

GRPO buys the abstention gain by refusing substantially more overall: over-refusal rises by MORE than the unknown-answering improvement in both seeds. And `truthful_pct` is essentially flat (+0.18, +0.53 pp). So on this instrument the abstention shift is a redistribution of the refuse/answer tradeoff rather than a net truthfulness gain. That is precisely the tension G2 exists to test, and it is why the block does not stop here.

**One instrument question to resolve before any write-up, flagged not assumed.** `over_refusal_pct` and `correct_on_known_pct` both RISE together, which is counterintuitive if both are rates over all known-labelled rows. A plausible explanation is that `correct_on_known_pct` is computed over ANSWERED known rows, so refusing the hard knowns mechanically raises accuracy on what remains. I have NOT verified that, and it materially changes how the +7 pp accuracy figure should be described. Resolve from the scorer source before any of these numbers appear in prose. Do not cite the accuracy gain until then.

Seed 3 is now 5 of 8 arms complete. G2 remains open and needs `clean_sft_grpo_dpo` on seed 3.

## 2026-08-06 ~11:00Z — `clean_sft_dpo_grpo` seed 3 CLEARED FOR LAUNCH (registered order kept)

Recorded before the launch verb.

Considered and REJECTED: reordering the remaining stage-3 arms to run `clean_sft_grpo_dpo` first, which would resolve G2 roughly 24h sooner since G2's open leg is `grpo_dpo` vs `grpo_v2` on seed 3. Rejected because `launch_order` is a REGISTERED field in the signed cell.yaml, listing `clean_sft`, `clean_sft_dpo`, `clean_sft_kto`, `clean_sft_grpo_v2`, `clean_sft_dpo_grpo`, `clean_sft_kto_grpo`, `clean_sft_grpo_dpo`, `clean_sft_grpo_kto`. Run order cannot affect any result here (each arm trains from a fixed merged checkpoint with a fixed seed on frozen data, so the arms are independent given their sources), which means deviating buys no scientific benefit while creating a divergence from a signed value. Getting an answer sooner is not a reason to edit a registered field. Flagged to the user as an available option if they want to authorize the deviation explicitly; proceeding in registered order absent that.

Next arm is therefore `clean_sft_dpo_grpo`, whose config was prepared and lead-verified on 2026-08-05 (63 keys, 4 seed-scoped differences, source = seed-3 DPO merged at `20260805_174834`, verified on disk). Preconditions: GPU free (grpo_v2 full eval exited 0), G0 PASS on its source cell, user green-light for the seed-3 chain stands.

## 2026-08-06 11:13Z — `clean_sft_dpo_grpo` seed 3 LAUNCHED; last two arms specified

Container `eh-grpo3seed-3-clean_sft_dpo_grpo-train-20260806T111330Z`, started 11:13:30Z, run dir `clean_sft_dpo_grpo_seed3_full/20260806_111355`. Lead-verified from the running container: image digest matches the pin, `Config.Cmd` names `grpo_clean_sft_dpo_grpo_seed3_full.yaml`, and that file carries `seed: 3`, `lora.random_state: 3`, source = seed-3 DPO merged at `20260805_174834`. Dry-run confirmed r32/alpha64/dropout 0.05, reward `epistemic_humility_reward`, 14888 examples. Dual watches armed. Dry-run leftover empty dir at `20260806_111245`; the real run is `20260806_111355`.

### Final two arms specified (no config files exist to write, and that is correct)

Registered specs read by the lead from cell.yaml:

| arm | trainer | batch | grad-accum | LR | beta | epochs | source |
|---|---|---|---|---|---|---|---|
| `clean_sft_grpo_dpo` | `Trainers/dpo/train_dpo.py` | 2 | 4 | 5e-6 | 0.1 | 1 | merged(`clean_sft_grpo_v2`) |
| `clean_sft_grpo_kto` | `Trainers/kto/train_kto.py` | 12 | 1 | 1e-6 | 0.1 | 1 | merged(`clean_sft_grpo_v2`) |

Both take the same seed-3 grpo_v2 merged source, verified on disk with `config.json` and standard shard bytes. Datasets re-counted: DPO 14943, KTO 29886, both matching the frozen counts. Planned invocations match the registered values exactly.

Trainer-specific handling confirmed correct for both:
- KTO defaults are r64/alpha128, so `clean_sft_grpo_kto` MUST pass `--lora-r 32 --lora-alpha 64 --lora-dropout 0.05` explicitly. DPO defaults already match, so `clean_sft_grpo_dpo` needs no LoRA flags.
- Neither trainer exposes a random_state flag, so both use the 3407 baseline. The seed-mirroring convention does NOT apply here and must not be "corrected" to 3. This is the split convention recorded on 2026-07-31 and refined later.

### Lead instruction error, FOURTH of the same class this cycle

I asked for "config files" and a "structured diff" for these two arms, and for a reward file path and function name. None of that applies: the DPO and KTO trainers are CLI-flag-driven with no persisted YAML, and the reward-file mechanism is GRPO-only (`rewards.custom`). The executor said so plainly rather than fabricating a config file, inventing a diff, or silently dropping the reward question.

The pattern across all four instances this cycle is identical, and it is now clear enough to name: I keep porting the MECHANISM of a check from the trainer I last dealt with, instead of stating the GOAL and letting the executor pick the mechanism the current trainer actually exposes. Instances: (1) `--dry-run` demanded of `run_eval.py`, which has none; (2) explicit LoRA flags demanded of GRPO, which is YAML-driven; (3) the stdout containment hazard scoped to GRPO when all four trainers do it; (4) config files and reward paths demanded of the CLI-driven DPO/KTO arms.

Durable fix for delegation prompts: specify the INVARIANT to establish ("the resolved hyperparameters must match the registered spec; confirm by whatever route this trainer exposes and tell me which route you used"), never the command to run. Every one of these was caught only because the executor pushed back instead of complying. Carry to the subagent-orchestration skill at the next doc pass.

Launch order for the remainder, registered and unchanged: `clean_sft_kto_grpo`, then `clean_sft_grpo_dpo` (G2's open leg), then `clean_sft_grpo_kto`.
