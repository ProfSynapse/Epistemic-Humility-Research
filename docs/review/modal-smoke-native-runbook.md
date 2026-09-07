# Modal prepared-path smoke: native Host runbook

## Status and ruling (2026-09-07)

The user selected direct native submission, without local Docker. This replaces
the execution commands in modal-smoke-runbook-34d6623d.md, which remains historical
evidence. It does not authorize cloud operations, key rotations, pushes or merges.

Candidate based on Host 9c77d492, engine 5db2809d. Do not execute candidate
provider commands from the edit worktree or mix candidate and released modules.
After independent review, an approved push and a new clean release, record the
full Host SHA and engine gitlink before the following steps.

The installed operator CLI is not the paid-submit boundary. The Host enters
its existing hash-pinned Linux runtime and retains one-use launch authority,
committed-source admission, evidence signing, budget grants and durable effects.
The remote Modal training container is unchanged. Windows-native submission is
not implemented by this Linux launcher; WSL is the selected native lane.

## Scope and credentials

Run one SmolLM2 job at the committed model revision, budget USD 1.00, timeout
3600 seconds, no retry, profile modal-a10-v1. Stop before publication.
Use only environment synaptic-smoke-v1, control Volume
synaptic-training-control-smoke-v1, artifact Volume
synaptic-training-artifacts-smoke-v1 and Secret synaptic-training-runtime-smoke-v1.
Never list or inspect the old environment or its objects.

The verified isolated child reads the selected saved Modal login only when
neither explicit token environment name is present. Partial or invalid explicit
pairs refuse rather than select another account. No credential values or lengths
may appear in commands, logs or new files. Do not print configuration objects.
HF_TOKEN remains separately required for deployment, supplied through the
approved process-environment mechanism. The saved Modal login does not supply it.

Every credential-bearing/provider/key operation below needs a fresh approval
of the exact command. Commands are templates until the new release and all
preconditions are verified. No permission is implied by this document.

## Step 0: release admission

Confirm clean Host and engine trees, the approved full Host SHA, the unchanged
engine gitlink, and the intended remote branch. Use the explicit git.exe binary
for Git mutations on F:. Never modify either historical release in place.

## Step 1: native gates (credential-free)

From the new release:

```bash
python3 -B .skills/host-modal-run/scripts/g2_native_host.py --prepare-runtime
python3 -B .skills/host-modal-run/scripts/g3_engine_lock_digests.py --expect 0
python3 -B .skills/host-modal-run/scripts/g5_isolation_triple.py
```

The explicit prepare option permits the existing pinned uv/Python bootstrap
to populate the release's ignored private cache. No Conda environment, Docker
image or local container is involved. Without that option G2 only verifies.
G2 must pass actual runtime proof and isolated SDK/source checks. G3 must report
zero committed-blob mismatches. G5 S1-S3 must pass; S4 must refuse until rotation.
Do not fabricate an attestation to obtain a green gate.

Before steps 3 and 4, repeat credential-free signature binding in the newly
prepared interpreter for every entry used by those direct-invocation snippets.
Import the same modules, bind required and supplied arguments, reject **kwargs
loopholes, and run negative controls. Historical container signature probes do
not replace this native-runtime check. This precondition is currently UNMET.

## Step 2: create and verify the dedicated environment

Approve creation separately, then use the pinned native CLI:

```bash
.synaptic/cache/modal-launcher-v1/bin/python -m modal environment create synaptic-smoke-v1
```

For verification, approve a lookup of only Environment.from_name with the
exact dedicated name, create_if_missing=False and one explicit client; hydrate
that handle. Do not use an environment/workspace listing. A collision is a stop,
not permission to adopt, replace or delete anything.

## Step 3: rotate the Host evidence key (direct invocation)

After the native signature precondition and exact-command approval:

```bash
.synaptic/cache/modal-launcher-v1/bin/python -B - <<'PY'
from pathlib import Path
import sys
from datetime import datetime, timezone
root = Path.cwd().resolve()
sys.path[:0] = [str(root), str(root / 'synaptic-tuner')]
from tuner.project.manifest import load_project_manifest
from synaptic_host.modal_key_rotation import rotate_host_evidence_key
manifest = load_project_manifest(root / 'synaptic.yaml')
context = manifest.create_context(engine_root=root / 'synaptic-tuner', invocation_cwd=root)
authenticator = rotate_host_evidence_key(context)
print('host_key_rotated')
print(datetime.fromtimestamp(authenticator.key_path.stat().st_mtime, timezone.utc).isoformat())
PY
```

Record the timestamp. Runtime bootstrap may already have created .synaptic/cache;
its presence is not evidence of an existing key. Inspect only the exact Host and
worker key paths for existence, not their contents. If a worker key already
exists, stop for a separate decision; do not delete it implicitly.

## Step 4: deploy the dedicated objects (direct invocation)

Require the approved HF_TOKEN environment mechanism, successful native signature
probes, fresh Host-key attestation and exact-command approval:

```bash
.synaptic/cache/modal-launcher-v1/bin/python -B - <<'PY'
from pathlib import Path
import os
import sys
root = Path.cwd().resolve()
sys.path[:0] = [str(root), str(root / 'synaptic-tuner')]
from tuner.project.manifest import load_project_manifest
from synaptic_host.modal_provider import ExplicitModalHostSession, ModalHostConfigV1, build_worker_authenticator
from synaptic_host.modal_credentials import select_modal_credentials
import modal
pair = select_modal_credentials(os.environ, allow_saved=True)
if pair is None or not os.environ.get('HF_TOKEN', '').strip():
    raise SystemExit('deployment credentials unavailable')
manifest = load_project_manifest(root / 'synaptic.yaml')
context = manifest.create_context(engine_root=root / 'synaptic-tuner', invocation_cwd=root)
config = ModalHostConfigV1.load(context)
session = ExplicitModalHostSession.from_credentials(sdk=modal, config=config, token_id=pair[0], token_secret=pair[1])
worker = build_worker_authenticator(context)
session.deploy(context=context, authenticator=worker, hf_token=os.environ['HF_TOKEN'])
print('deployed')
PY
```

This creates the two Volumes and worker-key Secret and deploys the app in the
dedicated environment. The Host key is never uploaded. Preserve deployment
journal and provider-state.json; never remove them to force a retry. A partial
failure requires inspection of exact local state and a new recovery approval.

## Step 5: live G5

After exact-command approval:

```bash
.synaptic/cache/modal-launcher-v1/bin/python -B .skills/host-modal-run/scripts/g5_isolation_triple.py \
  --check --rotation-recorded-at '<recorded-timestamp>'
```

Require all four named lookups and all offline checks. No local Docker process
is started. Live account behavior is still UNVERIFIED.

## Steps 6 and 7: optional dry run, then one paid submit

The dry run is not a gate. Do not invent flags on the closed Host parser.
Once all pre-submit gates and native checks pass, seek approval of this exact
eight-token Host command from the approved release:

```bash
python3 -m synaptic_host training run \
  --provider modal \
  --config project://training/smokes/modal-sft.json \
  --destination provider-staging
```

Budget, timeout and retries remain committed configuration, not new flags.
Never call a raw Modal function to bypass Host admission. On an interrupted or
ambiguous submit, reconcile the durable effect before any proposed retry; an
unsuccessful local exit does not prove no paid job started.

## Steps 8 and 9: observe, stop and verify

Approve credential-bearing observation of only the dedicated app:

```bash
.synaptic/cache/modal-launcher-v1/bin/python -m modal app logs synaptic-training-v1 -e synaptic-smoke-v1
```

If early stopping is needed, request separate approval of the corresponding
app stop command with the same explicit environment. Never touch the old app.
Read run-acceptance evidence, verify lifecycle and artifacts, sweep logs by
credential shape, and stop before publication. Do not run retire_worker_channel.
Record results, audit before any push, and ask about old-app teardown at closeout.

## Measured and unverified

Measured at released 9c77d492 before native edits: saved login ready (local-only);
native committed-source reader passes; a fresh credential-free private directory
chain on F: passes; the old launcher rejects the long inherited PATH. No provider
request, key rotation or paid submit occurred. Probe directories alone were removed.

The candidate's fake-backed tests cover fixed PATH, saved-profile selection,
proof-before-login ordering, explicit-pair refusal, closed diagnostics and native
G5 routing. They do not establish a working native cache bootstrap or live account.
The new clean release, full native G2 bootstrap, direct-invocation signature probes,
HF_TOKEN handoff, environment creation, rotation, deployment, live G5 and paid
run remain UNVERIFIED. No container, image or cloud object was deleted.
