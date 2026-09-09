# Modal SFT release readiness

Status date: 2026-09-08

## Decision summary

The narrow Linux/WSL to Modal A10 SFT path is proven on one exact release.
It is not ready to merge to either repository's `main` branch.

The successful release used:

- Host `eb2f2e0206b46eb0d932e06fbe999633f0cf023f`.
- Engine `a5460845c435c9e44847dbc1dd5d0f67d0fdff80`.
- Modal SDK 1.5.4 in the locked CPython 3.11.15 launcher.
- One-step SmolLM2-135M-Instruct SFT on Modal A10.

The Host authenticated the terminal result and verified five exact artifacts.
Local copies matched the accepted sizes and SHA-256 values. The adapter archive
contains `adapter_config.json`, `adapter_model.safetensors`, and `README.md`.
This proves the bounded smoke path. It does not prove model quality, cache-hit
reuse, local automatic model preparation, broad production readiness, or model
publication.

At the initial 2026-09-08 review snapshot, before the current feature-branch
integration work, two repository-integration blockers remained:

1. Host PR 596 is a review record, not a merge candidate. GitHub reports it as
   open, conflicting, and dirty, with no checks. Its merge-base feature diff is
   212 files with 133,079 additions and 2 deletions. Current `main` also changed
   747 files after the shared base. A direct tip-to-tip diff therefore contains
   many main-only changes and must not be interpreted as intended feature
   deletions.
2. The engine repair is on `feat/submodule-cloud-api-v1`, not engine `main`.
   Engine PR 156 merged as `9a8ad9f298a88b6a1e65982b8b8e1220480a5ad2`.
   That merge commit and tested engine `a5460845` have the same Git tree,
   `4cca0616438f6f1db65545273f2de8e6bf0e69f7`. The integration branch is 112
   commits ahead and 2 commits behind engine `main`, across 300 files. Engine
   sequencing to `main` is a release prerequisite, not a defect in the tested
   repair.

Do not merge PR 596 as it stands. First choose an integration strategy and
validate its resulting tree. This report does not choose, rebase, merge, or
publish a branch.

## Supported release scope

The proposed supported scope is deliberately small:

- Operator host: Linux x86_64 or WSL with the Linux launcher.
- Provider: Modal only, using the dedicated environment, two Volumes, and
  runtime Secret named by `training/providers/modal.json`.
- Accelerator: the pinned Modal A10 worker configuration.
- Method: one configured SFT workload through
  `python -m synaptic_host training run`.
- Operator continuity: the Host candidate accompanying this report adds bounded
  `training status` and authenticated `training reconcile` commands for an
  existing durable run. These commands are not part of the proven `eb2f2e02`
  release and become release scope only after the final Host/engine pair is
  validated.
- Model preparation: exact configured Hugging Face model and revision,
  prepared automatically inside the remote wrapper.
- Trainer boundary: offline, credential-free child with exact source and
  closure checks.
- Completion: authenticated terminal and log bindings, exact five-artifact
  inventory and byte verification, and workload/closure semantic verification.
- Retrieval: exact artifacts downloaded from the dedicated artifact Volume.

The release does not include native Windows submission, local Docker training,
local automatic model preparation, other Modal GPU classes, other training
methods, publication, model-quality claims, cloud-object teardown, or access to
the old Modal environment.

## Evidence already established

Private evidence is retained at
`/mnt/f/Code/ehr-modal-model-preparation-evidence.Hb8UXe`.

The fifth run used Host `eb2f2e02` and engine `a5460845`. Submission returned
`SUBMITTED` at 2026-09-08T15:24:07Z. Authenticated outcome reached `SUCCEEDED`
at 2026-09-08T15:28:46Z for:

- run `run-a8c39c783c752f7c255d5dc210f5ca44`;
- effect `effect-e2a82de01a17bc929131476d7151429c`;
- call `fc-01M20SX3C2PMJ77DBH6541WFK2`.

The accepted result reports trainer exit 0, execution status `completed`,
execution exit 0, and five verified artifacts. The released verifier requires:

- authenticated completion-manifest, terminal, and log records;
- exact cross-plane identity agreement;
- terminal and log-chain digest agreement;
- five unique roles, paths, and provider entry identifiers;
- exact relisted paths, sizes, and content SHA-256 values;
- artifact-set digest agreement;
- workload, closure, and SFT artifact-contract semantic verification.

The downloaded artifact copies match the accepted manifest. Both exact-run
trainer streams are retained. A scan of 20 retained logs found zero matches for
the checked HF/Modal token-prefix, private-key-header, and Bearer-token shapes.
That scan does not prove that every possible secret representation is absent.

The five-attempt history also proves several refusal and recovery properties:

- a consumed request did not create a duplicate paid job;
- failed jobs were reconciled to authenticated terminal states;
- provider upgrades preserved existing state, keys, and prior effects;
- the lazy Modal call handle was restored with an explicit client;
- source, worker-control-path, model-preparation, and bytecode-closure failures
  failed closed before the final successful run.

## Main integration scope and choices

Current Host `main` does not contain `synaptic_host`, `synaptic.yaml`, or the
Host Modal skill. Its submodule points to engine `6b01834b`. The Host feature
branch adds the Host implementation, tests, training configuration, skills,
historical design records, Docker work, and the Modal path in one 212-file
feature diff.

Only two textual merge conflicts were found by a three-way merge preview:

- `AGENTS.md`, where current-main instructions and the Host capability boundary
  must both be preserved;
- `synaptic-tuner`, where current main, the feature pin, and the engine
  integration target differ.

The low conflict count does not make the integration low risk. Most Host files
are new relative to the merge base, so Git cannot detect a missing dependency
or a policy mismatch with current main.

The lead and user can choose one of these strategies:

### Strategy A: integrate the complete Host feature

Merge current Host `main` into a dedicated integration branch based on the
feature history. Resolve the two known conflicts deliberately. This retains the
tested Host dependency graph and prior review history. It also lands the Docker
and historical-document surface, which is outside this narrow release claim.
Run the complete Host suite because the merged code surface is not narrow.

### Strategy B: build a Modal-only integration slice

Start from current Host `main` and transplant the Modal CLI, shared durable
state/security/artifact modules, configuration, skills, and tests. Pin the
chosen engine integration commit. This gives a smaller published surface, but
manual selection can omit shared dependencies that the tested feature branch
provided. Require an import-closure inventory, a file manifest, and all focused
plus shared-dependency tests on the resulting tree. Do not infer safety from the
successful feature-branch run alone.

### Strategy C: stage the complete Host feature, then narrow it

First produce a green integration tree with the complete feature. Then remove
Docker-only and historical material in a separate reviewed change. This makes
dependency removal observable, but it creates two integration steps and must
not silently remove shared Host modules used by Modal.

For all strategies, engine integration must be settled first or pinned as an
explicit prerequisite. The Host gitlink should name a durable engine commit on
the selected integration line. A tree-equivalent merge commit is acceptable
only if the source-admission and remote-ref gates accept that exact commit.

## CI and branch controls

GitHub reports one active Host workflow, `.github/workflows/validate.yml`.
It runs on pull requests and pushes to `main`. It checks:

- repository and skill-mirror invariants through `bin/validate_kg.py`;
- research-session notes;
- typed knowledge-graph frontmatter and edges.

The workflow uses `submodules: false`. It does not run Host tests, engine tests,
Modal runtime-lock checks, closure checks, launcher checks, Linux/WSL checks,
artifact verification, or artifact-load checks. PR 596 has no check runs.
GitHub reports no Actions workflows for the engine repository. Neither
repository's `main` branch has GitHub branch protection enabled.

The local Host pre-commit hook adds retired-term, experiment-layout, registry,
and graph validation. Those checks are important, but they do not replace
release CI. The successful smoke and retained local test logs are evidence for
exact commits, not an automatic gate for a future merged tree.

Before release, add or document an enforced integration check that runs at
least the following on the exact proposed Host and engine pair:

1. Host Modal provider, training, resolver, native-login, restoration,
   acceptance, security, SQLite, launcher, and cold-bootstrap tests.
2. Engine Modal provider, runtime-lock, offline-worker, model-snapshot, and SFT
   runtime tests.
3. G2 native source/runtime admission and G3 zero committed-blob mismatches.
4. Skill mirror and configuration validation.
5. A credential-shape scan over captured test logs, with the scan's limited
   claim stated explicitly.

Live G5 and a paid smoke must remain operator-controlled checks. Do not place
provider credentials in general pull-request CI.

## Failure classification

### Must fix or adjudicate before integration

Candidate update, 2026-09-08: the three-file engine test repair was independently
audited, then copied byte-for-byte onto engine `9a8ad9f` in an ordinary local
clone. The pinned Modal launcher lock in that clone was rematerialized from the
unchanged commit with LF bytes; its working SHA-256 and committed-blob SHA-256
both measured
`8273b49a3b613bed82905ac349d2028935269c4d369dd5781a5eb0bad23b874e`.
From the clean released Host working directory, Python 3.12.9 with `-B` and
`MODAL_IS_REMOTE=1` collected and passed all 365 tests in the recorded 18-file
Modal/runtime set. This independently resolves the earlier two construction
failures and nine reproduced SFT fixture/import failures for that candidate.
That audit baseline was engine `9a8ad9f` plus the three test files. The same
audited test content is now committed as
`de66b5869cf02c5fd6fc08706d51fb619e6dcd54` and pushed on
`fix/modal-test-reliability`. PR 157 merged that reviewed head into
`feat/submodule-cloud-api-v1` at 2026-09-08T21:06:06Z as
`519a567d1562680c57137ca166459ab6efaa17a2`. This did not merge the work to
engine `main`. The passing candidate is evidence for the reviewed content, not
a green release gate or production proof. The final Host pin and
feature-integration pair must repeat the applicable checks.

Integration verification, 2026-09-08: engine merge `519a567d` and reviewed head
`de66b586` both resolve to tree `142e693892fc848dc55fb2ed397c2821f78f166d`.
The five-module Host suite was rerun with that pin and passed all 109 tests.
Clean committed-pair source/runtime gates remain separate from that result.

Readiness follow-up, 2026-09-08: PR 158 merged the explicit Modal launcher-lock
LF attribute and checkout regression into the same engine feature branch at
2026-09-08T21:20:58Z. Merge `c2ae4d03cb2d51d2582354a8d79150cf2cbb12d3`
and reviewed head `3ea52d23de2b52b2d4fa86ecc4b8b2bc0cc5554d` both resolve
to tree `1ed44207772fba5d0cb976bd055694ae5997839c`. An independent ordinary
clone made by native Windows Git with `core.autocrlf=true` and no `core.eol`
override preserved the lock's exact SHA-256 above while converting an ordinary
text control to CRLF. All 366 tests in the same 18-module suite passed against
that committed source. No dependency or runtime bytes changed. The accompanying
Host candidate now pins `c2ae4d03`; all 109 Host tests passed again with this pin.

The Host operator candidate accompanying this report adds local-ledger status
and authenticated public-outcome reconciliation. Its 109-test Host suite passed
and an independent source review passed after adversarial ledger fixes. It is
not part of the proven `eb2f2e02` release. It does not add artifact download,
publication, or a new paid-job operation.

Host commit precondition, 2026-09-08: the required pre-commit hook refused the
candidate because historical research inputs under `archive/`, `scratch/`, and
`synaptic-tuner/toolset-training-artifacts/` are absent. Representative required
paths are also absent from the canonical checkout, so the documented worktree
reference setup cannot currently satisfy this check. The other hook checks
passed: repository invariants, terminology, research sessions, experiment
registry, and graph validation (zero errors). The user explicitly approved a
one-commit hook bypass after reviewing this unrelated missing-input failure.
The integration commit uses that exception; no hook or validator configuration
is changed, and the other recorded checks remain applicable. This exception is
not a passing experiment-validation result or a Modal test failure.

- Resolve the Host `AGENTS.md` and submodule conflicts without discarding either
  current-main policy or the Host security boundary.
- Confirm the final Host integration file set. PR 596 includes Docker code and
  long historical documents outside this narrow release claim.

### Supported-scope must fix

- Provide one authoritative release operator guide. The current native runbook
  is a chronological incident record with superseded commands. A release guide
  must identify prerequisites, the supported command, state preservation,
  reconnect behavior, artifact retrieval, and explicit stop conditions without
  requiring readers to resolve historical supersession layers.
- Define artifact retrieval as a supported interface. The successful run used
  the existing Modal CLI to download artifacts. The current Host candidate adds
  `training status` and `training reconcile`, but no artifact-download command.
  Either document the exact bounded Modal CLI retrieval procedure as the
  supported interface or add a separately reviewed Host command.
- Define a fresh-request procedure. Durable identity includes the config
  reference, so reusing a consumed reference returns the existing effect. The
  release guide must distinguish reconnect/replay from an intentional new run.
- Validate the final current-main integration tree from a clean checkout. The
  successful smoke ran the feature tree, not the eventual merge result.
- Preserve the explicit LF attribute introduced by engine PR 158. Native
  Windows first-checkout byte identity and the 366-test suite now pass; repeat
  the source/runtime gates on the final committed Host/engine pair.
- Pin and verify the final engine integration commit and remote branch before
  Host integration.

### Deferred outside the narrow release

- Native Windows submission.
- Local Docker and local automatic model preparation.
- GPU classes other than the pinned A10 profile.
- Methods other than the configured SFT path.
- Model publication and public model cards.
- Model-quality evaluation.
- Automatic teardown or old-environment migration.
- Cache-index services and generalized cache management.

Historical Docker and diagnostic documents may remain for provenance. They are
not release instructions. Mark their status clearly or move them to a separate
historical-doc cleanup after integration. Do not rewrite the evidence trail as
part of the release cut.

## Acceptance matrix

| Capability | Measurable acceptance | Current evidence | State |
|---|---|---|---|
| Fresh checkout | Checkout the proposed Host integration commit and exact engine gitlink. Both trees are clean. G2, G3, offline G5, and focused tests pass without `PYTHONPATH`. | Proven for Host `eb2f2e02` and engine `a5460845`; not proven on a current-main integration tree. | Unmet for release |
| Authentication | With a complete explicit Modal token pair or selected saved profile, the isolated client binds the dedicated environment. Partial explicit credentials refuse without fallback. No credential value enters argv or logs. | Fake-client tests, saved-profile tests, live G5, and five live submissions support this. | Proven on tested release |
| Submission | One exact eight-token Host command produces one durable effect and one provider call within the committed USD 1.00, one-step, zero-retry policy. | Fifth run submitted once and succeeded. Earlier runs exercised closed failures. | Proven on tested release |
| Reconnect | A new Host process with preserved state restores the exact call, observes outcome, and verifies completion without another submission. | Repeated process invocations and the explicit-client hydration repair recovered durable calls and the fifth terminal result. The operator candidate accompanying this report adds bounded status/reconcile surfaces and passed 109 Host tests plus independent source review. | Proven manually on tested release; candidate CLI not part of `eb2f2e02` |
| Intentional rerun | Repeating the same consumed request returns its original durable effect and creates no call. A distinct reviewed config reference creates a distinct effect only after explicit intent. | Duplicate prevention was proven for a consumed failed request. Exact replay after a successful request was not retained as a separate acceptance result. | Partly proven |
| Model preparation | Missing exact-revision files download in private scratch. Verified persistent files may be reused. The offline child receives a link-free snapshot and no secrets. | Automatic preparation is proven by the successful fifth run. A cache hit is expressly not proven. | Fresh preparation proven; cache hit unmet |
| Failure recovery | Inject a closed pre-submit failure, an ambiguous post-submit interruption, and a terminal worker failure. Preserve the ledger. Reconcile before retry. Never duplicate a call. | Multiple terminal failures and state-preserving upgrades are proven. The first submission's reconciliation path and later distinct effects provide partial interruption evidence. | Partly proven; run deterministic integration acceptance |
| Artifact download | Retrieve exactly five accepted paths. Local sizes and SHA-256 values match the authenticated manifest. No extra artifact is accepted. | Proven. All five local copies match. | Proven on tested release |
| Artifact load | Open the final-model archive, verify the three-member inventory, and load the adapter plus tokenizer against the exact base revision in a credential-free CPU smoke. Confirm one bounded inference or strict deserialization result. | Archive inventory was checked. No model or tokenizer load acceptance is recorded. | Unmet |
| Log hygiene | Scan all captured local and remote streams for the declared credential shapes. Retain only bounded evidence. | Twenty local logs and both trainer streams had zero matches for the declared shapes. | Proven for tested evidence; repeat after integration |

## Release gate

The narrow release can proceed only when all of these conditions hold:

1. The engine integration strategy is approved and its exact feature-integration
   commit passes the repaired test suite. The independently validated
   `9a8ad9f` plus three-test audit baseline was committed as `de66b586`; PR 157
   merged it into the intended engine feature branch as `519a567d`. The PR 158
   follow-up is merged as `c2ae4d03`, is tree-identical to its reviewed head,
   and passed the expanded 366-test suite. The Host candidate pins this commit.
2. The Host integration strategy is approved. The resulting current-main-based
   tree has an explicit file scope and resolved `AGENTS.md` and gitlink choices.
3. The final Host/engine pair passes the clean-checkout, focused Host, focused
   engine, G2, G3, offline G5, and mirror/config checks.
4. The release has one authoritative operator guide and a bounded artifact
   retrieval procedure.
5. Successful-request replay and credential-free CPU artifact load are either
   tested or explicitly removed from the release promise.
6. Review records the independently passing 366-test engine disposition and the
   independently reviewed 109-test Host operator disposition, then repeats the
   relevant checks on their committed feature-integration commits.

A second paid smoke is not required merely to merge identical logic. Require a
new live smoke only if integration changes executable behavior, source binding,
runtime locks, credentials, durable identity, provider deployment, or artifact
verification. Any such smoke requires its own approved request and cost bound.
