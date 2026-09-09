# Verified Modal output retrieval: candidate checks

Initial checkpoint measured 2026-09-09. This is local candidate evidence, not a
release verdict or a cloud smoke. No provider call, private run-state read,
artifact publication, or chat session was performed. At this checkpoint,
changes were uncommitted in isolated edit worktrees. The later correction below
records subsequent commits and review; do not read the initial state as current.

Host baseline: `f1bab0fa254b5d102fb806fd9bd7c50310bd72ad`.
Engine baseline: `c2ae4d03cb2d51d2582354a8d79150cf2cbb12d3`.

## Implemented candidate

`training retrieve --run-id` consumes its own launcher authority and requires
an existing successfully verified run. The Host reads its existing ledger
without initialization or migration and checks existing evidence keys without
creating storage. The engine exposes authenticated inventory and bounded,
single-use artifact streams through `RunsAPI`. The Host writes the five output
files exclusively, rechecks their bytes, and atomically publishes a receipt.

Review corrections include read-only ledger composition, final all-file
rehashing, source-directory and inode checks, failed-refresh cache eviction,
and an atomic concurrent stream claim. Files remain opaque archives; retrieval
does not establish model loading or model quality.

## Measurements

All test processes ran from `/home/profsynapse/code/ehr-release-readiness-20260909`
using CPython 3.12.9 with no inherited credentials, plugin autoload disabled,
and `MODAL_IS_REMOTE=1`. Candidate imports used explicit per-process `sys.path`,
never an exported `PYTHONPATH`. Fixtures used synthetic local state and fake
providers.

- Candidate retrieval operator, reconciliation, local sink, and engine read
  adapter: **64 passed**.
- Candidate release-check regression module: **9 passed**.
- Broader candidate Host operator, persistence, and supplemental lanes:
  **389 passed, 10 skipped, 5 failed**. One failure rejects an externally located
  candidate engine; four Docker ingress tests reject candidate source admission.
  These failures are not waived and this is not a release-check PASS.
- Clean baseline CLI and smoke-acceptance modules, including those five nodes:
  **123 passed, 2 skipped**. This comparison does not prove a clean candidate
  release will pass; it still needs its own committed-source checks.
- Scoped Host Modal skill synchronization: passed; no project context or
  managed memory file was updated.
- Independent final source review: no remaining blockers in the read-only
  retrieval path. This review does not cover live provider behavior or chat.

The candidate Host and engine sources live in the `modal-artifact-readiness`
and `modal-verified-run-reads` worktrees under
`/home/profsynapse/code/ehr-worktrees/`. The focused tests are
`test_training_operator_retrieve.py`, `test_training_operator_reconcile.py`,
`test_modal_artifact_retrieval.py`, and `test_modal_run_reads.py` in their
respective Host and engine test trees.

## Work remaining at the initial checkpoint

Commit the independently reviewed exact source paths, update the Host gitlink,
and validate a clean candidate release before any publication request.
No PR, push, or merge had been performed at that checkpoint. Historical runs retain
their original releases; this change does not migrate their ledgers or keys.

The requested easy local/Modal chat capability has a separate
[bounded-session design](../plans/bounded-model-chat.md). Serving, model-load
proof, runtime pins, and live timeout verification remain unimplemented or
unverified. No paid serving resource is authorized by this record.

## Correction: merge-preparation checkpoint, 2026-09-09

The engine change was independently audited and committed as
`f00cef358ec825c696f99890496219a8cded6cc7`. A clean engine release passed
**468 tests**, covering the complete Modal engine release lane plus the public
Runs and Training API contracts and the optional-dependency contract. Engine
[PR #159](https://github.com/ProfSynapse/Synaptic-Tuner/pull/159) merged into
`feat/submodule-cloud-api-v1` as
`68f3bea9ca210d8f507645d6048da2127852ad49`; its tree is identical to the tested
commit. Main was not changed.

The initial Host changes were committed as
`f5423a9d8716ef60b7d557540185e970643bdf46` with normal Host hooks enabled.
Pre-push review then identified a missing check of the published receipt name.
The correction reopens that name without following links, binds it to the
retained temporary inode, checks private file metadata and bounded exact bytes,
and requires the final five-file-plus-receipt inventory before returning success.
Adversarial replacement, symlink, hardlink, and extra-member tests were added.
The correction passed independent review and **25 sink tests**. The combined
retrieval, reconciliation, sink, and engine read tests then passed **68 tests**.
These checks used synthetic fixtures, not a live Modal run.

The Host candidate now pins the engine feature merge. A clean committed Host
release must still pass the checked-in release instrument before its PR may
merge. Record those final results in the associated Host PR against
`feat/submodule-cloud-api-v1-host`. This checkpoint does not waive the earlier
five source-admission failures or claim they have passed in the final candidate.
