# Bounded Local Evidence

Read only when interpreting or comparing bounded local diagnostic/evidence runs. These are not headline/protocol results unless a governed run record says so.

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

- Grouped-split SFT comparator evals completed against the regenerated SFT
  adapter
  `synaptic-tuner/toolset-training-artifacts/runs/local/4b/sft__4b__headline__seed1/20260614_053221/final_model`.
  Full SelfAware grouped-SFT-only eval exited 0 with `config_sha=327c92c91428e9d4`
  and no `<think>` / `</think>` matches. Summary: truthful 37.99,
  refusal_recall 83.82, answer_on_unknown 16.18, over_refusal 64.18,
  correct_on_known 49.58. Broader OOD grouped-SFT-only eval
  `eh-sft-grouped-broader-ood-local-4b` exited 0 with
  `config_sha=57cb7a1c6fe5e601` and no `<think>` / `</think>` matches. KUQ:
  truthful 51.82, refusal_recall 97.92, answer_on_unknown 2.08, over_refusal
  82.29. Known-only pressure: over_refusal 78.63 on CoCoNot, 80.47 on
  TruthfulQA, and 91.02 on PopQA. Interpretation: the grouped split did not
  erase the core SFT pattern; SFT still strongly learns abstention on unknowns,
  but over-refuses badly on known questions. Treat this as bounded local
  motivation for Amendment A, not headline/protocol evidence.

- Sequential preference-training plan: for `SFT -> DPO` / `SFT -> KTO`, merge
  the grouped SFT LoRA adapter into a standalone local `merged-16bit` model
  first, then train fresh downstream DPO/KTO LoRA adapters with `model.name`
  pointing at that merged SFT model path. DPO/KTO reference models should load
  from the same merged SFT path so the preference objective regularizes against
  the SFT starting policy, matching the sequential question. Do not continue
  the same adapter in-place unless explicitly testing adapter-continuation as a
  separate design.

- Amendment A sequential local smoke status: the grouped-split SFT adapter
  merged successfully to
  `synaptic-tuner/toolset-training-artifacts/runs/local/4b/sft__4b__headline__seed1/20260614_053221/Qwen3-4B-bnb-4bit/merged-16bit`
  (`config.json` present, no `adapter_config.json`, two safetensor shards
  totaling about 8.0 GB). `SFT -> DPO` max-2 smoke
  `sft_dpo__4b__amendment_a_smoke__seed1` completed from that merged model,
  saved `final_model`, lineage, and capacity artifacts at
  `synaptic-tuner/toolset-training-artifacts/runs/local/4b/sft_dpo__4b__amendment_a_smoke__seed1/20260614_073819`,
  final step 2, final loss 0.6931, peak reserved VRAM 4.922 GB, OOM risk low.
  `SFT -> KTO` max-2 smoke `sft_kto__4b__amendment_a_smoke__seed1` completed
  from the same merged model, saved artifacts at
  `synaptic-tuner/toolset-training-artifacts/runs/local/4b/sft_kto__4b__amendment_a_smoke__seed1/20260614_074015`,
  final step 2, final loss 0.5, peak reserved VRAM 4.375 GB, OOM risk low.
  Bind-mode artifacts may make `training_latest.jsonl` a Windows reparse point
  that `Get-Content` cannot read; use the concrete timestamped
  `logs/training_*.jsonl` files for verification and run records.

- Amendment A sequential full local status: `SFT -> DPO` full run
  `sft_dpo__4b__amendment_a__seed1` completed successfully from the merged SFT
  model at
  `synaptic-tuner/toolset-training-artifacts/runs/local/4b/sft_dpo__4b__amendment_a__seed1/20260614_074933`.
  It saved `final_model`, lineage, and capacity artifacts; concrete metrics log
  is `logs/training_20260614_115056.jsonl`; final step 1,800/1,800, final loss
  0.07663947408947731, train runtime 3,584.511s, peak reserved VRAM 6.902 GB,
  OOM risk low. `SFT -> KTO` full run `sft_kto__4b__amendment_a__seed1` was
  launched as host PID `24564`, container `elated_shaw`, artifact root
  `synaptic-tuner/toolset-training-artifacts/runs/local/4b/sft_kto__4b__amendment_a__seed1/20260614_085358`;
  concrete metrics log is `logs/training_20260614_125521.jsonl`;
  early checks passed through balanced KTO data (14,395 desirable / 14,395
  undesirable), merged SFT model load, tokenizer load, fresh LoRA application,
  trainer preprocessing, and first optimizer steps. Step 25/3,599 had OOM risk
  low and peak reserved VRAM 4.387 GB. These are training/provenance facts only;
  the behavioral evidence gate is still eval of the sequential adapters against
  SelfAware/KUQ/OOD to test whether sequential preference training preserves SFT
  abstention while reducing known-question over-refusal.

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

- 2026-06-16 local three-seed cold-start SelfAware eval completed for
  `sft__4b__headline__seed1..3`, `dpo__4b__headline__seed1..3`, and
  `kto__4b__headline__seed1..3`. Outputs:
  `experiment/phase1/eval/results_selfaware_full_seed1_all_arms_4b_20260615_2148`,
  `experiment/phase1/eval/results_selfaware_full_seed2_all_arms_4b_20260615_2148`,
  and
  `experiment/phase1/eval/results_selfaware_full_seed3_all_arms_4b_20260616_0615`.
  Each arm wrote 3,369 scored SelfAware rows, and contamination scans for
  `<think>`, `</think>`, and `reasoning_content` found no matches. Three-seed
  means/ranges: SFT refusal recall 87.88% (83.91-92.34), over-refusal 64.77%
  (64.31-65.25), truthful 39.19% (38.08-40.52); DPO-from-base refusal recall
  0.03% (0.00-0.10), over-refusal 0.10% (0.04-0.17), truthful 15.67%
  (15.08-16.68); KTO-from-base refusal recall 0.00%, over-refusal 0.14%
  (0.09-0.17), truthful 18.67% (18.43-18.85). Readout: the SFT abstention
  effect is seed-robust on SelfAware but carries a severe known-question
  over-refusal cost; cold-start DPO/KTO remain stable negative controls under
  this recipe.
