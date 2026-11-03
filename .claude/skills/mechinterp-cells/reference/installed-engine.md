# Installed engine for new cells

Read `docs/architecture/tuner-api-v1-migration.md` for installation and boundaries.
Install both the reviewed engine wheel and EHR's host package in one dedicated
environment. `ehr-engine doctor` must report an installed package, not the
historical submodule. Run `ehr-engine cli project validate --json` before work.

New Python consumers import only `synaptic_tuner.api.v1` public contracts.
MechInterp and batch verbs remain a separately pinned CLI boundary:

```bash
ehr-engine plan-pipeline project://experiments/<slug>/pipeline.yaml
ehr-engine cli mechinterp run --config project://experiments/<slug>/pipeline.yaml --provider local --yes
```

The second command is a launch and requires the user's existing authorization
for that concrete experiment and lane. Preserve the normal GPU acknowledgment,
smoke and signing gates. The boundary adds no approval flags automatically.
Never use `steer --dry-run` as a planning command; use pipeline `run --dry-run`.

Source reads use `project://`. Private outputs use `artifact://<slug>/...`.
Bare relative paths are config-relative; historical repo-relative recipes must
not be copied unchanged into host mode. Render and grader directories are
project plug-ins, never tuner source paths on `PYTHONPATH`.

New generation harnesses use `engine_host.generation_log.open_generation_runlog`.
Every non-textless record retains generation text. Preserve fingerprint checks,
fsynced per-row writes, the kill-resume smoke drill and signed persistence
declarations. The old `runlog_contract.py` is reserved for pinned consumers.

Local GPU work uses the reviewed derived runner image, including the exact
installed engine and its base dependencies. Record its digest separately from
model revision, config hashes and wheel/source identity. On the desktop, use
the caller-configured T7 E: paths. Do not infer engine readiness from images in
the native WSL Docker store; verify the active daemon identity.
Use `runtime/mechinterp/preflight.py` for the synthetic forward-only capture
smoke before a new local instrument; see its runtime README. It loads through
the installed CLI and records no scientific result. Set `EHR_HOST_CONFIG` for
the real local run so host cache/output checks apply.

New behavior remains config-first. A missing generic runtime capability belongs
in a Tuner branch, never a project-specific import of its internals. Stable v1
does not include RunLog, MechInterp, batch capture, DPO or KTO. Keep historical
training lanes pinned and label their evidence separately.
