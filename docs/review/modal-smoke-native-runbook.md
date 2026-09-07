# Modal prepared-path smoke: native Host runbook

## Automatic model preparation repair (2026-09-07)

Correction: the proposed fourth job from Host c6ea2885 was held before submit.
Code inspection showed that the worker created a fresh empty cache and then
required an existing offline model snapshot. No downloader or model copy ran
between those steps. This is a pre-submit finding, not a fourth cloud failure.

Engine repair `2c4ef885f03673ebb1308db1fbf67ffc5f029ee9` adds automatic
preparation inside the Modal worker. The official Hub SDK downloads missing
members of the exact configured revision into private remote scratch. Ordinary
repository files in the existing artifact Volume's `model-cache` namespace are
reused only after fresh upstream metadata and content-hash verification. SDK
filesystem writes never target the shared Volume. The run receives a verified,
link-free snapshot; both named runtime secrets remain in the wrapper and are
absent from the offline trainer child. The artifact Volume is committed before
trainer launch, preserving the cache if training fails. No new Volume, manual
laptop download/upload, dependency upgrade, cache index or downloader service
is introduced. Local prepared training has not yet been wired to this helper.

Measured candidate checks: 280 engine tests passed, with the same two historical
failures recorded below; all 104 Host Modal provider/training tests passed.
The official Hub 0.36.0 wheel was downloaded without installation for the
credential-free signature and ModelInfo contract checks. Those passed. Runtime
image digest, lock hashes, exact offline closure, budget, retries and source
admission remain enforced. Independent engine security/correctness review
accepted the repair. Live success remains unverified.

Private evidence: `/mnt/f/Code/ehr-modal-model-preparation-evidence.Hb8UXe`.
This section supersedes the lower next-engine pin. The unused request remains
`project://training/smokes/modal-sft-local-control.json`; it has not consumed
submission authority. Preserve all three earlier effects and their state.
Use a fresh clean release with reviewed/pushed source, G2/G3/live G5, and an
upgrade of only the existing dedicated deployment before its bounded submit.

## Local worker-control repair (2026-09-07)

Correction: Host 5857620259c045d02fe8aa5e736c15ec891247dd with engine
8bd49875f021b2e1a5f26bff887eaffd050f2fc0 submitted the third actual job
successfully at 2026-09-07T20:16:52Z. The Host hydration repair is live-proven.
Run `run-c6938bcbc603e2eab03966fa4dbfc0ed`, effect
`effect-7183f9a6462638d8cf4361c0fb16511b`, call
`fc-01M1YR8EBHRFGK532HKHGYPN5E` then reported authenticated FAILED at
2026-09-07T20:18:27Z with `worker_control_path_noncanonical`, zero verified
artifacts. The engine canonical-path check passed before the control-path
check failed. This proves the control path alias; its target was not exposed.
Private evidence and an integrity-checked terminal ledger backup are at
`/mnt/f/Code/ehr-modal-staging-evidence-58576202.ZynItK`.

Reviewed and pushed engine repair 4fbb3879f74b8b2c34813345bb0e92337cc9c47b
moves only the authenticated bootstrap closure copy to local
`/workspace/worker-control`. Durable claim/MAC/log/evidence paths stay on the
existing control Volume. All four invocation/verification path bindings agree;
canonicality, exclusive writes, closure digest, member hashes and exact
inventory remain enforced. Local checks: 259 passed, the same two historical
failures below. The alias regression reproduces the old failure and passes
with local bootstrap storage. Independent security/binding review passed;
cloud training success is still unverified.

The user's latest instruction reaffirms routine reviewed repair pushes,
the known scoped Host hook exception for missing unrelated experiment inputs,
and bounded smoke iterations without further routine prompts. Stop only for
a genuine safety, material cost or unresolved-submission issue. Main merge,
publication, destructive teardown and old-environment access remain excluded.
This section supersedes lower next-attempt request/engine pins. Preserve every
consumed effect and use a fresh clean release at exact pushed source, existing
state/keys, provider upgrade and G2/G3/live G5 before the next distinct request:

```bash
python3 -m synaptic_host training run --provider modal --config project://training/smokes/modal-sft-local-control.json --destination provider-staging
```

Its training bytes equal the original; USD 1.00 configured budget, one step and
zero retries are unchanged. No fourth job has run yet.

## Staging diagnostic iteration (2026-09-07)

Correction: the second actual job, submitted from Host
27ec52c54b9133781d31161103a5a9687d87a081 and engine
8b9b121b35abe96e5dc982f64e0126b02ed31f68, is terminal FAILED with
`locked_source_mismatch`, zero verified artifacts, at 2026-09-07T18:35:52Z.
Its run is `run-ab1e858b06f3374625b47263063b1d3c`, effect
`effect-8cfe95e0d1577bbd1fa804fb88e39134`, call
`fc-01M1YJCSRCS2W5BJE5JYKVM4PQ`. Its replacement request below is consumed;
do not submit it again. Provider wrapper SUCCESS does not mean training success.
Private evidence is retained at
`/mnt/f/Code/ehr-modal-replacement-evidence-8b64eac9.fwLeZx`.

The downloaded closure manifest matches committed bytes. Staging a canonical
full clone passes locally; aliased engine/control paths reproduce rejection,
but the remote cause is not yet proven. Reviewed engine commit
8bd49875f021b2e1a5f26bff887eaffd050f2fc0 adds closed staging diagnostics
without relaxing canonical-path, member-hash or exact-inventory checks.
Local engine checks: 257 passed, the same two historical failures recorded
below. The Host hydration repair separately passed 9 targeted and 104 existing
tests and independent review. It hydrates the lazy Modal call handle with the
captured explicit client, then revalidates authority and exact job identity;
it does not submit or read results.

For the next bounded diagnostic attempt, use the new committed request below,
byte-identical to the original training config. This section supersedes lower
next-attempt engine and request pins; previous commands remain historical.
The user's routine bounded-smoke authorization remains as recorded below.
Push approval is separate. Require exact reviewed/pushed source, a fresh clean
release, existing gates and provider upgrade before submission. Preserve both
consumed effects and all keys/state; do not reset the ledger or redeploy fresh
resources. The user reported stopping the app after the terminal failure;
verify only the dedicated deployment when upgrading. No third job has run yet.

```bash
python3 -m synaptic_host training run --provider modal --config project://training/smokes/modal-sft-staging-diagnostic.json --destination provider-staging
```

## Replacement authorization (2026-09-07)

After reviewing the failed attempt, the user authorized proceeding with the
replacement and routine bounded smoke iterations without repeated permission
prompts. The next attempt uses the reviewed engine repair
8b9b121b35abe96e5dc982f64e0126b02ed31f68 on
`fix/modal-prepared-worker-closure`. The historical 5db2809d release ref stays
unchanged. Keep each attempt separately durable, preserve its evidence, retain
the configured USD 1.00 budget and retries=0, and reconcile every uncertain
submission before considering another. Stop for meaningful cost escalation,
destructive action, or unresolved duplicate-submission risk. Publication and
main merges remain prohibited. This supersedes the per-attempt approval pauses
below; it does not reopen the first effect's consumed authority.
For the replacement, this section also supersedes the lower first-attempt
instructions for further user authorization, the 5db2809d engine pin, Host-key
rotation, and fresh-resource deployment. Those instructions remain historical
for the consumed first attempt; the Host must still issue fresh one-use durable
authority for each newly authorized effect.

Reuse the existing dedicated environment, Volumes, Secret and worker/Host keys.
Use the existing `ExplicitModalHostSession.upgrade(context=..., authenticator=...)`
workflow to update provider code and retain prior deployment records. Do not
delete provider-state.json or redeploy through the fresh-resource path.

The identical original CLI request returns its consumed first effect even after
the source/deployment upgrade; the config reference is part of the durable
ingress identity. For this replacement, use the separately committed
`project://training/smokes/modal-sft-prepared-replacement.json` request, whose
bytes and training settings equal the original. Do not clear the ledger or
change runtime idempotency. The replacement command is:

```bash
python3 -m synaptic_host training run --provider modal --config project://training/smokes/modal-sft-prepared-replacement.json --destination provider-staging
```

The original-request invocation at Host 50966021 returned the first job's
RECONCILE_REQUIRED envelope without submitting a new paid job. The dedicated
provider upgrade and G2/G3/G5 checks at that release passed; retain its state
for the new config-only release rather than upgrading the provider again.

## Terminal correction (2026-09-07)

The authorized single paid attempt has been consumed. Do not run the submit
template below again under that authority. The job failed before training;
no model artifact was produced or published. Exact execution source was Host
6557b9b7be0bb8e7080787e98743c9b1b5425b86 and engine
5db2809d0160b166a0d2b133b97368ddcfe426ce, from the clean native Linux release
`/home/profsynapse/code/ehr-release-6557b9b7`. G2, G3, live G5, both exact
remote source refs and native signature probes passed before that submission.
The historical UNMET signature banner below does not describe that attempt.

Run `run-e6a70f05a9fbd736b6f2a0e39bf3e29d`, effect
`effect-477d9870083b78ab1d37707a77e07d22`, Modal call
`fc-01M1YEJM7CZRFXDKBXZSCYM4DH`: authenticated outcome FAILED with closed code
`runtime_workload_engine_rejected`. The CLI initially reported
RECONCILE_REQUIRED after submission; public outcome reconciliation recovered
the terminal result. No second job was submitted.

Two independently reviewed repairs are local, not cloud-proven: Host commit
8d8e9612 pins the stable Modal 1.5.4 descriptor and callable bindings instead of
fresh partial-wrapper identity; engine commit
8b9b121b35abe96e5dc982f64e0126b02ed31f68 retains the verified full checkout and
stages the exact authenticated worker closure before invocation. The released
full checkout had extra files beyond the required 66 members. The engine repair
updates the packaged Modal runtime lock without changing the offline closure.
Neither repair relaxes source, identity, credential or exact-file validation.

Operator-observed post-restart Host candidate tests: 7 new and 104 existing PASS. Engine candidate focused
checks: 45 PASS, one unchanged symlink-error wording failure. Broad Modal provider
checks: 236 PASS, two failures, both reproduced individually at released engine
5db2809d: `test_mounted_reads_and_writes_reject_symlinked_ancestors` and
`test_finalizer_rejects_symlink_or_reparse_roots`. These failures remain open;
they are not represented as passing gates. Skill mirrors and runtime-lock
digest tests pass. Candidate tests used the released working directory with
explicit candidate imports, not provider calls from the editing checkout.
The retained Host test transcript predates the two additional regression tests;
the current totals and baseline reproductions above were observed in terminal
tool results, not independently reconstructed from retained test transcripts.

Private records are retained at
`/mnt/f/Code/ehr-native-smoke-evidence-5355d32f.EFevfy`, including authenticated
terminal/log files and a terminal SQLite backup whose integrity check was
operator-observed PASS. A shape
sweep of the saved console logs found zero Modal/HF token-prefix matches;
generic matches were hexadecimal digests and file paths. Synthetic positive
controls passed. This is not a claim about uncaptured output or arbitrary
secret formats. Existing keys, deployment records and cloud objects remain
intact; the old environment remains unread and untouched.

A further paid attempt needs new submission authority, exact reviewed/pushed
Host and engine refs, a fresh release, updated deployment/runtime proof and
the existing gates. Do not move the historical engine release ref, reuse the
consumed effect, or substitute a manual Modal launch. Publication remains out
of scope.

## Status and ruling (2026-09-07)

Correction after live deployment: the user authorized routine provisioning and
one bounded smoke without repeated approval pauses. Stop for collisions,
duplicate-spend risk or material decisions. Preserve the USD 1.00 job limit,
old-environment isolation and stop-before-publication boundary. For this smoke,
this authorization supersedes every per-step approval pause below for routine
preparation, provisioning, rotation, deployment, observation and the single
bounded submit. Older per-step approval wording below is historical for this
run, not an additional gate. Pushes, merges, publication and material recovery
remain separately controlled; no permission to retry an ambiguous job is implied.

Source verification requires a named Host branch whose exact remote ref equals
the release commit; detached Host HEAD is insufficient. The engine remains
pinned to 5db2809d0160b166a0d2b133b97368ddcfe426ce. Its dedicated upstream is
release/modal-smoke-5db2809d because feat/submodule-cloud-api-v1 advanced.
This changes the branch reference only, not engine code or the gitlink.

The user selected direct native submission, without local Docker. This replaces
the execution commands in modal-smoke-runbook-34d6623d.md, which remains historical
evidence. This document records the user's scoped authorization above; it does
not grant general authority over other cloud objects, pushes or merges.

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

Commands remain templates until the new release and all preconditions are
verified. Routine credential-bearing/provider/key operations for this one smoke
are covered by the user's authorization above. Stop for a material scope change,
collision, ambiguous submission or unsafe recovery.

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
