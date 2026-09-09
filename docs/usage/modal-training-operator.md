# Modal training operator commands

The supported run command remains unchanged:

```bash
python -m synaptic_host training run --provider modal --config project://training/smokes/modal-sft.json --destination provider-staging
```

For an existing run, inspect the durable local ledger without credentials or a
provider call:

```bash
python -m synaptic_host training status --run-id run-0123456789abcdef0123456789abcdef
```

The result says `"observation":"local_ledger"` and
`"provider_refreshed":false`. It is evidence of the last durable Host update,
not a claim about current provider state. A missing run returns `RUN_MISSING`
without creating or migrating the ledger.

Status reads a bounded snapshot of the existing private database. It is
available only while the ledger is quiescent: a present WAL or shared-memory
sidecar is reported as an unavailable/invalid operator read, not as a missing
run. The command never checkpoints, repairs, or migrates that state.

To perform the authenticated outcome operation, including provider reads when
the run is eligible for them, and durably advance the run when the available
evidence permits it, use:

```bash
python -m synaptic_host training reconcile --run-id run-0123456789abcdef0123456789abcdef
```

Reconcile enters the same pinned isolated Modal runtime and consumes the same
kind of one-use launcher authority as submission. It restores the configured
explicit client, validates the existing run and preparation binding, and calls
the public training outcome operation. A terminal outcome may be answered from
already durable evidence without a fresh provider read, so the reconcile result
does not claim provider freshness. Reconcile does not plan, preflight,
authorize, or start a job, and it cannot create a new run identity.

Artifact download is not yet a supported Modal operator command. The public
Modal training API exposes verified artifact references but no authenticated
byte stream. The separate public Runs API has a stream contract, but the Host
does not yet have a supported Modal Runs composition. Do not bypass that gap by
reading provider volumes or private control planes directly.
