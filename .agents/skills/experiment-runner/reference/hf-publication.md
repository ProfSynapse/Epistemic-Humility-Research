# HF Publication

Use this reference when preparing, documenting, or gating public Hugging Face
artifacts for this repo. It covers repo-side publication discipline only. Use
Synaptic Tuner's `upload-deployment` skill and CLI for the upload itself.

## Source of truth

- Repo manifest: `docs/public-artifacts.md`
- Provenance readiness: `archive/papers/retired/results-provenance-inventory.md`
- Run records: `experiment/phase1/run_records/`
- Tuner upload workflow: `synaptic-tuner/.skills/upload-deployment/SKILL.md`

## Publication gate

Do not upload a model artifact until:

1. The run record is completed and not stale.
2. Eval has run on the exact artifact intended for release.
3. The result is not marked failed or diagnostic-only in session/provenance docs.
4. `training_lineage.json` exists or can be generated.
5. The base-model and data licenses permit the planned public release.

Do not upload data/eval rows until:

1. Source license permits redistribution.
2. Restricted bridge/OpenMOSS/Cheng raw data is excluded.
3. Schema and dataset-card provenance are included.
4. The HF revision SHA is recorded after upload.

## Model artifact policy

- Prefer public LoRA-only repos for the first release wave.
- Publish merged 16-bit or GGUF artifacts only as deliberate reference releases.
- Failed or diagnostic runs belong in analysis docs/eval artifacts by default,
  not as model repos.
- Use lowercase, queryable names:
  `professorsynapse/eh-qwen3-4b-clean-sft-grpo-seed1-lora`.

## Upload command shape

From `synaptic-tuner/`, use the tuner wrapper:

```bash
python .skills/upload-deployment/scripts/upload_model.py \
  PATH/TO/final_model \
  professorsynapse/eh-qwen3-4b-clean-sft-seed1-lora \
  --save-method lora \
  --training-lineage PATH/TO/training_lineage.json
```

The upload command needs `HF_TOKEN` with write access. Do not add another
uploader to this repo unless the tuner capability is missing and the user
approves a generic tuner enhancement.

## After upload

Update `docs/public-artifacts.md` with:

- HF repo URL
- HF revision SHA
- local run record path
- eval result path
- caveats or license exclusions

If the artifact belongs to an experiment note, add the HF repo/revision to that
note's Outputs & provenance section after the upload succeeds.
