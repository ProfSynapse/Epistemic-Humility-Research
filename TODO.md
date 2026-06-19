# TODO / Current State

Last updated: 2026-06-19

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
  - Train/dev split is clean by `probe_pool_row_key` and by normalized question text.
  - Important fix: TriviaQA `question_id` is not unique, so audits must use `*_question_keys`, not bare `*_question_ids`.
  - Follow-up audit on 2026-06-14 found 188 normalized prompt texts present in both train and dev under different source row keys. This is now fixed: the builder groups the dev split by `norm_question(question)`, the regenerated `questions_frozen.json` records `dev_split_group_key`, and the re-audit found 0 normalized prompt overlaps.
  - Regenerated Qwen3 4B dataset hashes after the split fix: `sft_train.jsonl` `714577a8ce6d32ace422df519690b0a96adde3985f36cab0a24404e0a92d558b`; `dpo_train.jsonl` `39e2ba8c9bc1b41ef1b7e797f80637c276ba150c97055962bbc4e2b550bd17b5`; `kto_congruence_train.jsonl` and `kto_correctness_safe_train.jsonl` `9cb291ee45c8dd5893b150abe033386127d0eedce9fa16faa2309e31a1a70e15`; `questions_frozen.json` `2d29e79f0748c076e5768f38210dd4da2548725cb16e54d125a6b556b90bdd64`.
  - Public HF dataset repo: https://huggingface.co/datasets/professorsynapse/epistemic-humility-phase1
  - Qwen3 4B Phase 1 train/dev JSONLs are public there: `sft_train.jsonl`, `sft_dev.jsonl`, `dpo_train.jsonl`, `dpo_dev.jsonl`, `kto_congruence_train.jsonl`, `kto_congruence_dev.jsonl`, `kto_correctness_safe_train.jsonl`, and `kto_correctness_safe_dev.jsonl`.

- Local SFT headline seed 1 completed.
  - Run id: `sft__4b__headline__seed1`
  - Current grouped-split rerun adapter: `synaptic-tuner/toolset-training-artifacts/runs/local/4b/sft__4b__headline__seed1/20260614_053221/final_model`
  - Previous pre-split-fix adapter: `synaptic-tuner/toolset-training-artifacts/runs/local/4b/sft__4b__headline__seed1/20260611_202126/final_model`
  - Metrics: `.../logs/training_latest.jsonl`
  - Run record: `experiment/phase1/run_records/sft__4b__headline__seed1.json`
  - Grouped-split rerun completed on 2026-06-14: 1,800 / 1,800 steps, 1 epoch, train runtime 2,503.748s, train loss 0.44903450502289666, final logged loss 0.3236, peak reserved VRAM 4.393 GB, OOM risk low.

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

- Bounded SelfAware evidence run completed.
  - Config: `experiment/phase1/eval/config/eval_selfaware_evidence_2240_192_local_4b.yaml`.
  - Shape: SelfAware only, offset 2240, limit 192, expected/observed 97 known / 95 unknown, base/SFT/DPO only. No KTO, cloud, headline, full, or protocol run.
  - Docker run id: `eh-selfaware-evidence-2240-192-local-4b`.
  - Exit code 0 with `eval complete: 3 arm x set rows, config_sha=70ac0fe102d8db1f`.
  - Outputs: `experiment/phase1/eval/results_selfaware_evidence_2240_192_local_4b`.
  - `rg "<think>|</think>" experiment\phase1\eval\results_selfaware_evidence_2240_192_local_4b` found no matches.
  - Summary table: base n=192, unknown=95, known=97, refusal_recall 0.0, answer_on_unknown 100.0, over_refusal 0.0, correct_on_known 24.74, truthful 12.5; SFT n=192, unknown=95, known=97, refusal_recall 85.26, answer_on_unknown 14.74, over_refusal 71.13, correct_on_known 50.0, truthful 49.48; DPO n=192, unknown=95, known=97, refusal_recall 0.0, answer_on_unknown 100.0, over_refusal 0.0, correct_on_known 18.56, truthful 9.38.
  - Refusal counts: SFT refused 81/95 unknowns and 69/97 knowns; base and DPO refused 0/95 unknowns and 0/97 knowns.
  - Interpretation: the SFT pattern survived a larger contiguous SelfAware slice, with substantially improved refusal recall/truthful score versus base/DPO, but severe over-refusal. DPO remains base-like here. This is bounded research evidence on one contiguous SelfAware slice, not broad OOD, headline, protocol, or full-run evidence.
  - Non-blocking warnings were the same as earlier local diagnostics: Triton routing module, AOT cache save, and NCCL shutdown warning. No new blocker.

- Full SelfAware local evidence run completed.
  - Config: `experiment/phase1/eval/config/eval_selfaware_full_local_4b.yaml`.
  - Shape: full SelfAware, 3,369 rows = 2,337 known / 1,032 unknown, base/SFT/DPO only. No KTO, bridge, cloud, headline, protocol, or full matrix.
  - Docker run id: `eh-selfaware-full-local-4b`.
  - Exit code 0 with `eval complete: 3 arm x set rows, config_sha=25e6a1faf916c7ef`.
  - Outputs: `experiment/phase1/eval/results_selfaware_full_local_4b`.
  - `rg "<think>|</think>" experiment\phase1\eval\results_selfaware_full_local_4b` found no matches.
  - Summary table: base truthful 19.26, refusal_recall 0.0, answer_on_unknown 100.0, over_refusal 0.04, correct_on_known 27.78; SFT truthful 39.51, refusal_recall 89.73, answer_on_unknown 10.27, over_refusal 66.07, correct_on_known 51.07; DPO truthful 15.08, refusal_recall 0.0, answer_on_unknown 100.0, over_refusal 0.04, correct_on_known 21.75.
  - Refusal counts: SFT refused 926/1,032 unknowns and 1,544/2,337 knowns; base refused 0 unknowns and 1 known; DPO refused 0 unknowns and 1 known.
  - Interpretation: the earlier 192-row SelfAware pattern survived on full SelfAware. SFT strongly learns abstention on unknowns, but the cost is severe known-question over-refusal; DPO remains close to base.

- Broader local OOD evidence run completed.
  - Config: `experiment/phase1/eval/config/eval_broader_ood_evidence_local_4b.yaml`.
  - Shape: base/SFT/DPO only over KUQ balanced slice (384 rows = 192 unknown / 192 known), full CoCoNot contrast set (379 known), TruthfulQA 256 known, PopQA 256 known. No KTO, bridge, cloud, headline, protocol, or full matrix.
  - Docker run id: `eh-broader-ood-evidence-local-4b`.
  - Exit code 0 with `eval complete: 12 arm x set rows, config_sha=7bcf77af7f76caaf`.
  - Outputs: `experiment/phase1/eval/results_broader_ood_evidence_local_4b`.
  - `rg "<think>|</think>" experiment\phase1\eval\results_broader_ood_evidence_local_4b` found no matches.
  - KUQ: base truthful 9.64 / refusal_recall 0.0 / over_refusal 0.0; SFT truthful 53.12 / refusal_recall 97.4 / over_refusal 79.69; DPO truthful 9.11 / refusal_recall 0.52 / over_refusal 0.0.
  - Known-only pressure: SFT over_refusal was 79.68 on CoCoNot, 76.17 on TruthfulQA, and 92.97 on PopQA. DPO stayed near base on refusal behavior, but had lower known correctness than base on PopQA.
  - CoCoNot caveat: the local contrast file has empty answer aliases, so its truthful/correctness scores are 0 by construction; use it for refusal-rate/over-refusal behavior, not answer correctness.
  - Interpretation: the SFT abstention signal generalized beyond SelfAware to KUQ, but the over-refusal failure also generalized strongly across known-only OOD pressure sets. This is broader bounded local evidence, still not headline/protocol evidence.

- Grouped-split SFT rerun comparator evals completed.
  - Adapter: `synaptic-tuner/toolset-training-artifacts/runs/local/4b/sft__4b__headline__seed1/20260614_053221/final_model`.
  - Full SelfAware grouped-SFT-only eval completed with `config_sha=327c92c91428e9d4`.
  - Outputs: `experiment/phase1/eval/results_sft_grouped_selfaware_full_local_4b`.
  - Summary: truthful 37.99, refusal_recall 83.82, answer_on_unknown 16.18, over_refusal 64.18, correct_on_known 49.58. No `<think>` / `</think>` matches were found.
  - Broader OOD grouped-SFT-only eval completed in Docker run `eh-sft-grouped-broader-ood-local-4b`, exit 0, with `config_sha=57cb7a1c6fe5e601`.
  - Outputs: `experiment/phase1/eval/results_sft_grouped_broader_ood_local_4b`.
  - KUQ: truthful 51.82, refusal_recall 97.92, answer_on_unknown 2.08, over_refusal 82.29.
  - Known-only pressure: over_refusal 78.63 on CoCoNot, 80.47 on TruthfulQA, and 91.02 on PopQA. CoCoNot and TruthfulQA correctness/truthful values are not useful in this local file/config because aliases/gold coverage are empty or absent there; use those rows for refusal-rate/over-refusal pressure.
  - Interpretation: the grouped split did not erase the core SFT pattern. SFT still strongly learns abstention on unknowns, but it still over-refuses badly on known questions. The grouped rerun is slightly weaker than the pre-split full SelfAware SFT result, but qualitatively the same.

- Amendment A sequential local smoke path completed.
  - Amendment A / v0.4 is signed as a prospective extension, separate from the locked v0.3 matrix.
  - Grouped-split SFT adapter merged successfully to: `synaptic-tuner/toolset-training-artifacts/runs/local/4b/sft__4b__headline__seed1/20260614_053221/Qwen3-4B-bnb-4bit/merged-16bit`.
  - Merge output has `config.json`, no `adapter_config.json`, and two safetensor shards totaling about 8.0 GB.
  - `SFT -> DPO` max-2 smoke completed from the merged SFT model.
    - Run id: `sft_dpo__4b__amendment_a_smoke__seed1`
    - Artifact root: `synaptic-tuner/toolset-training-artifacts/runs/local/4b/sft_dpo__4b__amendment_a_smoke__seed1/20260614_073819`
    - Concrete log: `.../logs/training_20260614_113942.jsonl`
    - Final step 2, final loss 0.6931, peak reserved VRAM 4.922 GB, OOM risk low.
  - `SFT -> KTO` max-2 smoke completed from the merged SFT model.
    - Run id: `sft_kto__4b__amendment_a_smoke__seed1`
    - Artifact root: `synaptic-tuner/toolset-training-artifacts/runs/local/4b/sft_kto__4b__amendment_a_smoke__seed1/20260614_074015`
    - Concrete log: `.../logs/training_20260614_114134.jsonl`
    - Final step 2, final loss 0.5, peak reserved VRAM 4.375 GB, OOM risk low.
  - Interpretation: the end-to-end local mechanics for sequential training work: merged SFT model load, fresh DPO/KTO LoRA application, data load, two optimizer steps, final adapter save, lineage/capacity artifacts, and host artifact write-out.

- Amendment A sequential full local runs are underway.
  - `SFT -> DPO` full local run completed successfully.
    - Run id: `sft_dpo__4b__amendment_a__seed1`.
    - Artifact root: `synaptic-tuner/toolset-training-artifacts/runs/local/4b/sft_dpo__4b__amendment_a__seed1/20260614_074933`.
    - Final adapter: `.../final_model`.
    - Concrete log: `.../logs/training_20260614_115056.jsonl`.
    - Final step 1,800 / 1,800, final loss 0.07663947408947731, train runtime 3,584.511s, peak reserved VRAM 6.902 GB, OOM risk low.
    - Run record: `experiment/phase1/run_records/sft_dpo__4b__amendment_a__seed1.json`.
  - `SFT -> DPO` full local seed expansion completed for seeds 2 and 3.
    - Seed 2 run id: `sft_dpo__4b__amendment_a__seed2`; artifact root `synaptic-tuner/toolset-training-artifacts/runs/local/4b/sft_dpo__4b__amendment_a__seed2/20260616_114829`; concrete log `.../logs/training_20260616_155022.jsonl`; final step 1,800 / 1,800, final loss 0.09853133141752753, train runtime 4,142.616s, peak reserved VRAM 6.902 GB, OOM risk low.
    - Seed 3 run id: `sft_dpo__4b__amendment_a__seed3`; artifact root `synaptic-tuner/toolset-training-artifacts/runs/local/4b/sft_dpo__4b__amendment_a__seed3/20260616_130451`; concrete log `.../logs/training_20260616_170641.jsonl`; final step 1,800 / 1,800, final loss 0.07731692519496493, train runtime 4,015.803s, peak reserved VRAM 6.902 GB, OOM risk low.
    - Full SelfAware DPO-only evals completed while KTO seed 2 was training. The original seed 2 output `experiment/phase1/eval/results_amendment_a_selfaware_full_seed2_sft_dpo_local_4b` is confounded and excluded. Seed 3 output: `experiment/phase1/eval/results_amendment_a_selfaware_full_seed3_sft_dpo_local_4b`, config sha `8ea042deeaef115e`. Neither output contained `<think>` / `</think>` matches.
    - Full SelfAware DPO metrics from the original pass: seed 1 refusal_recall 48.84, over_refusal 13.95, truthful 30.25; excluded bad-merge seed 2 refusal_recall 2.23, over_refusal 0.04, truthful 17.01; seed 3 refusal_recall 43.70, over_refusal 11.42, truthful 28.55.
    - The original seed 2 attempt is flagged as confounded, not clean sequential evidence. The DPO training log was clean and did train from `sft__4b__headline__seed2/.../merged-16bit`, but a post-hoc sanity eval of that merged SFT seed2 base alone on the 192-row SelfAware slice produced refusal_recall 6.32, over_refusal 4.12, truthful 12.5. The expected SFT seed2 adapter eval had refusal_recall 87.4 on full SelfAware. The earlier nonzero/OSError seed2 merge must be treated as a semantic merge failure despite structural file validation.
    - SFT seed2 was re-merged with low-memory Unsloth merge into `synaptic-tuner/toolset-training-artifacts/runs/local/4b/sft__4b__headline__seed2/20260615_090734/Qwen3-4B-bnb-4bit/merged-16bit-lowmem-20260616`. Structural shape matched the expected 2-shard 8,044,936,192-byte index, and the 192-row SelfAware sanity eval passed behaviorally: refusal_recall 85.26, over_refusal 70.1, truthful 50.0, with no `<think>` / `</think>` / `reasoning_content` matches.
    - Clean seed2 `SFT -> DPO` rerun launched from the verified low-memory merge and completed.
      - New artifact root: `synaptic-tuner/toolset-training-artifacts/runs/local/4b/sft_dpo__4b__amendment_a__seed2/20260616_164539`.
      - Container: `funny_ride`; host PID observed: `11544`.
      - Concrete log: `.../logs/training_20260616_204756.jsonl`.
      - Training result: final step 1,800 / 1,800, final loss 0.07945938525647055, train runtime 5,009.702s, peak reserved VRAM 6.902 GB, OOM risk low.
      - Run record: `experiment/phase1/run_records/sft_dpo__4b__amendment_a__seed2.json`; the record retains the bad-merge attempt under `outcome.confounded_attempt`.
      - Clean eval output: `experiment/phase1/eval/results_amendment_a_selfaware_full_seed2_sft_dpo_lowmem_local_4b/sft_dpo_seed2_lowmem__selfaware/metrics.json`.
      - Clean eval metrics: n=3,369, unknown=1,032, known=2,337, refusal_recall 65.89, answer_on_unknown 34.11, over_refusal 18.36, refusal_rate 32.92, correct_on_known 25.84, truthful 34.82.
      - Contamination scan for `<think>` / `</think>` / `reasoning_content` found no matches.
    - Clean `SFT -> DPO` three-seed means from the listed seed metrics: refusal_recall 52.81, answer_on_unknown 47.19, over_refusal 14.58, truthful 31.21, correct_on_known 25.38. Note: the handoff aggregate listed refusal_recall 52.48, which does not match the provided per-seed values; reconcile before citing the refusal-recall mean in publication-grade output.
    - Interpretation update: valid sequential DPO evidence now includes clean seeds 1, 2, and 3. All three reduce SFT over-refusal while preserving some unknown refusal. Clean seed 2 is plausible but stronger than seeds 1 and 3; the original bad-merge seed2 attempt remains excluded.
  - `SFT -> KTO` full local run completed successfully from the same merged SFT model.
    - Run id: `sft_kto__4b__amendment_a__seed1`.
    - Host PID: `24564`.
    - Container: `elated_shaw`.
    - Artifact root: `synaptic-tuner/toolset-training-artifacts/runs/local/4b/sft_kto__4b__amendment_a__seed1/20260614_085358`.
    - Final adapter: `.../final_model`.
    - Concrete log: `.../logs/training_20260614_125521.jsonl`.
    - Final step 3,599 / 3,599, final loss 0.2568387638515617, train runtime 28,753.901s, peak reserved VRAM 4.391 GB, OOM risk low.
    - Data/training checks passed: balanced KTO data 14,395 desirable / 14,395 undesirable, merged SFT model load, tokenizer load, fresh LoRA application, trainer preprocessing, full optimizer schedule, final adapter save, lineage/capacity artifacts, and host artifact write-out.
    - Run record: `experiment/phase1/run_records/sft_kto__4b__amendment_a__seed1.json`.
  - `SFT -> KTO` seed 2 was stopped locally because it used the same bad merged SFT seed2 base.
    - Run id: `sft_kto__4b__amendment_a__seed2`.
    - Host PID: `11252`.
    - Container: `goofy_benz`.
    - Artifact root: `synaptic-tuner/toolset-training-artifacts/runs/local/4b/sft_kto__4b__amendment_a__seed2/20260616_141725`.
    - Concrete log: `.../logs/training_20260616_181929.jsonl`.
    - Early checks passed: balanced KTO data, merged SFT seed 2 base load, tokenizer load, fresh LoRA application, trainer preprocessing, and optimizer steps. During concurrent DPO evals, total GPU VRAM peaked around 16.4 GB, but KTO's own reserved VRAM stayed about 4.389 GB with low OOM risk.
    - Stop status: host PID `11252` was stopped; GPU returned to idle. Run record status is `stopped_confounded`.
    - Validity caveat: because the merged SFT seed2 base failed the behavioral sanity check, this stopped KTO seed2 run should not be counted as clean `SFT -> KTO` evidence. Rerun KTO seed2 only from the verified `merged-16bit-lowmem-20260616` base.
  - Clean `SFT -> KTO` seed 2 was relaunched from the verified low-memory SFT seed2 base and completed training.
    - Run id: `sft_kto__4b__amendment_a__seed2`.
    - Container: `zealous_villani`; container id `2a33dd0f3d8f`; host PID `45780`.
    - Artifact root: `synaptic-tuner/toolset-training-artifacts/runs/local/4b/sft_kto__4b__amendment_a__seed2/20260616_183650`.
    - Concrete log: `synaptic-tuner/toolset-training-artifacts/runs/local/4b/sft_kto__4b__amendment_a__seed2/20260616_183650/logs/training_20260616_223856.jsonl`.
    - Recipe base model: `/workspace/repo/toolset-training-artifacts/runs/local/4b/sft__4b__headline__seed2/20260615_090734/Qwen3-4B-bnb-4bit/merged-16bit-lowmem-20260616`.
    - Final training check: `train_end` at step 3,599 / 3,599, runtime 26,859.501 seconds, final loss 0.2636691490522058, peak reserved VRAM 4.393 GB, OOM risk low.
    - Final artifacts present: `final_model/adapter_model.safetensors`, `adapter_config.json`, tokenizer files, `training_lineage.json`, and `capacity_features.json`.
    - Run record: `experiment/phase1/run_records/sft_kto__4b__amendment_a__seed2.json`.
    - Full SelfAware eval completed in Docker container `eh-amendment-kto-seed2-eval`, exit 0, with `config_sha=b18d66c711bc62bd`.
    - Eval output: `experiment/phase1/eval/results_amendment_a_selfaware_full_seed2_sft_kto_lowmem_local_4b/sft_kto_seed2_lowmem__selfaware/metrics.json`.
    - No `<think>` / `</think>` / `reasoning_content` contamination matches were found.
    - Full SelfAware metrics: n 3,369 = 1,032 unknown / 2,337 known; refusal_recall 78.68, answer_on_unknown 21.32, over_refusal 45.53, correct_on_known 37.16, truthful 38.14.
  - Clean `SFT -> KTO` seed 3 was launched locally from the seed3 merged SFT base.
    - Run id: `sft_kto__4b__amendment_a__seed3`.
    - Container: `local-run-sft-kto-4b-amendment-a-seed3-20260617_070334`; container id `6a6db9a4b858`.
    - Artifact root: `synaptic-tuner/toolset-training-artifacts/runs/local/4b/sft_kto__4b__amendment_a__seed3/20260617_070334`.
    - Concrete log: `synaptic-tuner/toolset-training-artifacts/runs/local/4b/sft_kto__4b__amendment_a__seed3/20260617_070334/logs/training_20260617_110523.jsonl`.
    - Early checks passed: balanced KTO data 14,395 desirable / 14,395 undesirable, seed3 merged SFT model load, LoRA rank 32 / alpha 64 application, trainer initialization, and first optimizer steps.
    - Latest launch check: step 95 / 3,599, loss 0.5014, reserved VRAM 4.385 GB, OOM risk low; checkpoints observed at 25, 50, and 75.
    - Launch caveat: this run was launched by an equivalent direct detached Docker command because PowerShell background launch paths in the Codex shell failed on duplicate `Path`/`PATH` environment handling and non-persistent background jobs. The materialized recipe remains the provenance source for settings.
  - Interpretation: seed-1 and clean seed-2 `SFT -> KTO` are evaluated; seed3 `SFT -> KTO` is now training. KTO is seed-consistent so far: it preserves much more unknown refusal than DPO, but retains high over-refusal.

- Amendment A sequential broader OOD local eval completed.
  - Config: `experiment/phase1/eval/config/eval_amendment_a_broader_ood_local_4b.yaml`.
  - Shape: `sft_merged`, `sft_dpo`, and `sft_kto` over KUQ balanced slice (384 rows = 192 unknown / 192 known), full CoCoNot contrast set (379 known), TruthfulQA 256 known, and PopQA 256 known. No cloud, bridge, headline aggregation, protocol, or full matrix.
  - Lineage rule: all arms used the merged grouped-SFT base model at `synaptic-tuner/toolset-training-artifacts/runs/local/4b/sft__4b__headline__seed1/20260614_053221/Qwen3-4B-bnb-4bit/merged-16bit`; sequential DPO/KTO adapters were applied as LoRAs on top.
  - Docker run exited 0 with `eval complete: 12 arm x set rows, config_sha=d5d819efb942a202`.
  - Outputs: `experiment/phase1/eval/results_amendment_a_broader_ood_local_4b`.
  - `rg "<think>|</think>|reasoning_content" experiment/phase1/eval/results_amendment_a_broader_ood_local_4b` found no matches.
  - KUQ: `sft_merged` truthful 52.34 / refusal_recall 98.44 / over_refusal 80.21; `sft_dpo` truthful 40.1 / refusal_recall 69.79 / over_refusal 20.31; `sft_kto` truthful 48.7 / refusal_recall 90.62 / over_refusal 72.92.
  - Known-only pressure: `sft_dpo` reduced over-refusal sharply versus `sft_merged` on CoCoNot 22.43 vs 74.93, TruthfulQA 25.0 vs 78.12, and PopQA 46.48 vs 88.67, but also reduced KUQ unknown refusal. `sft_kto` mostly preserved high KUQ refusal but retained high over-refusal: CoCoNot 65.17, TruthfulQA 59.38, PopQA 80.08.
  - CoCoNot caveat remains: local contrast aliases are empty, so use CoCoNot for refusal-rate/over-refusal behavior, not answer correctness.
  - Interpretation: sequential DPO is the first local evidence of a meaningful over-refusal reduction after SFT, but it trades away a substantial part of unknown refusal. Sequential KTO preserves more of the SFT abstention behavior, but only modestly improves over-refusal. This is bounded local Amendment A evidence, not v0.3 headline/protocol evidence.

- Amendment A sequential full SelfAware local eval completed.
  - Config: `experiment/phase1/eval/config/eval_amendment_a_selfaware_full_local_4b.yaml`.
  - Shape: full SelfAware, 3,369 rows = 2,337 known / 1,032 unknown, `sft_merged`, `sft_dpo`, and `sft_kto` only. No cloud, bridge, headline aggregation, protocol, or full matrix.
  - Lineage rule: all arms used the merged grouped-SFT base model at `synaptic-tuner/toolset-training-artifacts/runs/local/4b/sft__4b__headline__seed1/20260614_053221/Qwen3-4B-bnb-4bit/merged-16bit`; sequential DPO/KTO adapters were applied as LoRAs on top.
  - Docker run exited 0 with `eval complete: 3 arm x set rows, config_sha=62388c69b67bbc43`.
  - Outputs: `experiment/phase1/eval/results_amendment_a_selfaware_full_local_4b`.
  - `rg "<think>|</think>|reasoning_content" experiment/phase1/eval/results_amendment_a_selfaware_full_local_4b` found no matches.
  - Summary: `sft_merged` truthful 38.5, refusal_recall 82.56, answer_on_unknown 17.44, over_refusal 61.49, correct_on_known 49.44; `sft_dpo` truthful 30.25, refusal_recall 48.84, answer_on_unknown 51.16, over_refusal 13.95, correct_on_known 25.61; `sft_kto` truthful 36.92, refusal_recall 75.68, answer_on_unknown 24.32, over_refusal 48.31, correct_on_known 38.33.
  - Interpretation: full SelfAware matches the broader OOD direction. Sequential DPO sharply reduces over-refusal but loses much of SFT's unknown refusal and known correctness. Sequential KTO retains more abstention and truthful score than DPO, but only partially reduces over-refusal. This is bounded local Amendment A evidence, not v0.3 headline/protocol evidence.

- Amendment A scored-row rerun and exact transition analysis completed from persisted local eval artifacts.
  - Script/report: `experiment/phase1/eval/analysis/amendment_a_transition_analysis.py` and `experiment/phase1/eval/analysis/amendment_a_transition_report.md`.
  - Rerun containers: `amend-a-selfaware-scored-20260614` exited 0 and wrote 3 x 3,369 SelfAware `scored_rows.jsonl` files; `amend-a-broader-ood-scored-20260614` exited 0 and wrote all 12 broader OOD `scored_rows.jsonl` files. `rg "<think>|</think>|reasoning_content"` found no matches in either result directory.
  - Row-identity rule: exact transitions align by `eval_set` plus `row_index`; `id` is metadata only. This avoids relying on globally unique question IDs.
  - Full SelfAware exact truthful flips: `sft_merged -> sft_dpo` had 429 SFT-truthful/DPO-untruthful vs 145 DPO-truthful/SFT-untruthful rows; `sft_merged -> sft_kto` had 125 vs 70; `sft_dpo -> sft_kto` had 106 vs 335.
  - Full SelfAware exact transition evidence: `sft_dpo` answered on 377 unknown rows where `sft_merged` correctly refused, while `sft_kto` did so on 91 such rows. `sft_dpo` also converted 1,113 known SFT refusals into answers, but only 95 of those became correct answers; `sft_kto` converted 322 known SFT refusals into answers, with 37 correct.
  - KUQ exact transitions support the same direction: `sft_merged -> sft_dpo` had 57 SFT-truthful/DPO-untruthful flips, 54 from unknown SFT-refusal becoming DPO-answer; `sft_merged -> sft_kto` had 17 such flips, 14 from unknown-refusal loss.
  - Interpretation: sequential DPO's over-refusal reduction is real but mixed; it applies strong answer pressure that also collapses a substantial portion of unknown refusal and known correctness. Sequential KTO preserves more abstention but leaves high over-refusal.
  - Next experimental recommendation: if Amendment A continues, prioritize deliberately scoped sequential-stage sensitivity. DPO variants should test lower-intensity correction (lower beta, lower LR, fewer effective epochs/steps, and possibly smaller downstream LoRA rank/alpha). KTO variants are justified only if the priority is preserving abstention first while seeking stronger known-question recovery. Keep `scored_rows.jsonl` as a required eval artifact for exact transition analysis.

- Local KTO headline seed 1 completed and was audited.
  - Run id: `kto__4b__headline__seed1`.
  - Adapter: `synaptic-tuner/toolset-training-artifacts/runs/local/4b/kto__4b__headline__seed1/20260613_151337_logging_patch/final_model`.
  - Metrics: `.../logs/training_latest.jsonl`.
  - Run record: `experiment/phase1/run_records/kto__4b__headline__seed1.json`.
  - Training completed 3,599 / 3,599 steps in 5h43m4s, saved `final_model`, `training_lineage.json`, and `capacity_features.json`.
  - Audit: `training_latest.jsonl` ended with `train_end`, final loss was 0.3003657495819817, `oom_risk_level` was low, and peak reserved VRAM was well below the 24 GB card limit.
  - Caveat: the materialized local recipe still carries the temporary copy-mode `import logging` patch for compatibility with older KTO copies. The Synaptic Tuner source itself already imports `logging` and passed the KTO source test.

- Local 4B cold-start headline seed expansion completed through full SelfAware eval.
  - Completed local training cells: `sft__4b__headline__seed1..3`, `dpo__4b__headline__seed1..3`, and `kto__4b__headline__seed1..3`.
  - Run records are present under `experiment/phase1/run_records/`; seed 2/3 materialized recipes are present under `experiment/phase1/run_records/materialized_recipes/`.
  - Full SelfAware all-arm eval outputs:
    - Seed 1: `experiment/phase1/eval/results_selfaware_full_seed1_all_arms_4b_20260615_2148`.
    - Seed 2: `experiment/phase1/eval/results_selfaware_full_seed2_all_arms_4b_20260615_2148`.
    - Seed 3: `experiment/phase1/eval/results_selfaware_full_seed3_all_arms_4b_20260616_0615`.
  - Each arm wrote 3,369 scored rows = 1,032 unknown-labeled / 2,337 known-labeled SelfAware examples. `rg "<think>|</think>|reasoning_content"` found no matches in the completed result directories.
  - Three-seed means and ranges:
    - SFT: refusal recall 87.88% (83.91-92.34), over-refusal 64.77% (64.31-65.25), correct-on-known 50.21% (49.88-50.74), truthful 39.19% (38.08-40.52).
    - DPO-from-base: refusal recall 0.03% (0.00-0.10), over-refusal 0.10% (0.04-0.17), correct-on-known 22.60% (21.77-24.06), truthful 15.67% (15.08-16.68).
    - KTO-from-base: refusal recall 0.00% (0.00-0.00), over-refusal 0.14% (0.09-0.17), correct-on-known 26.95% (26.62-27.19), truthful 18.67% (18.43-18.85).
  - Interpretation: the local three-seed SelfAware evidence strongly supports the SFT part of the hypothesis: SFT consistently induces unknown-question abstention. It also confirms the major failure mode: SFT over-refuses known questions at about 65%. Cold-start DPO and KTO are stable negative controls here; neither learns abstention under this recipe.
  - Claim tier: bounded local SelfAware evidence across three seeds. This is stronger than the earlier slices, but still not the full locked v0.3 headline matrix across all evaluation surfaces.

- Dependent Amendment A sequential seed queue did not progress and is no longer active.
  - Prior dependent queue PID `36436` and headline queue PID `39164` are not running.
  - Queue log `experiment/phase1/run_records/logs/queue_amendment_a_after_headline.log` only records `QUEUE_START waiting_for_headline_pid=39164`; it has no `QUEUE_COMPLETE`, launched-cell, or failure lines.
  - The intended cells remain useful but should be relaunched deliberately if/when approved: `sft_dpo__4b__amendment_a__seed2`, `sft_kto__4b__amendment_a__seed2`, `sft_dpo__4b__amendment_a__seed3`, and `sft_kto__4b__amendment_a__seed3`.
  - Claim tier: not running, not result evidence.

- KTO full SelfAware local comparator completed.
  - Config: `experiment/phase1/eval/config/eval_kto_selfaware_full_local_4b.yaml`.
  - Shape: full SelfAware, 3,369 rows = 2,337 known / 1,032 unknown, KTO seed 1 only. No base/SFT/DPO, bridge, cloud, headline aggregation, protocol, or full matrix.
  - Docker run id: `eh-kto-selfaware-full-local-4b`.
  - Exit code 0 with `eval complete: 1 arm x set rows, config_sha=fb24ee65ee717a18`.
  - Outputs: `experiment/phase1/eval/results_kto_selfaware_full_local_4b`.
  - `rg "<think>|</think>" experiment\phase1\eval\results_kto_selfaware_full_local_4b` found no matches.
  - Summary: truthful 18.73, refusal_recall 0.0, answer_on_unknown 100.0, over_refusal 0.21, correct_on_known 27.06.
  - Refusal counts: KTO refused 0/1,032 unknowns and 5/2,337 knowns.
  - Interpretation: cold-start KTO did not learn the abstention behavior on full SelfAware. It is much closer to base/DPO behavior than to SFT.

- KTO broader OOD local comparator completed.
  - Config: `experiment/phase1/eval/config/eval_kto_broader_ood_evidence_local_4b.yaml`.
  - Shape: KTO seed 1 only over KUQ balanced slice (384 rows = 192 unknown / 192 known), full CoCoNot contrast set (379 known), TruthfulQA 256 known, and PopQA 256 known. No base/SFT/DPO, bridge, cloud, headline aggregation, protocol, or full matrix.
  - Docker run id: `eh-kto-broader-ood-evidence-local-4b`.
  - Exit code 0 with `eval complete: 4 arm x set rows, config_sha=2acc68f74d12e302`.
  - Outputs: `experiment/phase1/eval/results_kto_broader_ood_evidence_local_4b`.
  - `rg "<think>|</think>" experiment\phase1\eval\results_kto_broader_ood_evidence_local_4b` found no matches.
  - KUQ: truthful 9.9, refusal_recall 0.0, answer_on_unknown 100.0, over_refusal 1.56.
  - Known-only pressure: KTO over_refusal was 0.0 on CoCoNot, TruthfulQA, and PopQA; correctness was 9.38 on TruthfulQA and 19.92 on PopQA. CoCoNot still has empty answer aliases, so use it only for refusal-rate/over-refusal.
  - Interpretation: KTO-from-base is now a completed local comparator, and it supports the same practical hypothesis as DPO-from-base: preference-style training alone is not inducing abstention on this small model/run. The next research question is whether `SFT -> DPO` or `SFT -> KTO` can preserve SFT's abstention gains while reducing over-refusal.

- Local hidden-state extraction MVP and comparable 128x128 scale diagnostics completed for grouped-split SFT plus cold-start DPO/KTO adapters.
  - This is exploratory mechanism evidence only; it is off the locked v0.3 headline path and does not mutate run records.
  - Smoke config: `.tmp/hidden_state_probe_sft_smoke_docker.yaml` (ignored temp file), 1 known + 1 unknown, all layers.
  - Smoke output: `experiment/phase1/probe/qwen3-4b-instruct/hidden_states/extraction__520184798388`, manifest `status=ok`, `verified=true`, 2 rows, 6 safetensor shards.
  - MVP config: `.tmp/hidden_state_probe_sft_mvp_docker.yaml` (ignored temp file), 16 known + 16 unknown, all layers.
  - MVP output: `experiment/phase1/probe/qwen3-4b-instruct/hidden_states/extraction__c35b3f3bf8ae`, manifest `status=ok`, `verified=true`, 32 rows, 96 safetensor shards.
  - Scale config: `.tmp/hidden_state_probe_sft_128x128_docker.yaml` (ignored temp file), config SHA `12fb10b1c8c8522f`, 128 known + 128 unknown, all layers.
  - Scale output: `experiment/phase1/probe/qwen3-4b-instruct/hidden_states/extraction__12fb10b1c8c8`, manifest `status=ok`, `verified=true`, 256 rows, 768 safetensor shards.
  - Runtime contract confirmed on real Qwen3-4B: tensor shapes are `h_base`, `h_lora`, and `delta` each `[37, 2560]`, i.e. embeddings + 36 transformer layers.
  - Scale extraction confirmed the same tensor shapes: `h_base`, `h_lora`, and `delta` each `[37, 2560]`.
  - Provenance captured: base revision `cad0bedfdd862093a12af478cb974ab2addd0e0a`, PEFT `0.18.1`, Transformers `4.57.6`, aligned run record `sft__4b__headline__seed1`, research repo commit `552fa8bd35c863ab94510ff4689e84545aac78f1`, submodule gitlink `040054021c6da2c8c94453edbb699a487221120e`.
  - Scale run thinking-token check passed: no `<think>`, `</think>`, or `reasoning_content` matches.
  - Native Windows Python was not viable for this specific 4-bit model load: `bitsandbytes` failed on `ModuleNotFoundError: No module named 'triton.ops'`. Docker/Unsloth worked.
  - Docker needed Git safe-directory env vars for manifest finalization: `GIT_CONFIG_COUNT=1`, `GIT_CONFIG_KEY_0=safe.directory`, `GIT_CONFIG_VALUE_0=/workspace/repo`. Without that, extraction wrote rows but failed finalization because `research_repo_commit` and `submodule_commit` were `None`.
  - Diagnostic linear-probe layer was added at `experiment/phase1/probe/hidden_state_linear_probe.py` with tests in `experiment/phase1/probe/tests/test_hidden_state_linear_probe.py`.
  - `hidden_state_directions.py` now provides exploratory Phase 3 direction-candidate infrastructure: it writes vector shards plus CSV/JSON provenance for later intervention pilots. Verification reported 4 focused tests passed and 117 passed / 5 skipped integrated. Claim tier: tooling only, not mechanism evidence or steering.
  - Diagnostic run over `extraction__c35b3f3bf8ae` wrote `hidden_state_linear_probe_diagnostic.csv/json` into the gitignored extraction directory. It evaluated 111 role/layer cells (3 roles x 37 layers). Best balanced accuracy on the tiny 32-row smoke slice: `h_base` layer 24 = 0.6875, `h_lora` layer 25 = 0.84375, `delta` layer 24 = 0.84375. This validates the analysis plumbing only; do not treat it as headline evidence.
  - Five-fold scale diagnostic over `extraction__12fb10b1c8c8` wrote `hidden_state_linear_probe_kfold5_diagnostic.csv/json` into the gitignored extraction directory. Extraction took about 195s; the 5-fold diagnostic took about 295s. Best balanced accuracy: `h_base` layer 25 = 0.75390625 (known 0.71875, unknown 0.7890625), `h_lora` layer 36 = 0.86328125 (known 0.84375, unknown 0.8828125), `delta` layer 35 = 0.85546875 (known 0.8515625, unknown 0.859375). This is still exploratory mechanism/local diagnostic evidence, not headline or pre-registered evidence.
  - Comparable DPO config: `.tmp/hidden_state_probe_dpo_128x128_docker.yaml` (ignored temp file), 128 known + 128 unknown, all layers.
  - Comparable DPO output: `experiment/phase1/probe/qwen3-4b-instruct/hidden_states/extraction__f3dbd2c1754a`, manifest `status=ok`, `verified=true`, 256 rows, 768 safetensor shards, and no `<think>` / `</think>` / `reasoning_content` matches.
  - DPO five-fold diagnostic best balanced accuracy: `h_base` layer 25 = 0.75390625, `h_lora` layer 35 = 0.7734375, `delta` layer 35 = 0.75.
  - Comparable KTO config: `.tmp/hidden_state_probe_kto_128x128_docker.yaml` (ignored temp file), 128 known + 128 unknown, all layers.
  - Comparable KTO output: `experiment/phase1/probe/qwen3-4b-instruct/hidden_states/extraction__0810aa2972e8`, manifest `status=ok`, `verified=true`, 256 rows, 768 safetensor shards, and no `<think>` / `</think>` / `reasoning_content` matches.
  - KTO five-fold diagnostic best balanced accuracy: `h_base` layer 25 = 0.75390625, `h_lora` layer 36 = 0.765625, `delta` layer 26 = 0.75.
  - Plain read across comparable 128x128 local diagnostics: the base pass is identical across arms, while SFT adapter/delta representations show stronger known-vs-unknown separability than cold-start DPO/KTO. This is consistent with the bounded behavioral evidence that preference-only DPO/KTO runs stayed base-like, but it remains exploratory local mechanism evidence only.
  - Sequential `SFT -> DPO` hidden-state extraction completed at `experiment/phase1/probe/qwen3-4b-instruct/hidden_states/extraction__0d58c201ab3e`.
  - Sequential `SFT -> KTO` hidden-state extraction completed at `experiment/phase1/probe/qwen3-4b-instruct/hidden_states/extraction__e1473df788a5`.
  - Both sequential extractions used the same 128 known + 128 unknown slice, all layers, 256 rows, 768 safetensor shards, manifest `status=ok`, `verified=true`, no `<think>` / `</think>` / `reasoning_content` matches, and base revision/hash `local-sha256:813a8a882a07871b2167948931791f69ad19add8b7c4e6cf2faef0a25e1fbdcd`.
  - Generic local-model provenance fix: local merged model directories now populate `base_model_revision` and `base_model_hash` as `local-sha256:<digest>` while the strict final manifest gate and Hub commit behavior remain preserved.
  - Sequential `sft_dpo` five-fold diagnostic best balanced accuracy: `h_base` layer 36 = 0.84375, `h_lora` layer 34 = 0.85546875, `delta` layer 35 = 0.859375.
  - Sequential `sft_kto` five-fold diagnostic best balanced accuracy: `h_base` layer 36 = 0.84375, `h_lora` layer 35 = 0.859375, `delta` layer 36 = 0.85546875.
  - Comparative caveat: the sequential base is merged SFT, not original Qwen, so `h_base` already represents SFT; `delta` is the preference-stage change over SFT. Plain read: SFT creates high separability; cold-start DPO/KTO do not; sequential DPO/KTO preserve or reshape the high SFT separability.
  - `hidden_state_linear_probe.py` now supports `--cv stratified_kfold --cv-folds 5`; default leave-one-out behavior is preserved.
  - Command shape that worked:

    ```powershell
    docker run --rm --gpus all `
      -e GIT_CONFIG_COUNT=1 `
      -e GIT_CONFIG_KEY_0=safe.directory `
      -e GIT_CONFIG_VALUE_0=/workspace/repo `
      -v "F:\Code\Epistemic-Humility-Research:/workspace/repo" `
      -v hf-cache:/root/.cache/huggingface `
      -w /workspace/repo `
      --entrypoint python3 unsloth/unsloth:latest `
      experiment/phase1/probe/hidden_state_probe.py `
      --config .tmp/hidden_state_probe_sft_mvp_docker.yaml
    ```

- Phase 3 causal-pilot dry-run validation completed without generation.
  - Config: `experiment/phase1/probe/config/phase3_causal_pilot_smoke.yaml`.
  - Validator: `experiment/phase1/probe/phase3_causal_pilot_dry_run.py`.
  - Output root: `experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_sft_smoke/` (generated/local artifacts; not shown by `git status`).
  - Written artifacts: `dry_run_manifest.json`, `planned_arms.json`, and `metrics_plan.json`.
  - Validation passed for the two SFT candidate directions: `sft_h_lora_l36_known_unknown` (`direction__9c8c74f718038292`, vector hash `c39566b0c0dc550f617ff5368a473abd5c2aa87f2ad853f8cd9f1b473bc45b5a`) and `sft_delta_l35_known_unknown` (`direction__8bb10838ed21eebe`, vector hash `98292b59523bf0a78d0d5ae65df3757d8d538c6cc78ef9bede4ac2e38dd47fc1`).
  - Row contract: each direction resolves to 256 rows = 128 known / 128 unknown from `extraction__12fb10b1c8c8`.
  - Planned arms: 112 dry-run arms across two directions, seven coefficient values, and required controls. `generation_executed` is `false` in the validator result, manifest, and metrics plan.
  - Verification: `python experiment\phase1\probe\phase3_causal_pilot_dry_run.py --config experiment\phase1\probe\config\phase3_causal_pilot_smoke.yaml --no-write` passed; `python -m pytest experiment\phase1\probe\tests\test_phase3_causal_pilot_dry_run.py -q` passed with 3 tests.
  - Next Phase 3 step: implement or select the actual intervention runner only after an explicit go-ahead. It should consume this dry-run manifest, preserve the fixed row/prompt contracts, run no-vector/sign-flip/random/shuffled/wrong-layer controls, and keep results Tier 2 exploratory local diagnostics.

## Known Issues / Gotchas

- Hidden-state extraction local runtime gotchas.
  - Prefer Docker/Unsloth over native Windows Python for `unsloth/Qwen3-4B-bnb-4bit`; native Python currently sees CUDA but fails the 4-bit load through `bitsandbytes` / missing `triton.ops`.
  - If running in Docker, use container-native adapter paths (`/workspace/repo/...`) or disable eval-config mirroring and set `arms[].adapter` explicitly in a temp config. Windows absolute adapter paths from eval configs are not valid inside Linux containers.
  - Pass Git safe-directory env vars into the container so `_git_commit` and `_submodule_commit` can populate the manifest. Otherwise the harness can finish tensor writes and still fail the final `require_populated=True` provenance gate.
  - Local merged model directories are now represented in hidden-state manifests with `base_model_revision` and `base_model_hash` set to `local-sha256:<digest>`. Hub model ids still use Hub commit provenance, and manifest finalization still requires populated provenance.
  - Keep HF model cache outside the git workspace. The successful run used Docker volume `hf-cache:/root/.cache/huggingface`.

- KTO source logging bug is fixed locally, but KTO remains gated for cloud.
  - First full KTO attempt trained nearly to completion but failed after training because `train_kto.py` references `logging` without importing it.
  - A 20-step patched KTO debug run proved that adding `import logging` inside the copied container file allows the KTO trainer to complete and copy artifacts.
  - `synaptic-tuner/Trainers/kto/train_kto.py` now imports `logging` locally and was verified with `python -m pytest synaptic-tuner\tests\trainers\kto\test_train_kto_source.py -q` (5 passed).
  - HF Jobs/cloud KTO smoke remains blocked until the Synaptic Tuner fix is committed/pushed to the exact cloud commit and the cloud launcher/dataset prerequisites are cleared. The experiment-side local copy-mode workaround will not apply in HF Jobs.
  - The patched full KTO rerun progressed to at least step 1,650 / 3,599, then `docker exec` returned Windows code `3221225786`; Docker Desktop then returned HTTP 500 for `docker ps/info/inspect`. A later local KTO seed 1 rerun completed cleanly.
  - Run record: `experiment/phase1/run_records/kto__4b__headline__seed1.json`
  - Current local status: completed and verified.

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
  - Do not pass the full repo `.env` into local eval containers unless that exact run truly needs secrets. The grouped-SFT broader OOD eval used public/local assets and ran successfully with only `HF_HOME` / `HUGGINGFACE_HUB_CACHE` env vars.
  - When a live eval config uses a Windows absolute `model_name` for a local merged base, the container wrapper must translate `model_name` as well as `arms[].adapter`; otherwise vLLM receives an unmounted Windows path inside Linux.
  - Bind-mode local training artifacts can leave `training_latest.jsonl` as a Windows reparse point that `Get-Content` cannot read. Use the concrete timestamped `logs/training_*.jsonl` file for verification and run records.

- Local eval scoring/generation gotchas fixed.
  - OOD records carry their own `aliases`; scoring now prefers normalized non-empty record aliases and falls back to global Cheng gold. Without this, OOD known correctness/truthful vectors could be wrongly zero when questions are absent from Cheng gold.
  - Qwen3 prompt rendering with thinking disabled is insufficient; vLLM `SamplingParams` now receives stop strings `<think>` and `</think>` when `generation.enable_thinking: false`, preserving any configured `generation.stop` values. The generated-thinking guard remains a backstop; do not strip contaminated outputs.
  - Non-blocking warnings seen during local diagnostics: Triton routing module warning, AOT cache save/HF cache metadata permission warnings, and NCCL `destroy_process_group` shutdown warning.

- Cheng recipe provenance correction.
  - The Cheng paper text is vague on exact training implementation, but the official OpenMOSS/Say-I-Dont-Know README gives concrete commands.
  - Idk-SFT uses `llama_recipes/finetuning.py --enable_fsdp`, `--num_epochs 10`, `--lr 2e-5`, `--batch_size_training 4`, and `--gradient_accumulation_steps 2`.
  - Idk-DPO is initialized from the SFT result model and uses `loss.beta=0.1`, `loss.sft_coef_when_dpo=0.01`, batch size 64, gradient accumulation 4, and FSDPTrainer.
  - Therefore the Qwen3 Phase 1 LoRA/QLoRA recipes are not a bit-for-bit Cheng reproduction. They are a modern, resource-feasible replication-style design that reuses the dataset/metric idea while holding LoRA capacity fixed across arms.
  - Research implication: DPO/KTO-from-base doing little is less surprising under this correction. The more Cheng-faithful preference question is sequential `SFT -> DPO` / `SFT -> KTO`, and epochs/LoRA rank/alpha deserve a sensitivity axis after the grouped-split SFT comparator is evaluated.

- Dataset audit caveat fixed: row-key disjointness is not the same as prompt-text disjointness.
  - `questions_frozen.json` train/dev keys remain disjoint, and the builder now also keeps duplicate normalized prompts on the same side.
  - A stricter 2026-06-14 audit initially found 188 normalized question texts appearing on both train and dev sides because TriviaQA carries duplicate source rows with identical prompts under different row keys.
  - The builder now splits grouped by `norm_question(question)`, records `dev_split_group_key`, and has regression coverage for this exact failure mode.
  - Re-audit after rebuild: 0 row-key overlap, 0 normalized-question overlap, leakage guard passed, KTO labels balanced, no unknown-negative fallback, no `<think>` / `</think>` / `reasoning_content`, and byte-for-byte reproducibility against a fresh rebuild.

- `Start-Process` may fail in Codex Desktop PowerShell due duplicate `Path` / `PATH`.
  - Reliable detached launcher is a `py -3.11 -c` wrapper around `subprocess.Popen`.

## Next Steps

1. Amendment A / v0.4 is signed as a prospective extension for mixed-stage `SFT -> DPO` and `SFT -> KTO` (user approval, 2026-06-14). Keep it separate from the locked v0.3 headline matrix.
2. The grouped-split SFT LoRA adapter is already merged locally; use the `merged-16bit` path above for sequential DPO/KTO runs, then train fresh downstream DPO/KTO LoRA adapters with `model.name` pointing at that merged SFT model path.
3. Treat previous local DPO and KTO seed 1 as completed pre-split-fix bounded comparators. The plain-language read remains: SFT learned abstention but over-refused badly; DPO-from-base and KTO-from-base stayed base-like and did not learn abstention on those local evidence surfaces.
4. Sequential DPO clean seeds 1, 2, and 3 are now usable as bounded local Amendment A evidence; the original seed2 attempt from the bad SFT merge remains confounded and excluded.
5. Clean KTO seed2 has completed full SelfAware eval and now counts as bounded local behavioral evidence. KTO seeds 1-2 are consistent: high abstention retention with high over-refusal. KTO seed3 is now training locally. If Amendment A continues after clean KTO seed evidence, add sensitivity around the sequential preference stage: lower DPO beta, lower LR, fewer effective epochs/steps, and possibly smaller downstream LoRA rank/alpha for gentler correction; KTO sensitivity is most useful if the priority is preserving abstention while reducing known over-refusal.
6. Candidate exploratory cells requested for future approval/tracking, all separate from locked v0.3 headline matrix/counts:
   - Amendment C crossover preference stacking: `sft_dpo_kto` (`SFT -> DPO -> KTO`) seeds 1, 2, and 3; `sft_kto_dpo` (`SFT -> KTO -> DPO`) seeds 1, 2, and 3.
   - Amendment B prospective GRPO: cold-start `grpo` seeds 1, 2, and 3; sequential `sft_grpo` (`SFT -> GRPO`) seeds 1, 2, and 3.
   - No launch is authorized by this TODO entry. Before materializing recipes, record exact source artifacts to merge/use, destination run ids, eval contract, lane, and whether the tuner path can express the intended base/reference/reward relationship.
   - Do not create runnable recipe YAML for these cells until the missing prerequisites are resolved. Current known blockers: crossover recipes need seed-specific merged prior-stage model paths; GRPO recipes need a truthfully supported Phase 1 GRPO local/cloud dispatch path plus the projected GRPO dataset/reward wiring for this experiment.
7. Before cloud KTO smoke, commit/push the Synaptic Tuner KTO logging fix to the exact cloud commit, then clear cloud launcher and dataset prerequisites.
8. Before any long local run, prefer the bare Docker/host GPU checks that are known to work from Codex:

   ```powershell
   docker ps -a --format "{{.Names}} {{.Status}}"
   nvidia-smi --query-gpu=timestamp,name,utilization.gpu,memory.used,memory.total --format=csv,noheader
   ```

   Avoid treating `docker info` / `docker context ls` failures as definitive engine failures in this environment; they can be Docker config/API permission artifacts.

9. If Docker is healthy, use the SFT max-2 micro recipe as the first confidence check:

   ```powershell
   py -3.11 tuner.py local-run --job-config F:\Code\Epistemic-Humility-Research\experiment\phase1\run_records\materialized_recipes\sft__4b__micro_max2.yaml --yes
   ```

   Run from `F:\Code\Epistemic-Humility-Research\synaptic-tuner`.

10. Full SelfAware three-seed cold-start eval is complete locally. Next behavioral evidence should focus on the already signed Amendment A question: whether `SFT -> DPO` or `SFT -> KTO` can preserve SFT's abstention while reducing known-question over-refusal. Avoid re-running the same cold-start DPO/KTO recipe unless a code or data defect is found.
11. Internal probing next step: do not treat the 128x128 hidden-state diagnostics or the causal-pilot dry-run as headline evidence. If mechanism work continues, implement the bounded causal/intervention runner against `phase3_sft_smoke`, consume the dry-run manifest, and only then interpret Tier 2 exploratory local effects.
12. Do not run additional long behavioral cells, 8B cells, cloud cells, or mixed-stage sequential expansions without explicit approval.
13. Do not immediately repeat the same A10G Qwen3 4B HF Jobs download loop. The latest `0400540` bounded SFT max-2 `cloud-pipeline` smoke submitted job `6a2c75e97c68f455eff143b2` and failed during remote `Qwen/Qwen3-4B` first-shard download before training/eval. Next, run a smaller cloud-pipeline smoke, for example a tiny public model, or improve launcher job-id capture, UTF-8 logging, and model-cache strategy before another Qwen3 4B attempt.
14. Only after local eval and cloud smoke both work should we consider more headline cells. KTO remains blocked for cloud expansion until an explicit KTO smoke is approved with the cloud prerequisites cleared. Mixed-stage cells are Amendment A / v0.4 work and require deliberately materialized recipes/run records.
15. Before cloud-lane expansion beyond the SFT smoke, verify process-local `HF_TOKEN` availability, use Synaptic Tuner's `cloud-pipeline` flow from a clean pushed exact commit, and confirm the already public Qwen3 4B dataset file names.

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
