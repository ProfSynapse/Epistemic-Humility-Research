# R2 execution runbook

The experiment is signed on delegated PI authority. The machine pins in
experiment.yaml remain the admission boundary.
Use AMENDMENT.md and astra_r2.yaml for the scientific contract. No R2 target
weight edit or inference has run.

## Pinned environment and inputs

Use the registered desktop image with the project mounted at /project.
The installed engine and host binding are in runtime/r2_host_binding.json.
Models and checkpoints stay under E:/Models/Epistemic-Humility-Research.
Private run products stay under E:/SynapticResearch. Source data, grades,
transcripts and tensors never go in public Git.

Mount the shared capture bundle read-only at
experiments/common/captures/astra-r1/analysis/private_bundle. The public
origin.json pins all 308 members. Mount the separate original calibration
bundle read-only at experiments/common/captures/astra-r1/analysis/decoys.
Its 25 positive and 25 negative examples keep the original frozen hash.
Mount the original model read-only at the artifact shared/base_model path.
Mount an existing T7 model-output parent at astra-r2/checkpoints; the edited
subdirectory must not exist before preparation. Never use symlinks for mounts.

## Pre-sign checks

From the experiment directory in the pinned container, use:

```sh
python -m r2_runtime.astra_run --project-root /project prepare --dry-run
python -m r2_runtime.astra_run --project-root /project materialize \
  --fit /project/experiments/common/captures/astra-r1/analysis/private_bundle/raw/fit.jsonl \
  --selfaware /project/experiments/common/captures/astra-r1/analysis/private_bundle/raw/SelfAware.json \
  --ambigqa /project/experiments/common/captures/astra-r1/analysis/private_bundle/raw/ambigqa_validation_screened.jsonl
python -m r2_runtime.astra_run --project-root /project preflight \
  --model /project/.synaptic/artifacts/qwen35-4b-astra-broader-weight-edit/shared/base_model
```

Dry-run resolves real inputs and verifies their hashes. Materialization strips
old responses and creates the R2 roster and benchmark inputs. Preflight loads
only the tokenizer. The actual readiness run passed all eight original/retry
prompt checks; the maximum was 310 tokens against context 2048.

Keep the immutable CPU test copies and failed attempts on T7. The V6 report
covers the first 97 tests and review repairs. Later preparation tests extend
that evidence; use their exact retained report and source hashes for signing.

## One construction, then freeze

After signed source and input doctor checks pass:

```sh
python -m r2_runtime.astra_run --project-root /project prepare
```

This command authenticates inherited capture, constructs the single fixed-dose
proposal, invokes public weights-patch validation/export, audits stored tensor
bytes and stages the exact original twenty qualification rows. It has no GPU
inference stage. It returns freeze_pending only after the complete chain passes.
Every claim/output is create-only. Partial or refused attempts remain retained;
no automatic replay, alternate output, rescale or replacement proposal exists.

Freeze with the exact refs in runtime/preparation.yaml. The construction report
is astra-r2/construction/report.json, and spec/payload are in construction/patch.
The freeze authenticates the inherited handoff and all preparation phases.
Commit the public hash-only patch freeze before any benchmark generation.

## Edited qualification and evaluation

The actual edited-model qualification remains required after freeze: original
twenty unscored rows, two repeats of two orders and owned SIGKILL/resume, at most
120 requests. Commit both the exact qualification receipt and its manifest.
The signed qualified:false field stays unchanged; committed evidence admits use.

Only then run eight cells in registered order through astra_run eval-cell.
Persist every request and token result. Do not inspect interim arm deltas.
Commit the blinded pool before grading, commit raw grade hashes before unblinding,
complete the blind write-once spot check, then run the frozen roll-up.
The r2_runtime/README.md is the earlier port handoff, retained as history.
