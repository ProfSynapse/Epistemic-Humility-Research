# Completing the prompt-condition crossing: warmed preference arms under P-struct, cold SFT under RC, warmed arms under plain-answer notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

### 2026-08-16 ~03:44Z — config 5 (warmed pplain) complete; all 11 arms done, run finished

Eval config 5 (`configs/eval_crossing_warmed_pplain_local_4b.yaml`, arms
clean_sft_merged_pplain (no adapter) + sft_grpo_v2_seed1_pplain, plain-answer
contract, no structured JSON output): container
`eh-pcc-eval-cfg5-warmedpplain-20260815T231639Z`. Started 03:16:39Z, exited
03:44:48Z (~28 min for 2 arms — the fastest config, consistent with the
plain-answer contract having no JSON-retry overhead).

PC-G0 both arms: n=3369, `provenance.config_sha` = `ba2f4af692d0652b`,
matching the first 16 hex chars of the pinned sha256
(`ba2f4af692d0652bd536bc108a037a3642d718bd03fe41d7dca3ebc5a6870289`) exactly.
PC-G0 PASS both arms.

Results: clean_sft_merged_pplain refusal_recall_pct=87.6,
over_refusal_pct=71.59, truthful_pct=36.72. sft_grpo_v2_seed1_pplain
refusal_recall_pct=96.22, over_refusal_pct=84.42, truthful_pct=36.0.

Metrics copied to `analysis-committed/metrics_clean_sft_merged_pplain__selfaware.json`
and `analysis-committed/metrics_sft_grpo_v2_seed1_pplain__selfaware.json`.
Container removed after verification. GPU confirmed idle (0 MiB) at close.

**All 11 arms across all 5 configs complete, PC-G0 PASS on every arm (full
n=3369 coverage, config_sha matches pinned bytes, scorer parse path
recorded).** `analysis-committed/` now holds 11 `metrics_*__selfaware.json`
files, one per arm, aggregate-only (no row-level generations or question
text committed anywhere; `results_prompt_crossing_completion_4b/` stays local
and gitignored per the cell's `.gitignore`). Total wall clock from first
merge launch (17:17Z) to last eval exit (03:44Z next day): ~10.5h, longer
than the ~5-6h estimate, driven mainly by the per-request retry-path
throughput on the six seq DPO/KTO P-struct arms (config 1-3, ~50 min/config
for 2 arms vs ~24 min/config for the SFT/plain arms in config 4-5). No commits
made, no gates adjudicated, no design changes to any pinned file. PC-G1
classification and the falsifier check (any seq arm < 30% P-struct recall)
are left to the lead; note that seq_sft_dpo_seed3_pstruct read 31.78%, close
to the 30% floor.

### 2026-08-16 ~03:16Z — config 4 (cold SFT RC) complete; config 5 (warmed pplain) launching

Eval config 4 (`configs/eval_crossing_coldsft_rc_local_4b.yaml`, three arms
cold_sft_seed{1,2,3}_rc, raw bnb-4bit base + each headline SFT adapter,
response-confidence contract): container
`eh-pcc-eval-cfg4-coldsftrc-20260815T222741Z`. Started 02:27:41Z, exited
03:16:05Z (~48 min for 3 arms — noticeably faster per-arm than the 2-arm seq
configs, consistent with the lead's hypothesis that the slow throughput is
specific to the seq DPO/KTO arms, not the SFT arms, though the RC contract
also uses the same structured-output retry settings; not diagnosed further).

PC-G0 all three arms: n=3369, `provenance.config_sha` = `8fdc13e6c0fbff8f`,
matching the first 16 hex chars of the pinned sha256
(`8fdc13e6c0fbff8f1e5eac434d77290ea2f426fb3c6f92c7da4be5b997bd964e`) exactly.
PC-G0 PASS all three arms.

Results: cold_sft_seed1_rc refusal_recall_pct=85.66, over_refusal_pct=53.23,
truthful_pct=40.13. cold_sft_seed2_rc refusal_recall_pct=90.21,
over_refusal_pct=60.33, truthful_pct=40.78. cold_sft_seed3_rc
refusal_recall_pct=90.6, over_refusal_pct=60.16, truthful_pct=40.93. All
three land inside the amendment's predicted 85-95% band for Gap 1a.

Metrics copied to `analysis-committed/metrics_cold_sft_seed{1,2,3}_rc__selfaware.json`.
Container removed after verification. GPU idle, disk 25G free.

Launching config 5 now (`configs/eval_crossing_warmed_pplain_local_4b.yaml`,
two arms: clean_sft_merged_pplain (no adapter) + sft_grpo_v2_seed1_pplain,
plain-answer contract, no structured JSON output — expect the fastest
config of the five). This is the last config in run_order; all 11 arms will
be complete after this. This entry precedes the launch verb.

### 2026-08-16 ~02:27Z — config 3 (seed3 pstruct) complete; all six Gap-3 seq arms done; config 4 (cold SFT RC) launching

Eval config 3 (`configs/eval_crossing_seq_pstruct_seed3_local_4b.yaml`, arms
seq_sft_dpo_seed3_pstruct + seq_sft_kto_seed3_pstruct, standard non-lowmem
seed3 merge): container `eh-pcc-eval-cfg3-seed3pstruct-20260815T213703Z`.
Started 01:37:03Z, exited 02:27:04Z (~50 min), exit 0.

PC-G0 both arms: n=3369, `provenance.config_sha` = `c9a8bfd0bd99a3ea`,
matching the first 16 hex chars of the pinned sha256
(`c9a8bfd0bd99a3ea3e330af9338c1e8f57f02ef5d99615807e3fb593dca9faa3`) exactly.
PC-G0 PASS both arms.

Results: seq_sft_dpo_seed3_pstruct refusal_recall_pct=31.78,
over_refusal_pct=9.93, truthful_pct=25.5 (close to the PC-G1 30% floor —
flagging for the lead's attention, not adjudicating). seq_sft_kto_seed3_pstruct
refusal_recall_pct=65.41, over_refusal_pct=31.92, truthful_pct=35.11.

All six Gap-3 seq arms (DPO/KTO x seed1/2/3) now complete. Summary of raw
P-struct refusal_recall_pct by arm (gate classification left to the lead):
dpo seed1=35.17, kto seed1=61.43, dpo seed2=54.17, kto seed2=65.12, dpo
seed3=31.78, kto seed3=65.41.

Metrics copied to `analysis-committed/metrics_seq_sft_dpo_seed3_pstruct__selfaware.json`
and `analysis-committed/metrics_seq_sft_kto_seed3_pstruct__selfaware.json`.
Container removed after verification. GPU idle, disk 25G free.

Launching config 4 now (`configs/eval_crossing_coldsft_rc_local_4b.yaml`,
three arms: cold_sft_seed{1,2,3}_rc, raw bnb-4bit base + each headline SFT
adapter, response-confidence contract). This is a 3-arm config so expect a
longer single-container run than configs 1-3. This entry precedes the launch
verb.

### 2026-08-16 ~01:36Z — config 2 (seed2 pstruct) complete; config 3 (seed3 pstruct) launching

Eval config 2 (`configs/eval_crossing_seq_pstruct_seed2_local_4b.yaml`, arms
seq_sft_dpo_seed2_pstruct + seq_sft_kto_seed2_pstruct, on the seed2 lowmem
merge): container `eh-pcc-eval-cfg2-seed2pstruct-20260815T205006Z`, same
invocation shape as config 1. Started 00:50:06Z, exited 01:36:29Z (~46 min),
exit 0. Same per-request retry-path throughput pattern observed in
`docker logs` as config 1 (not re-logged in detail).

PC-G0 both arms: n=3369, `provenance.config_sha` = `de8f647975f8e6ea`,
matching the first 16 hex chars of the pinned sha256
(`de8f647975f8e6ea383f1e7e35ad12297334e5f59168994c7cadb629d2493356`) exactly.
PC-G0 PASS both arms.

Results: seq_sft_dpo_seed2_pstruct refusal_recall_pct=54.17,
over_refusal_pct=13.26, truthful_pct=32.29. seq_sft_kto_seed2_pstruct
refusal_recall_pct=65.12, over_refusal_pct=34.66, truthful_pct=34.67.

Metrics copied to `analysis-committed/metrics_seq_sft_dpo_seed2_pstruct__selfaware.json`
and `analysis-committed/metrics_seq_sft_kto_seed2_pstruct__selfaware.json`.
Container removed after verification. GPU idle before next launch, disk 25G
free (unchanged — eval outputs are small relative to the 40G freed margin
after the merges).

Launching config 3 now (seed3 pstruct, arms seq_sft_dpo_seed3_pstruct +
seq_sft_kto_seed3_pstruct, standard non-lowmem seed3 merge). This entry
precedes the launch verb.

### 2026-08-16 ~00:49Z — config 1 (seed1 pstruct) complete; config 2 (seed2 pstruct) launching

Merges: all three rebuilt and verified (config.json parses, safetensors index
matches shard files present, 12-file layout matching the existing clean-SFT
merge reference) before any eval launched:
- seed1: `.../sft__4b__headline__seed1/20260614_053221/Qwen3-4B-bnb-4bit/merged-16bit/`
  — container `eh-pcc-merge-seed1-20260815T171715Z`, exit 0. (This container's
  own `docker wait` background-watch notification was delayed ~2h by a harness
  issue unrelated to the merge itself — the lead caught the stall and
  confirmed via direct inspection that the merge had already succeeded; all
  subsequent waits in this run use bounded foreground polling instead, per
  the lead's correction, never an unverified background notification.)
- seed2 (lowmem): `.../sft__4b__headline__seed2/20260615_090734/Qwen3-4B-bnb-4bit/merged-16bit-lowmem-20260616/`
  — container `eh-pcc-merge-seed2-20260815T194759Z`, exit 0, ran from a
  path-corrected copy of `.tmp/merge_sft_seed2_lowmem.py`
  (`.tmp/merge_sft_seed2_lowmem_pathfix.py`, same recipe, only the
  `synaptic-tuner/` path segment fixed — the original script's hardcoded
  paths omitted it and would have written outside the mounted tree).
- seed3: `.../sft__4b__headline__seed3/20260615_104507/Qwen3-4B-bnb-4bit/merged-16bit/`
  — container `eh-pcc-merge-seed3-20260815T195229Z`, exit 0, generic
  `archive/experiment/phase1/grpo/merge_sft_adapter_16bit.py <adapter_dir>
  <output_dir>` script, unmodified.

Disk after all three merges: 25G free (started at 49G; each merge ~7.6-8G).

Eval config 1 (`configs/eval_crossing_seq_pstruct_seed1_local_4b.yaml`,
arms seq_sft_dpo_seed1_pstruct + seq_sft_kto_seed1_pstruct): container
`eh-pcc-eval-cfg1-seed1pstruct-20260815T195641Z`, `docker run -d --gpus all
--ipc=host --entrypoint python3 -e HF_HOME=/workspace/repo/.cache/hf -e
HUGGINGFACE_HUB_CACHE=/workspace/repo/.cache/hf/hub -v
/home/profsynapse/code/Epistemic-Humility-Research:/workspace/repo -w
/workspace/repo unsloth/unsloth@sha256:f21629b9... archive/experiment/phase1/eval/run_eval.py
--config experiments/prompt-crossing-completion/configs/eval_crossing_seq_pstruct_seed1_local_4b.yaml
--live-vllm`. Started 23:56:41Z, exited 00:48:56Z (~52 min), exit 0.

Anomaly observed (matches the lead's anticipated failure mode): `docker logs`
showed the vLLM engine processing requests ONE AT A TIME
(`Adding requests: 1/1` repeated, not a large batch), i.e. the structured-JSON
retry path (`stated_confidence_json_retries: 2`,
`stated_confidence_structured_outputs: true`) appears to serialize generation
per-row for these non-SFT-descended (seq DPO/KTO) arms rather than batching
across the full 3369-row set the way a plain-answer arm would. This is the
likely reason config 1 took ~52 min for 2 arms versus panel/seed-robustness
precedent throughput; flagging as observed behavior, not diagnosed further
(out of scope for this execution-only cell).

PC-G0 per arm: both arms n=3369 (full coverage), `metrics.json`
`provenance.config_sha` = `29cbffb958207a24`, matching the first 16 hex chars
of the pinned sha256 for this config
(`29cbffb958207a2420011d94ce2386aaa80c85e3665a2c830592187b30839fc0` in
`experiment.yaml`) exactly. Scorer parse path recorded
(`provenance.verified: true`, `metric: truthful_rate`). PC-G0 PASS both arms.

Results: seq_sft_dpo_seed1_pstruct refusal_recall_pct=35.17,
over_refusal_pct=9.11, truthful_pct=26.6. seq_sft_kto_seed1_pstruct
refusal_recall_pct=61.43, over_refusal_pct=31.07, truthful_pct=33.84. (Gate
classification against the seed1 parent value, 69.57%, is the lead's call per
PC-G1, not made here.)

Metrics copied to
`analysis-committed/metrics_seq_sft_dpo_seed1_pstruct__selfaware.json` and
`analysis-committed/metrics_seq_sft_kto_seed1_pstruct__selfaware.json`
(aggregate only, no row-level generations or question text). Container
removed after verification. GPU confirmed idle (0 MiB) before next launch.

Launching config 2 now (seed2 pstruct, arms seq_sft_dpo_seed2_pstruct +
seq_sft_kto_seed2_pstruct, on the lowmem merge). This entry precedes the
launch verb.

### 2026-08-15 ~17:17Z — pre-run integrity check, merge rebuilds begin

Pre-flight: all five pinned configs' sha256 recomputed and verified byte-identical
to the pins in `experiment.yaml` (cell.yaml, gates.yaml, and all five
`configs/eval_crossing_*.yaml` match exactly). GPU idle (0 MiB, `docker ps`
empty) before launch. Disk: 49G free on `/` (95% used, 1007G total) before any
merge; each 4B 16-bit merge is ~7.6G based on the existing clean-SFT merge on
disk, so three merges (~23G) fit with margin, but free space is checked again
before each merge per the lead's instruction. All nine adapters referenced
across the five configs (six Amendment A seq adapters, three headline SFT
adapters) verified present on disk; two of three seq-block bases (clean-SFT
merged, GRPO-v2 adapter for Gap 1b) already exist on disk from the panel cell
— only the three per-seed 16-bit SFT merges (seed1, seed2-lowmem, seed3) need
rebuilding, matching the lead's brief.

Docker: local `default` context Docker Desktop 29.3.1, native `--gpus all`
confirmed against the RTX 3090 directly. Pinned image
`unsloth/unsloth@sha256:f21629b9ae4ed11231768edfaed0f40d41d85d6ea9a71e8096a3d96ea0311772`
already cached locally (digest matches local-runtime.md's pinned reference
exactly, no pull needed).

Merge rebuild plan (per each seq config's header comment, the locked recipe):
- seed1: `.tmp/merge_grouped_sft_lora_container.py` as-is (paths inside it
  already resolve correctly to
  `.../sft__4b__headline__seed1/20260614_053221/Qwen3-4B-bnb-4bit/merged-16bit`,
  matching the config's `model_name` byte-for-byte; verified by reading the
  script before running). Calls `merge_lora_checkpoint(..., load_in_4bit=True)`
  with `save_method="merged_16bit"` internally.
- seed2: `.tmp/merge_sft_seed2_lowmem.py` recipe (FastLanguageModel direct
  load, `save_pretrained_merged(..., maximum_memory_usage=0.5)`), but the
  script AS WRITTEN has a path bug: its `LORA_PATH`/`OUTPUT_PATH` are missing
  the `synaptic-tuner/` path segment (`/workspace/repo/toolset-training-artifacts/...`
  instead of `/workspace/repo/synaptic-tuner/toolset-training-artifacts/...`),
  which would write outside the mounted tree entirely since no
  `toolset-training-artifacts` exists at repo root (confirmed: only under
  `synaptic-tuner/`). This is a disposable `.tmp/` scratch script, not a
  pinned instrument file, so it is being run from a path-corrected copy that
  preserves the exact same recipe (same calls, same `maximum_memory_usage=0.5`
  flag) with only the path prefix fixed so the output lands at the config's
  `model_name` byte-for-byte, per the lead's explicit instruction.
- seed3: no seed3-specific script survives on disk; the seed3 config's own
  header rules out the lowmem path and points at the generic
  `archive/experiment/phase1/grpo/merge_sft_adapter_16bit.py <adapter_dir>
  <output_dir>` full-precision-load pattern (matches seed1's underlying
  mechanism: `load_in_4bit=False`, `save_method="merged_16bit"`, no
  `maximum_memory_usage` override) — invoked with seed3's adapter/output
  paths as CLI args, script itself unmodified.

All three run dirs and (for seed2) the pre-existing empty `Qwen3-4B-bnb-4bit/`
dir are already `777 profsynapse:profsynapse` on the host, so the non-root
(uid 1001) unsloth container can create the merge output subtree without a
pre-launch chmod.

Launching seed1 merge now: `docker run -d --name
eh-pcc-merge-seed1-20260815T171715Z --gpus all --ipc=host --entrypoint
python3 -v /home/profsynapse/code/Epistemic-Humility-Research:/workspace/repo
-w /workspace/repo unsloth/unsloth@sha256:f21629b9... .tmp/merge_grouped_sft_lora_container.py`.
Launch confirmed (`docker ps` shows `Up`). This entry precedes the launch verb.

## 2026-08-15 — lead adjudication (gates applied, Outcome written)

Lead verification before adjudication: 11/11 metrics files present in
`analysis-committed/`; independent recompute from raw `scored_rows.jsonl`
on three pivotal arms (seq_sft_dpo_seed3 31.78/9.93, seq_sft_kto_seed1
61.43/31.07, cold_sft_seed3_rc 90.60/60.16) agreed exactly with the
runner's metrics; row-stamped config_shas match the signed pins on all
three checked configs.

PC-G0 PASS x11. PC-G1 applied verbatim as registered: falsifier NOT
fired; kto_seed1 preserved; the other five seq arms partial erosion
(closest call dpo_seed3 at 31.78, 1.78pp above the 30 floor). Gap-1a
85-95 band held all seeds; at-or-above-plain ordering broke at seed 3
(90.60 < 92.34). Gap-1b both arms inside the ~10pp band vs their governed
RC readings (87.60 vs 87.02; 96.22 vs 93.41, from the
grpo-three-seed-confirmatory seed-1 table). Scoreboard reconciled
straight in the Outcome, including the orchestrator's missed 40-80 band
(dpo_seed1 35.17, dpo_seed3 31.78) and the KTO-near-parent call holding
only at seed 1.

Outcome section written into AMENDMENT.md. Resolve awaits explicit PI
approval per standing rule; verdict text staged in the Outcome.
