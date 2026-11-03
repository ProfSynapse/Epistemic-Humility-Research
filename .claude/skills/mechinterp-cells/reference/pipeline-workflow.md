# Current pipeline workflow

New cells use the installed EHR host and reviewed engine. Read
[installed-engine.md](installed-engine.md) before this workflow. Historical
signed pipelines retain their original engine and bytes; reproduce them with
their registered pin rather than editing them to fit host mode.

## 1. Configure

A `mechinterp-pipeline/v1` pipeline belongs in `experiments/<slug>/pipeline.yaml`.
Use the current engine's actual schema and commands; inspect command help and
the EHR-owned configs. The installed wheel may not include engine templates,
so `list-configs` is not a capability check.

- Stage `config`, source rows and readout references use explicit
  `project://experiments/<slug>/...` or the appropriate `artifact://` reference.
- Private generation outputs and fitted readouts use `artifact://<slug>/...`.
- Pipeline command stages name checked-in project programs. Keep model
  revision, render, grader, generation settings and engine identity explicit.
- Declare only project plug-in directories in `runtime.pythonpath`.
- Never copy a historical bare repo-relative path into a config-relative field.

Kinds include `mechinterp.extract`, `mechinterp.probe-fit`, `mechinterp.steer`,
`mechinterp.dose-calibrate`, `mechinterp.score-gates`, and project `command`
stages. Inspect actual model-revision forwarding on the installed build before
using a pinned calibration; the base 1.1.0rc1 path needs the reviewed revision fix.
The root manifest pins that extension by wheel SHA256 as well as version.

## 2. Plan without effects

```bash
ehr-engine doctor
ehr-engine cli project validate --json
ehr-engine cli capabilities list --json
ehr-engine plan-pipeline project://experiments/<slug>/pipeline.yaml
```

Pipeline `run --dry-run` is the planning boundary. Direct `steer --dry-run` does
not implement this contract. Do not import `MechInterp.config` through a tuner
checkout to simulate planning.

The installed build must include the pipeline-module entrypoint fix. Base
1.1.0rc1 compiles child commands through an unpackaged `tuner.py`; a passing
manifest check alone is not evidence that installed pipeline stages can run.

## 3. Smoke and run

Pre-state the prediction, falsifier and gates before evidence generation. Record
config/module hashes, model revision, engine wheel/source identity, runtime
image digest and declared persistence through the experiments skill.

Use the pinned container for desktop GPU verbs. The user-selected T7 E: drive
holds the new project snapshot, models, checkpoints and `.synaptic/` artifacts.
Verify Docker Desktop's actual daemon and image store before capturing its digest.

A steering smoke must establish realized write accuracy and correct hook firing.
It does not establish behavioral effect. Preserve the engine's smoke-pass marker,
config identity and resume fingerprint checks. Never bypass them with
`--force-full-run` on a signed instrument.

```bash
# Only after the concrete experiment/lane is authorized and the instrument is pinned:
ehr-engine cli mechinterp run --config project://experiments/<slug>/pipeline.yaml --provider local --yes
```

The host boundary does not add `--yes` or GPU acknowledgments. Supply the
engine's actual required flags explicitly for the selected verb. Modal or other
paid lanes require their separately authorized launch and current runtime policy.

## 4. Preserve and adjudicate

New project generation loops use
`engine_host.generation_log.open_generation_runlog`: retain nonempty generation
text, flush/fsync every record, verify resume identity, and perform a real
kill-resume drill for an incremental signed module. Long desktop processes use
the checked-in detached launcher; write PID, exit status and progress artifacts.

Use the registered graders and blinded adjudication lane on both benefit and
cost populations. Score with the registered instrument; never infer success
from exit code, GPU idleness or a progress line. Read actual summary/verdict
artifacts. Keep source text and raw outputs private under `.synaptic/artifacts`.

Before worktree cleanup, harvest private artifacts and tracking through
`bin/harvest_worktree_data.py`. Model caches and host authority state are not
harvested; preserve required exports explicitly. Retain old instruments byte-for-byte.
