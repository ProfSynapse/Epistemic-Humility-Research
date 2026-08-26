# prompt-crossing-heldout-confirmatory -- launch sequence

Operating record for the stages in `cell.yaml`. This is a reusable operating
spec, not a claims surface; the signed prose lives in `AMENDMENT.md`, the
machine state in `experiment.yaml`, the pinned thresholds in `gates.yaml`.
Run everything from the canonical checkout
(`/home/profsynapse/code/Epistemic-Humility-Research`); the shell resets its
cwd between calls, so `cd` there explicitly first every time.

GPU launch requires explicit PI approval naming the exact stages. Nothing
below authorizes itself. This cell trains nothing; every stage is either
input staging/verification (CPU) or eval-only generation (GPU, docker).

## Stage 0 -- input staging and verification (CPU, no gate on the stage itself; feeds PH-G0)

This cell reuses the row artifacts and screening already done and adjudicated
by `experiments/ood-breadth-beyond-selfaware/` (resolved 2026-08-09). Nothing
is re-fetched, re-screened, or copied; the screened manifests are read by
path from that cell's gitignored `analysis/screen/` directory, which is
present in the canonical checkout but will be ABSENT in a fresh worktree or
clean clone (same containment posture that cell's own design decision 14
states). If any of the three files below is missing, STOP and re-run that
cell's `screen_ood_surfaces.py` (or restage from wherever the canonical
checkout's `analysis/` tree normally comes from) before proceeding -- do not
re-derive a new screen here.

1. Verify the three screened surface files exist and have the exact row
   counts `cell.yaml surfaces[].rows` states:

   ```
   wc -l experiments/ood-breadth-beyond-selfaware/analysis/screen/ambigqa_validation_screened.jsonl \
         experiments/ood-breadth-beyond-selfaware/analysis/screen/kuq_screened.jsonl \
         experiments/ood-breadth-beyond-selfaware/analysis/screen/bigbench_known_unknowns_screened.jsonl
   ```

   Expected: 1832 / 5540 / 46. Verified at build time (2026-08-17): exact
   match. STOP if any count differs -- do not proceed on a stale or
   re-screened manifest.

2. Verify `archive/experiment/phase1/eval/ood.py` carries the `load_ambigqa`
   and `load_bigbench_known_unknowns` loaders registered under `"ambigqa"`
   and `"bigbench_known_unknowns"` (ood-breadth's deviation D2, additive
   only). Verified at build time by sha256: current file hashes to
   `cfd6cf8be6c0a892056b4b339dd2b8725dc9050c5cf991d8ec184f2b216d7760`, the
   POST-change digest ood-breadth's own RUNBOOK.md stage 1 recorded (not its
   `frozen_inputs.instrument_pre_change` pre-change sha
   `e747f232a73f18080efe80762e84425b188511478b0c733a807044f59ec7c005`).
   `run_eval.py` and `scorers.py` are unmodified since ood-breadth's
   registration (current shas `a77633892e5ba01964728cbabd35df2c48dbbd7eb2d86a779147947b50ac4f85`
   and `75e690f583d83d654cb88a3b066b39acb7e9e1b954c9d5677d4b887d6c30905a`,
   matching `frozen_inputs.instrument_pre_change` exactly). STOP if any of
   the three shas differ -- the harness has changed since this cell's build
   and the config/prompt provenance needs re-verification before launch.

3. Verify every checkpoint path `cell.yaml checkpoints:` names exists on
   disk. Table (verified 2026-08-17 in the canonical checkout; `y` = exists):

   | Checkpoint key | Path (relative to repo root) | Exists |
   |---|---|---|
   | base | `unsloth/Qwen3-4B-bnb-4bit` (HF hub id, not local) | n/a |
   | cold_sft_seed1 | `synaptic-tuner/toolset-training-artifacts/runs/local/4b/sft__4b__headline__seed1/20260614_053221/final_model` | y |
   | cold_sft_seed2 | `synaptic-tuner/toolset-training-artifacts/runs/local/4b/sft__4b__headline__seed2/20260615_090734/final_model` | y |
   | cold_sft_seed3 | `synaptic-tuner/toolset-training-artifacts/runs/local/4b/sft__4b__headline__seed3/20260615_104507/final_model` | y |
   | cold_dpo_seed1 | `.../dpo__4b__headline__seed1_postfix/20260807_192026/final_model` | y |
   | cold_dpo_seed2 | `.../dpo__4b__headline__seed2/20260615_114512/final_model` | y |
   | cold_dpo_seed3 | `.../dpo__4b__headline__seed3/20260615_130441/final_model` | y |
   | cold_kto_seed1 | `.../kto__4b__headline__seed1_postfix/20260807_124416/final_model` | y |
   | cold_kto_seed2 | `.../kto__4b__headline__seed2/20260615_142046_logging_patch/final_model` | y |
   | cold_kto_seed3 | `.../kto__4b__headline__seed3/20260615_204215_logging_patch/final_model` | y |
   | clean_sft_merged_base | `scratch/schema_response_confidence/runs/sft_schema_clean_seed1_full/20260623_123624/Qwen3-4B-bnb-4bit/merged-16bit` | y |
   | sft_grpo_v2_seed1_adapter | `scratch/schema_response_confidence/runs/schema_clean_sft_grpo_v2_seed1_full/20260624_095831/final_model` | y |
   | seq_seed1_base | `.../sft__4b__headline__seed1/20260614_053221/Qwen3-4B-bnb-4bit/merged-16bit` | y |
   | seq_seed2_base | `.../sft__4b__headline__seed2/20260615_090734/Qwen3-4B-bnb-4bit/merged-16bit-lowmem-20260616` | y |
   | seq_seed3_base | `.../sft__4b__headline__seed3/20260615_104507/Qwen3-4B-bnb-4bit/merged-16bit` | y |
   | seq_sft_dpo_seed{1,2,3}_adapter | `.../sft_dpo__4b__amendment_a__seed{1,2,3}/.../final_model` | y (all three) |
   | seq_sft_kto_seed{1,2,3}_adapter | `.../sft_kto__4b__amendment_a__seed{1,2,3}/.../final_model` | y (all three) |

   All non-hub paths verified present via `ls -d` at build time. Every one of
   these merged-16bit seq bases was "NOT ON DISK" when
   `prompt-crossing-completion` first registered (its configs' header
   comments record the rebuild recipes) but was subsequently built as part
   of that cell's run and never deleted; this cell reuses those merges,
   it does not rebuild them. STOP if any path is missing at launch time --
   do not silently rebuild here; escalate, since a missing merge that
   existed at build time means something removed it between build and
   launch and that needs explanation before proceeding.

4. Verify the docker digest before ANY stage counts as valid (same pinned
   image the crossing cell used; no engine exception in this cell -- see
   `cell.yaml instrument.runtime` block):

   ```
   docker inspect --format '{{.Id}}' <container_name_or_id>
   # must equal sha256:f21629b9ae4ed11231768edfaed0f40d41d85d6ea9a71e8096a3d96ea0311772 char for char
   ```

5. Recompute the sha256 of all 8 config files plus `cell.yaml` and
   `gates.yaml` and compare against `experiment.yaml instrument.pins` (empty
   until `bin/exp sign` runs; this step is a no-op until signing, listed here
   for completeness of the launch sequence).

## Stage 1 -- primary campaign, 20 arms on AmbigQA (GPU, ~9-11h) -- feeds PH-G0, PH-G1 C1/C2/C3

One `docker run` per config, in `cell.yaml run_order` (grouped by base model
so adapter-only arms reuse a warm base where possible): configs 1, 2
(base_prc, base_pplain -- two single-arm base loads for C1), then config 3
(ten arms, one base load, C1's descriptive base_pstruct row + C2 gate), then
config 4 (warmed pstruct, own base), then configs 5-7 (seq seed1/seed2/seed3,
each its own per-seed merged base, C3 gate). One GPU job at a time.

```
docker run -d --name eh-phc-eval-<cfg-slug>-$(date +%Y%m%dT%H%M%SZ) --gpus all --ipc=host \
  --entrypoint python3 -e HF_HOME=/workspace/repo/.cache/hf \
  -e HUGGINGFACE_HUB_CACHE=/workspace/repo/.cache/hf/hub \
  -v "/home/profsynapse/code/Epistemic-Humility-Research:/workspace/repo" \
  -w /workspace/repo \
  unsloth/unsloth@sha256:f21629b9ae4ed11231768edfaed0f40d41d85d6ea9a71e8096a3d96ea0311772 \
  archive/experiment/phase1/eval/run_eval.py --config <config path> --live-vllm
```

Repeat for each of the 7 primary configs in `run_order`. Verify the docker
digest before EACH launch (stage 0 item 4). Confirm GPU idle (0 MiB,
`docker ps` empty) before each subsequent launch.

STOP if: any container exits non-zero; any arm's row coverage is short of
its surface's full retained n (1832 for every primary arm); or
`metrics.json provenance.config_sha` does not match the pinned config's
first 16 hex chars once signed.

## Stage 2 -- secondary descriptive campaign, 2 arms x 2 surfaces (GPU, ~2-3h) -- no gate

```
docker run -d --name eh-phc-eval-secondary-$(date +%Y%m%dT%H%M%SZ) --gpus all --ipc=host \
  --entrypoint python3 -e HF_HOME=/workspace/repo/.cache/hf \
  -e HUGGINGFACE_HUB_CACHE=/workspace/repo/.cache/hf/hub \
  -v "/home/profsynapse/code/Epistemic-Humility-Research:/workspace/repo" \
  -w /workspace/repo \
  unsloth/unsloth@sha256:f21629b9ae4ed11231768edfaed0f40d41d85d6ea9a71e8096a3d96ea0311772 \
  archive/experiment/phase1/eval/run_eval.py \
  --config experiments/prompt-crossing-heldout-confirmatory/configs/eval_heldout_secondary_pstruct_local_4b.yaml \
  --live-vllm
```

Before launching this stage, resolve the arm-count ambiguity flagged in
`cell.yaml arms_secondary` and this build's report (2 vs 4 arms; the config
as built covers 2). Reported straight, no gate, no promotion rides on this
stage.

## Stage 3 -- scoring and per-arm metrics (produced inline by run_eval.py; no separate stage)

`run_eval.py` writes `metrics.json` and `scored_rows.jsonl` per arm per eval
set under each config's `results_dir`
(`results_prompt_crossing_heldout_confirmatory_4b` for primary,
`results_prompt_crossing_heldout_confirmatory_secondary_4b` for secondary),
mirroring the crossing cell's layout exactly. No separate scoring pass is
required; `scorers.score_quadrants` + `scorers.metrics_from_quadrants` run
inline (same as `prompt-crossing-completion` and
`ood-breadth-beyond-selfaware`).

## Stage 4 -- aggregation and gate evaluation (CPU) -- PH-G0, PH-G1

1. **PH-G0** (per arm): confirm full row coverage against `cell.yaml`
   `primary_rows_per_arm: 1832` (primary) / `secondary_rows_per_arm: 5586`
   (secondary, KUQ 5540 + BB 46 combined); confirm `metrics.json
   provenance.config_sha` matches the pinned config bytes
   (`experiment.yaml instrument.pins`, populated at signing); confirm the
   scorer parse path is recorded (`provenance.verified`, `metric` fields,
   same shape as the crossing cell's PC-G0 check).

2. Lead recomputes at least two pivotal arms from raw `scored_rows.jsonl`
   independently of the runner's `metrics.json` (`gates.yaml
   ph_g0.lead_recompute_min_arms: 2`) -- pick from the arms carrying the
   most weight in the C1/C2/C3 adjudication (e.g. base_prc, one cold-SFT
   seed, one seq arm), per the crossing cell's precedent (it recomputed
   seq_sft_dpo_seed3, seq_sft_kto_seed1, cold_sft_seed3_rc).

3. **PH-G1**, applied verbatim from `gates.yaml`:
   - C1: `base_prc.refusal_recall_pct - base_pplain.refusal_recall_pct` on
     AmbigQA against the [50, 90]pp band / <15pp falsifier.
   - C2: each cold SFT seed's P-struct AmbigQA recall against [40, 80]% /
     <20% falsifier; base_pstruct against <=10% / >15% falsifier; each cold
     DPO/KTO seed against <=10% / >=20% falsifier.
   - C3: each seq arm's P-struct AmbigQA recall as a percentage of its
     SAME-SEED cold-SFT parent's P-struct AmbigQA recall (config 3's
     cold_sft_seed{N}_pstruct arm on the SAME AmbigQA surface -- NOT the
     SelfAware parent value `prompt-crossing-completion`'s PC-G1 used;
     `gates.yaml ph_g1.c3_erosion_not_erasure.parent_definition`) against
     [40, 100]% / <25% falsifier.

This step is lead-only per the project's delegation discipline (protocol
interpretation and gate/falsifier adjudication are never delegated).

## Budget

11-14 GPU-hours local RTX 3090 (docker lane), per `AMENDMENT.md` and
`cell.yaml budget_gpu_hours`. Primary campaign ~36.6k generations (comparable
total volume to `prompt-crossing-completion`'s 37k, ~10.5h wall); secondary
campaign ~11.2k generations under the 2-arm reading built here (see the
arm-count ambiguity note in stage 2). No training, no cloud, no new data
fetch -- every checkpoint and row artifact already exists on disk.

## STOP conditions (summary; each also stated inline above)

- Any checkpoint path in stage 0 item 3 is missing at launch time.
- Any of the three screened row-artifact files is missing or its row count
  does not match `cell.yaml surfaces[].rows`.
- The docker digest does not match
  `sha256:f21629b9ae4ed11231768edfaed0f40d41d85d6ea9a71e8096a3d96ea0311772`
  char for char.
- `ood.py` / `run_eval.py` / `scorers.py` shas differ from stage 0 item 2's
  recorded values (harness has changed since this build; re-verify before
  launch).
- Any arm's row coverage falls short of its surface's full retained n.
- The stage-2 arm-count ambiguity is unresolved at launch time.
