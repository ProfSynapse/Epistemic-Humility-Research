# Public Artifacts

This file is the repo-side manifest for Hugging Face publication. It records
what should be public, what must stay local, and how published HF artifacts point
back to local provenance.

Publication is a release gate, not a training side effect. Upload only after the
run/eval artifacts are reconciled against
`archive/papers/retired/results-provenance-inventory.md` and the relevant run records.

## Published HF Repos

Use lowercase, queryable names. Record the exact HF revision after every upload.

| Artifact family | HF repo | Status | Revision | Local provenance | Notes |
|---|---|---|---|---|---|
| Phase 1 redistributable datasets | [`professorsynapse/epistemic-humility-phase1`](https://huggingface.co/datasets/professorsynapse/epistemic-humility-phase1) | published | `922d3b52ff6e8143b2701c3a7562909077eba4ab` | `experiment/phase1/data/qwen3-4b-instruct/` | Qwen3 4B train/dev JSONLs plus `README.md`, `build_manifest.json`, and `questions_frozen.json`. Excludes restricted bridge/OpenMOSS/Cheng-derived raw data. |
| Phase 1 eval outputs | [`professorsynapse/epistemic-humility-phase1-evals`](https://huggingface.co/datasets/professorsynapse/epistemic-humility-phase1-evals) | published | `df4a9961321c04903c748f8caa4d79f84840e3b7` | `experiment/phase1/eval/analysis/`, `papers/paper-2-training-regimen/analysis/row-pattern/`, and `archive/papers/retired/results-provenance-inventory.md` | Compact analysis layer only: aggregate tables, analysis reports, Paper 2 row-pattern outputs, thinking/sycophancy summaries, unknown-label analyses, and scripts. Full raw local eval result directories remain local unless deliberately released. |
| Phase 1 knowledge labels | [`professorsynapse/epistemic-humility-phase1-labels`](https://huggingface.co/datasets/professorsynapse/epistemic-humility-phase1-labels) | published | `fef638b8870937fddab6c2759baa404cb13da660` | `experiment/phase1/data/qwen3-4b-instruct/questions_frozen.json` and `experiment/phase1/probe/qwen3-4b-instruct/` | Compact label/probe release: frozen question split, probe manifest, and sensitivity grid. The large local `probe_results.jsonl` cache is not published. |
| Cloud-lane per-cell results | [`professorsynapse/epistemic-humility-cloud-results`](https://huggingface.co/datasets/professorsynapse/epistemic-humility-cloud-results) | published | `af7309529ef1fac77617fdf02860b8c16a504a1b` (card) | `experiment/phase1/probe/cloud/` (wrapper + launch manifests) | Result/manifest JSONs uploaded per cell by the HF Jobs lane itself; the card documents the folder schema and run-tag conventions (`y-*` = Amendment Y, `smoke-*` = non-evidence). Cells append continuously as jobs land. |
| Two-signal probe directions | [`professorsynapse/eh-probe-directions`](https://huggingface.co/datasets/professorsynapse/eh-probe-directions) | published (user-approved 2026-07-02) | `033ae541ba862e289f0c7ff200f6f3e9d171626e` | `experiments/common/artifacts/two_signal_probe_directions/` (Amendment AA fits, seed 20260630) | 4 families x gate/dial: per-layer unit-normed directions (safetensors) + fit metadata JSON + `PROVENANCE.json`. Apache-2.0 (probe weights over our own activations). Card carries the AA caveat: readout vectors, not validated steering handles. |
| Readout row surfaces | [`professorsynapse/eh-readout-rows`](https://huggingface.co/datasets/professorsynapse/eh-readout-rows) | published (user-approved 2026-07-02) | `808dd12336e34295ff64db91781e2b643ace9989` | per-folder source paths recorded in the repo's `PROVENANCE.json`; sources under `experiment/phase1/probe/` | 31 folders / 79,015 rows / ~62 MB: S/T/U/W/X/Z/SR/P generation surfaces (question, answer, grade — NO hidden states) + frozen probe-pool row layers. Per-source licenses on the card (SelfAware Apache-2.0, KUQ MIT, PopQA MIT companion, TriviaQA research-use). No OpenMOSS/Cheng IDK content; smokes excluded. |
| Amendment AH exhaust | [`professorsynapse/eh-doubt-on-command`](https://huggingface.co/datasets/professorsynapse/eh-doubt-on-command) | published (user-approved 2026-07-04) | `42b3629d3003f5048db3546b73454364a82cc7ea` | `experiment/phase1/probe/analysis/ah_main/`, `analysis/ah_addendum_a1/`, `analysis/ah_stage0/` (gen rows, instrumentation, stratum, manifests/gates) | 5,436 rows / ~4.3 MB: AH main 3 arms + primed-readout instrumentation + Addendum A1 stratum, with DATASHEET + LICENSE-AUDIT. Same four sources/verdicts as eh-readout-rows; zero FalseQA (audited 3 ways); absolute paths stripped (`<repo>/`); full mining pools deliberately NOT included (available on request under same audit). |
| J-space fresh-pool census | [`professorsynapse/eh-jspace-fresh-pool-census-qwen3-4b`](https://huggingface.co/datasets/professorsynapse/eh-jspace-fresh-pool-census-qwen3-4b) | published (user-approved 2026-07-08) | `3add102ce930f73a29013f572f03e7325da30825` | `experiments/j-space-layer-contrast-replication-qwen3-4b/analysis-committed/fresh_eval_pool_manifest.json` plus `build_hf_public_census.py` | 12,923 text-free candidate rows / 2,263 selected rows: ID/provenance/role/behavior flags only. No raw question text, aliases, prompt text, generation text, hidden states, or intervention outputs. |
| Deployed clean-SFT to GRPO-v2 adapter (seed 1) | `professorsynapse/eh-qwen3-4b-clean-sft-grpo-v2-seed1-lora` | staged private (2026-07-05) | `8914081dfcec4f1f025f2dbe4195d4f7aa8d210e` | `scratch/schema_response_confidence/runs/schema_clean_sft_grpo_v2_seed1_full/20260624_095831/final_model` | LoRA adapter staged private so cloud cells can reference it by repo + revision. Uploaded excluding the auto-generated `README.md` (its `base_model:` YAML carries a local path and fails Hub validation) and `training_args.bin`; consumers pass the base model explicitly. Not a public release. |

## Pending HF Repos

| Artifact family | Proposed HF repo | Status | Local provenance | Notes |
|---|---|---|---|---|
| Hidden-state tensors | `professorsynapse/eh-hidden-states-<family>` | planned (wave 2d) | extraction dirs under `experiment/phase1/probe/` | ~2 GB per model; Z families first. Y cloud cells discard extraction dirs by design — publishing Y tensors would need the upload knob flipped in `hf_jobs_cell.sh` for future cells. |
| Adapter repos | one repo per evaluated adapter | private-staged (2026-07-05) | run record + `training_lineage.json` + exact eval result path | 33 Qwen3-4B LoRA/merged checkpoints are now PRIVATELY staged on HF; the master mapping (HF repo @ revision <-> local source run dir <-> amendment/paper it backs) is [docs/checkpoint-staging.md](checkpoint-staging.md). Public release of any of these remains a separate per-release user approval and would be recorded as its own row here. |

## Adapter Naming

Use one model repo per released adapter:

```text
professorsynapse/eh-qwen3-4b-clean-sft-seed1-lora
professorsynapse/eh-qwen3-4b-clean-sft-dpo-seed1-lora
professorsynapse/eh-qwen3-4b-clean-sft-kto-seed1-lora
professorsynapse/eh-qwen3-4b-clean-sft-grpo-seed1-lora
```

For stacked runs, keep stage order explicit:

```text
professorsynapse/eh-qwen3-4b-clean-sft-dpo-grpo-seed1-lora
professorsynapse/eh-qwen3-4b-clean-sft-grpo-kto-seed1-lora
```

## Publication Gate

Before uploading a model artifact:

1. Confirm the run record is completed and not stale.
2. Confirm eval has run on the artifact intended for release.
3. Confirm the result is not marked as a failed or diagnostic-only run in the
   session note or provenance inventory.
4. Confirm `training_lineage.json` exists or can be generated.
5. Confirm the base model license allows public adapter release.
6. Confirm the upload is public unless the user explicitly approves a private
   temporary cloud-extraction artifact.

Before uploading datasets or eval rows:

1. Confirm source license permits redistribution.
2. Exclude restricted bridge/OpenMOSS/Cheng raw data.
3. Include schema and dataset-card provenance.
4. Pin and record the HF dataset revision after upload.

## Upload Path

Use the Synaptic Tuner upload-deployment workflow; do not create a parallel
uploader in this repo.

From `synaptic-tuner/`:

```bash
python .skills/upload-deployment/scripts/upload_model.py \
  PATH/TO/final_model \
  professorsynapse/eh-qwen3-4b-clean-sft-seed1-lora \
  --save-method lora \
  --training-lineage PATH/TO/training_lineage.json
```

For the first public release wave, prefer `--save-method lora`. Merged 16-bit
or GGUF releases should be deliberate reference artifacts, not the default.

After upload, update this file with:

- HF repo URL
- HF revision SHA
- local run record path
- eval result path
- caveats or exclusion notes

## Do Not Publish

- OpenMOSS / Cheng bridge raw data.
- Gated Llama-derived artifacts unless the license and user approval explicitly
  allow the exact release.
- Local HF caches, Docker outputs, scratch directories, or unreviewed checkpoints.
- Failed GRPO/reward-diagnostic runs as model repos unless intentionally released
  as negative-control artifacts with prominent model-card warnings.
