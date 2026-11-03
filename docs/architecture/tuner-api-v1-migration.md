# Current Tuner integration

New work uses an installed Synaptic Tuner engine. The historical
`synaptic-tuner/` gitlink stays at its signed pin. A package version, source
commit, wheel hash and runtime image digest are separate identities; record
each actual value in the run manifest. An import check does not qualify GPU
execution or grant authority to run.

## Install and inspect

Install a reviewed engine wheel in a dedicated Python environment, then install
this host without resolving a different engine from PyPI:

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python 'synaptic-tuner @ file:///absolute/reviewed-engine.whl#sha256=<reviewed-wheel-sha256>' pytest
uv pip install --python .venv/bin/python --no-deps .
.venv/bin/python -I -m engine_host doctor
.venv/bin/python -I -m engine_host cli project validate --json
```

For engine development, building from a clean, reviewed source commit is also
supported. Record that source commit and the actual built wheel digest. Do not
describe a local build as the published release artifact. `synaptic.yaml`
explicitly admits prerelease API v1 engines; stable-only `>=1,<2` refuses the
current release candidate.

The root manifest pins the locally built weight-edit extension from Tuner PR
281. Its version is also `1.1.0rc1`; the wheel hash distinguishes it from the
base release. Install the exact retained wheel, or review a new build and update
both its source commit and wheel pin before use. `doctor` checks that pin and
the installed files against RECORD. It reports direct-URL provenance and the
declared source commit; the source-commit association comes from the reviewed
build ledger, not an independent Git checkout inspection. Directory installs
without a wheel hash are refused by the experimental CLI. With uv, use the
named direct reference above so its hash remains in installation provenance.

The host package is installed independently of the engine. Its modules are
under `experiments/common/engine_host/`; they import public v1 contracts only.
They never add the historical engine to Python's search path.

## Supported boundaries

- Training uses `TrainingInputV1`, `TrainingAPI`, `ProviderRef` and `RunsAPI`.
  `load_training_input` validates canonical inputs. `plan_training` calls the
  caller-composed public API and never starts a run. Provider composition,
  prepared material, storage and grants remain explicit caller responsibilities.
- API v1 admits SFT and GRPO. Actual method/provider/model/runtime combinations
  must also be qualified. DPO, KTO and the locked matrix retain the historical
  engine; this migration does not pretend they have a v1 training contract.
- Data and Evaluation public families are available for new host consumers.
  Existing cell-local grading and data-exhaust publication are separate
  workflows and are not relabeled as DataAPI or EvaluationAPI execution.
- MechInterp and batch generation/capture use `engine_host.cli_boundary.EngineCLI`.
  They remain checkout/version-specific CLI interfaces, outside the stable
  Python v1 promise. The boundary preserves explicit GPU and launch flags.
  It never inserts `--yes` or `--i-know-this-runs-on-gpu` automatically.
- The host owns a format-compatible `RunLog`, ported verbatim from historical
  engine `6b01834b8192d1d875db9bfce3eaa8fd9e14334c` (MIT). Its source SHA256 is
  `ba74ccfc464954b718b2ac1bf9a1b867eed0c5959afd77b8d9fc784c1d45a415`.
  New generation code uses `engine_host.generation_log.open_generation_runlog`.
  The older `experiments/common/runlog_contract.py` stays untouched for pinned
  consumers.

## Paths and storage

New configuration reads use `project://experiments/<slug>/...`. Private output
and fitted-artifact paths use `artifact://<slug>/...` under `.synaptic/artifacts`.
Bare relative paths resolve from their declaring configuration, not necessarily
the repository root. `project://` paths are source, never output destinations.

Project plug-ins are EHR code. Supply their exact project-owned directories to
`EngineCLI(plugin_roots=...)` or the pipeline's declared Python paths. Never add
the tuner checkout to `PYTHONPATH`.

The desktop host is configured in `configs/hosts/desktop-3090.yaml`.
The owner selected T7, Windows E: (`/mnt/e`), for new models and checkpoints.
Run the new project snapshot on that drive so `.synaptic/` outputs remain both
inside the host project and on T7. Existing model caches and old checkouts are
read-only sources. Do not substitute F: or the video-render staging directory.

The atlas template now reads this host file, refuses an off-drive project,
sets `HF_HOME`, `HF_HUB_CACHE`, `TORCH_HOME` and temporary paths on T7 before
tokenizer loading, and reuses the matching local snapshot after shard-hash
verification. Set `EHR_HOST_CONFIG` to the reviewed host file for other local
GPU launchers; `EngineCLI.run` then validates and applies the same paths. Bind
those exact directories into the container. `ehr-engine host-storage --config
configs/hosts/desktop-3090.yaml` checks this selection. It deliberately fails
on this server, whose project root is not on the desktop's T7 mount.

The manifest's policy keys express intent. Engine 1.1.0rc1 does not enforce all
of `external_paths`, `engine_writes`, `source_writes` and `dirty_sources`.
They are not an OS sandbox or proof that a command cannot write a source file.
Use explicit project/artifact references, EHR's host checks, reviewed command
stages and container mounts. Absolute model snapshot reads selected by the
desktop host file remain explicit read-only sources. The manifest's path
resolver still constrains writes that use its writable path surface; do not
generalize that to arbitrary command-stage programs.

Manifest `inputs` for new private artifacts must use the explicit local mapping,
not a repository-input string:

```yaml
inputs:
  - path: .synaptic/artifacts/<slug>/rows.jsonl
    availability: local
    source: <producer and source manifest>
    sha256: <actual sha256>
```

Portable validation permits those bytes to be absent; `bin/exp doctor <slug>`
must verify them on the execution machine. The old analysis/directions string
exemption applies only to historical layouts.

The data harvester includes `.synaptic/artifacts/` and `.synaptic/tracking/`.
It deliberately excludes host authorization state and model caches. Exported
model/checkpoint retention is an explicit run responsibility; never remove a
worktree or run directory while it holds the sole copy of required artifacts.
It discovers Git worktrees, not arbitrary T7 snapshots. A detached project
snapshot therefore needs an explicit verified copy-back and inventory before
removal; a passing harvester scan is not retention evidence for that snapshot.

## Plan and test

```bash
ehr-engine plan-pipeline project://experiments/<slug>/pipeline.yaml
.venv/bin/python -m pytest experiments/common/engine_host/tests -q
python3 bin/sync_skills.py --check
bin/exp validate
```

Reinstall this host after every source edit before running installed-consumer
tests. A test compares the installed host modules to the reviewed source bytes.
The weights verbs are tested against the actual installed parser. Packaged
`mechinterp list-configs` may have no engine templates; EHR owns its source
configs and does not use that output as a capability check.

Only `mechinterp run --dry-run` is a supported pipeline plan. Direct
`mechinterp steer --dry-run` is not a safe planning command. Planning is not
launch authority. Existing smoke, revision, manifest, resumability, grading and
experiment-signing checks remain required before effects.

## Migration scope

Signed scripts, common scripts pinned by experiments, the historical matrix,
archived outputs and the submodule gitlink remain unchanged. Prospective skills
and the family-atlas template use the installed boundary. Generic engine gaps
are implemented in Tuner, on its own branch, with no EHR model/site assumptions.
The native-weight-edit experiment additionally requires reviewed patching,
patch-export, module-capture, revision-forwarding and installed-pipeline fixes;
base release import success does not establish those capabilities.
