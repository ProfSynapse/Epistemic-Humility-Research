# Public Artifacts

This file is the repo-side manifest for Hugging Face publication. It records
what should be public, what must stay local, and how published HF artifacts point
back to local provenance.

Publication is a release gate, not a training side effect. Upload only after the
run/eval artifacts are reconciled against
`experiment/paper/results-provenance-inventory.md` and the relevant run records.

## Candidate HF Repos

Use lowercase, queryable names. Fill `status`, `hf_repo`, and `revision` when an
artifact is actually uploaded.

| Artifact family | Proposed HF repo | Status | Local provenance | Notes |
|---|---|---|---|---|
| Phase 1 redistributable datasets | `professorsynapse/epistemic-humility-phase1-data` | planned | `experiment/phase1/data/` dataset cards + build scripts | Exclude restricted bridge/OpenMOSS/Cheng-derived raw data. |
| Phase 1 eval outputs | `professorsynapse/epistemic-humility-phase1-evals` | planned | `experiment/phase1/eval/analysis/` + scored rows | Include aggregate CSVs and license-safe row-level outputs. |
| Phase 1 knowledge labels | `professorsynapse/epistemic-humility-phase1-labels` | planned | probe outputs / selected publication slices | Publish compact, reproducible labels/slices, not local cache dumps. |
| Adapter repos | one repo per evaluated adapter | planned | run record + `training_lineage.json` | Prefer LoRA-only repos first. |

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
