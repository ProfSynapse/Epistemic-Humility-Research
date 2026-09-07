---
name: host-modal-run
description: Prepare and use the native Host CLI for Modal cloud training, without local Docker. Covers the locked Linux launcher, saved Modal login, source and runtime gates, direct deployment, and bounded submission. Use for the Modal prepared-path smoke; cloud operations still require exact-command approval.
allowed-tools: Read, Bash, Write, Grep, Glob
---

# Native Host submission to Modal

The local process prepares, submits and observes. The GPU training workload
runs remotely on Modal. Do not require a local Docker daemon, submit image,
container mount, or credential-forwarding container for this workflow.

The user selected this native workflow on 2026-09-07. It supersedes the local
submit-container requirement in diagnostic section 29.10. It does not change
the remote training image, runtime lock, isolation, evidence or budget rules.

## Entry point and runtime

Run from a clean approved released Host checkout with its exact engine gitlink.
Edits belong in the edit worktree, not the release. Do not export PYTHONPATH.

The existing Host entry point remains `python -m synaptic_host training run`.
It authenticates committed inputs, prepares a private hash-pinned Linux Python
runtime when needed, and re-executes there with one-use launch authority. The
operator does not create a Conda environment or run a local container.

The native launcher currently supports Linux x86_64, including WSL. Windows
Python is not a paid-submit fallback. Its bootstrap pins CPython 3.11.15 and
uv 0.12.0; the engine requirements lock pins Modal 1.5.4. The operator's Python
version is not the isolated child's version. Do not bypass runtime proof or
call the training executor directly merely because a global Modal CLI works.

The launcher gives uv and the isolated child a fixed `/usr/bin:/bin` PATH,
not the operator's PATH. Other inherited values use the existing bounded
allowlist. uv receives no Modal token pair or saved-profile selectors.

## Credentials

A complete explicit MODAL_TOKEN_ID / MODAL_TOKEN_SECRET environment pair is
used as one pair. When neither name is present, the verified isolated child
reads the selected saved Modal login. MODAL_PROFILE and MODAL_CONFIG_PATH
select that login using the SDK's existing configuration mechanism.

A partial or invalid explicit pair never falls back to another account.
The saved-profile loader requires exact Modal 1.5.4, returns only a complete
valid pair, emits no credential-derived text, writes no credential file, and
constructs no client. The existing one-use authority snapshots the pair and
the existing provider session constructs the explicit client.

Do not print credential values or lengths, put them in argv, or write new
credential files. Never print the SDK configuration object. Saved login is
local authentication, not proof that the dedicated cloud environment exists.
HF_TOKEN is still separately required for deployment; the worker receives it
through the dedicated runtime Secret, never through the paid-submit argv.

## Local gates

```bash
python3 -B .skills/host-modal-run/scripts/g2_native_host.py --prepare-runtime
python3 -B .skills/host-modal-run/scripts/g3_engine_lock_digests.py --expect 0
python3 -B .skills/host-modal-run/scripts/g5_isolation_triple.py
```

G2 is native. The explicit --prepare-runtime option permits the existing
hash-pinned dependency bootstrap to write the release's ignored private cache.
Without that option, a missing or invalid runtime refuses. It checks clean
source, the engine gitlink, the actual committed-source reader, runtime proof,
exact child Python and SDK, and engine containment. Its isolated verification
child has no credentials and disables saved-config reads.

G3 reads committed blobs, not line-ending-translated working files.

G5 without --check makes no provider call. S1 checks dedicated names; S2 the
required Secret key names; S3 parses the exact worker decorator; S4 requires
the recorded rotation attestation. Before rotation, S4 refusal is expected,
and must not be called a complete G5 pass.

After operator-approved deployment and rotation, use the locked interpreter:

```bash
.synaptic/cache/modal-launcher-v1/bin/python -B \
  .skills/host-modal-run/scripts/g5_isolation_triple.py \
  --check --rotation-recorded-at <recorded-timestamp>
```

This live check requires separate exact-command approval. Offline failures
prevent the lookup child. The native child uses a closed environment and
closed diagnostics. It hydrates only the dedicated Environment, two Volumes
and Secret under one explicit client. Environment and Volume use
create_if_missing=False; Secret uses required_keys, with no unsupported
creation parameter. No workspace listing or Secret-content read is allowed.
The old --submit-image/--docker/--endpoint options are removed, not shims.

## Operator steps

Use [the native runbook](../../docs/review/modal-smoke-native-runbook.md).
It distinguishes measured local results from unverified bootstrap/provider
behavior. Confirm each credential-bearing or account-changing command at the
moment of execution. Confirm the one paid submit separately.

The paid entry point remains exactly eight argument tokens:

```bash
python3 -m synaptic_host training run \
  --provider modal \
  --config project://training/smokes/modal-sft.json \
  --destination provider-staging
```

Do not replace this with a raw Modal function call. The Host path retains
committed-source admission, budget authorization, evidence signing, durable
effect identity and duplicate-submit protection. Stop before publication.

## Tests and historical artifacts

The gate tests live in tests/skills/host_modal_run/. Native saved-login and
launcher routing tests live in tests/synaptic_host/test_modal_native_login.py.
Use fake credentials and fake clients for regressions. Real-SDK checks bind
signatures only; they are not account evidence.

The old container recipe and G2 container instrument remain historical files,
not an alternate native workflow. Do not execute them for this cloud smoke.
Do not delete retained containers or images without separate user approval.
