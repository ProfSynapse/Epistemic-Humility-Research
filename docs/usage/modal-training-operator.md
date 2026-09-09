# Modal SFT operator guide

This is the operator guide for the narrow native Linux/WSL to Modal A10 SFT
path. It covers admission, one bounded submission, durable observation, and
reconnect. It does not make native Windows Python, Docker, publication,
teardown, or arbitrary Modal administration part of the supported path.

## Release prerequisites

Work only from a clean, reviewed release checkout whose Host commit is pushed
on the intended feature integration branch. Its `synaptic-tuner` gitlink and
the checked-out engine HEAD must be the same reviewed, pushed commit. Do not
export `PYTHONPATH`, run from an edit worktree, or substitute uncommitted files.

Use Linux x86_64 or WSL. The Host enters its hash-pinned CPython 3.11.15
launcher with Modal SDK 1.5.4. Do not use Docker, a global Modal CLI runtime,
or a direct provider call in place of that launcher. Model files are prepared
inside the remote wrapper at the exact committed Hugging Face revision. Do not
stage model weights manually.

Use the checked-in credential-free release check:

```bash
python3 -B .skills/host-modal-run/scripts/release_check.py --prepare-runtime
```

The command also accepts `--project-root /absolute/clean/release`; omit it to
check the checkout containing the script. `--prepare-runtime` is forwarded only
to G2 and permits its existing ignored, pinned-runtime bootstrap. Without that
flag, the command performs no runtime bootstrap or provider call; its test lanes
may still create ordinary pytest temporary or cache files. Run it with a Python
interpreter that already has the project test dependencies, including pytest.
Those gate-runner dependencies are distinct from the hash-pinned submission
runtime and are not a reason to upgrade that runtime. The command first
requires clean Host and engine trees and an engine HEAD equal to the Host
gitlink. It then runs fresh, credential-free subprocess lanes for the focused
Host and engine tests, all skill mirrors, G2, G3 with zero mismatches, and
offline G5. It stops at the first failure, never composes live G5 `--check`, and
labels the expected offline result
`S1-S3-pass-S4-expected-refusal-not-full-G5`. Exit 0 means every composed check
passed; exit 2 means invalid input or source admission refusal; exit 1 means a
child check was unavailable, timed out, or failed. Child output and diagnostics
are not relayed.

For individual gate diagnostics, use the canonical commands documented in
`.skills/host-modal-run/SKILL.md`. A failed release check is not permission to
proceed with submission. Offline isolation
checks do not prove account access, Secret contents, or provider deployment.
Provider-facing checks require their separately authorized exact command.

Authentication uses either one complete explicit
`MODAL_TOKEN_ID`/`MODAL_TOKEN_SECRET` pair or the selected saved profile when
both explicit names are absent. A partial or invalid explicit pair must refuse
without fallback. Never print credentials, their lengths, SDK configuration,
or credential-derived diagnostics; never put secrets in argv or new files.
The remote worker obtains `HF_TOKEN` only through the committed dedicated
runtime Secret.

## Submit one committed request

The paid submission boundary is exactly these eight argument tokens:

```bash
python3 -m synaptic_host training run --provider modal --config project://training/smokes/modal-sft.json --destination provider-staging
```

Confirm that this exact committed config reference expresses the intended new
run, budget, one-step workload, zero-retry policy, model revision, and A10
profile before invoking it. In a ledger where that reference is already
consumed, do not run this example again; use the intentional-new-run procedure
below and substitute only its distinct reviewed config reference. Record the
returned run ID, effect ID, provider job reference, exact Host and engine
commits, config reference, and timestamp.

An interrupted or ambiguous submission is not permission to run the command
again. Preserve `.synaptic` state and reconcile the recorded run. Never delete,
replace, checkpoint, hand-edit, or migrate the ledger or its evidence keys to
obtain a fresh effect.

## Observe and reconnect

Read the last durable Host state without credentials or a provider call:

```bash
python3 -m synaptic_host training status --run-id run-0123456789abcdef0123456789abcdef
```

An `OK` result with `"observation":"local_ledger"` and
`"provider_refreshed":false` reports only the saved Host view. It is not a
fresh provider observation. `RUN_MISSING` means the exact run pair is absent.
If the SQLite WAL or shared-memory sidecar is present, status reports the read
as unavailable rather than missing; it never checkpoints, repairs, creates, or
migrates the ledger.

Refresh an existing run through the authenticated public outcome operation:

```bash
python3 -m synaptic_host training reconcile --run-id run-0123456789abcdef0123456789abcdef
```

Reconcile enters the pinned launcher, consumes authority bound to this verb and
run ID, validates the durable preparation and released source, and calls only
the public training outcome operation. It may durably advance lifecycle state.
It cannot plan, authorize, grant, or submit a new job. A terminal result can be
answered from durable evidence, so its output does not promise that a provider
read occurred.

For reconnect, return to the same clean released source and preserved private
state, then use status and reconcile with the recorded run ID. Do not resubmit
merely because a shell, WSL session, or client process restarted.

State is local to the checkout that created the run. A newly cloned release
does not contain an earlier checkout's ledger or evidence keys, and there is no
supported state-handoff or ledger-migration command. Do not copy, reconstruct,
or partially restore private state as an operator workaround. Keep the original
released checkout and its whole state intact; treat cross-checkout reconnect as
an explicit release-readiness gap until a reviewed handoff exists.

## Intentional new runs

Repeating a consumed request returns its existing durable effect; it is not a
new-run mechanism. An intentional new run requires a separately reviewed,
committed config at a distinct project-relative config reference, followed by
the normal source and release gates. Do not clear state, mutate a consumed
config in place, use an empty clone to bypass consumed authority, manufacture
an effect ID, or create an ad hoc launcher/helper. Extend the checked-in config
or CLI workflow if a reusable capability is missing.

## Evidence and logs

Retain the closed Host result envelopes and the exact run/effect/job bindings.
For completion, require authenticated completion, terminal, and log records;
exact cross-plane identities; terminal/log-chain agreement; exactly the five
accepted artifact roles and paths; matching relisted sizes and SHA-256 values;
artifact-set agreement; and workload, closure, and SFT artifact-contract
verification. Provider wrapper success alone is not training success.

Capture only the bounded command outputs needed for review. Keep stdout as the
machine-readable Host envelope and treat stderr as closed diagnostics. Scan
retained streams for the declared credential shapes, but describe a clean scan
only as evidence for those shapes and captured streams, not proof that every
possible secret representation is absent.

## Artifact retrieval limitation

The current Host CLI has no supported Modal artifact-download command. The
successful historical smoke used an existing Modal CLI to retrieve the exact
five already accepted paths, then matched every local size and SHA-256 value to
the authenticated manifest. That historical procedure is evidence, not a
checked-in release interface.

Do not compensate by reading provider Volumes or private control planes
directly, broad-syncing a Volume, guessing paths, accepting extra files, or
placing credentials in argv. Until a bounded checked-in retrieval command or
an independently reviewed exact Modal CLI procedure is documented, artifact
retrieval remains a release-readiness gap. Status and reconcile expose state
and verified artifact references, not artifact byte streams.

## Stop conditions

Stop without submitting or retrying when any of these is true:

- Host or engine source is dirty, unpushed, detached from the approved ref, or
  differs from the exact gitlink.
- A committed-blob, launcher/runtime, source, isolation, mirror, config, budget,
  credential, durable identity, or provider deployment gate refuses.
- Credentials are partial, the selected account/environment is uncertain, or a
  command would expose credentials or unbounded provider diagnostics.
- The ledger is malformed, redirected, active with WAL/shared-memory sidecars,
  missing unexpectedly, or inconsistent with the run and preparation.
- Submission outcome is ambiguous, authority is consumed, a provider/effect
  collision exists, or another invocation could duplicate spend.
- The requested config, model, GPU, retry, timeout, budget, environment,
  Volumes, Secret, publication, retrieval, or teardown scope differs from the
  reviewed request.
- Completion evidence, exact five-artifact inventory, local byte hashes, or
  workload/closure verification disagrees.

Do not cancel, delete, teardown, publish, rotate keys, inspect the old
environment, or launch another paid job unless that exact action is separately
authorized.
