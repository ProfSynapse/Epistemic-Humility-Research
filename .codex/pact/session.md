# PACT Session

Active orchestration ledger for the current repo-focused PACT session.

## Startup Context

- User intent: review handoff context, orient the orchestrator, and start local GPU probing of the Phase 1 experiment pipeline after secretary startup.
- Docker is reported up by the user. The secretary did not verify Docker, GPU, or experiment state.
- Main near-term objective for downstream phases: local GPU probing to make sure the merged Phase 1 pipeline works, solving encountered issues where possible and updating relevant skills, gotchas, or scripts to smooth future runs.

## Current Constraints

- Secretary role is recorder/synthesizer only.
- No experiments, Docker/GPU commands, broad code inspection, or subagent coordination were performed during startup synthesis.
- Existing `.codex/pact` state was absent at startup, so this first repo-focused state version was initialized.

## Pending Verification

- Review `HANDOFF.md` or equivalent handoff artifact if the orchestrator includes it in the next phase scope.
- Verify local runner prerequisites before launching any actual GPU work.
- Use explicit pytest file paths or non-`rtk` invocation when checking tests because of the known directory-glob false negative.

## Accepted Handoff Harvest

### 2026-06-19 - Phase 3 Full SelfAware Delta Logit Diagnostic

- Source of truth: `docs/sessions/0007 - phase-3-selfaware-stratified-row-manifest.md`, checkpoints `011-validation`, `012-analysis`, and `013-result`.
- Full SFT->KTO SelfAware extraction finalized locally for seed1 with Docker: manifest `status=ok`, `verified=true`, 1233 rows, 3699 safetensors, row provenance mismatches 0, sampled delta tensors nonzero.
- Full KTO hidden-state analysis materialized with 222 ok directions. Top KTO diagnostic candidate is delta layer 25; paired DPO comparison candidate remains delta layer 24.
- Local Docker logit diagnostics completed for SFT->DPO delta L24 and SFT->KTO delta L25. Both runs were `status=ok`, `generation_executed=false`, `logit_diagnostic_executed=true`, with 18 arms x 16 rows per candidate.
- Interpretation: KTO L25 has the cleaner sign pattern on refusal-opener probability deltas, but source-layer-specific claims are not warranted from this panel because wrong-layer and random controls also move, including comparable top-1 changes in some high-coefficient settings.
- Validation facts recorded from the accepted handoff: research session validate passed, causal pilot tests passed with 63 tests, and diff check passed.
- Decision: treat these outputs as Tier 2 exploratory local logit diagnostics only, not generation evidence and not pre-registered headline evidence.

### 2026-06-19 - Phase 3 Nearby-Layer SelfAware Logit Diagnostic

- Source of truth: `docs/sessions/0007 - phase-3-selfaware-stratified-row-manifest.md`, checkpoint `014-result`.
- Nearby-layer Docker logit diagnostics completed for full SelfAware top delta candidates across offsets `-2`, `-1`, `+1`, and `+2`.
- All 8 candidate/offset runs were `status=ok`, with `generation_executed=false` and `logit_diagnostic_executed=true`.
- Grid details: coefficients `2`, `5`, `10`, and `20`; 16 rows per candidate.
- Interpretation: the smaller grid preserved sign behavior for source activation arms, especially KTO L25, but nearby wrong-layer arms often matched or exceeded source-layer refusal-opener probability deltas. This panel does not support a source-layer-local claim.
- Validation facts recorded from the accepted handoff: research session validation passed, causal pilot tests passed with 63 tests, and scoped diff check passed with only a CRLF warning.
- Decision: preserve these outputs as Tier 2 exploratory local logit diagnostics only, not generation evidence and not pre-registered headline evidence.

## Next Dispatch Context

- Dispatch should likely use the `experiment-runner` skill for local lane gating/dry-run/probing.
- Bound the first technical pass to prerequisite checks, dry-run/materialization checks, and smallest local GPU smoke probe needed to expose integration failures.
- If failures reveal durable process gotchas or runner gaps, update the relevant checked-in scripts or skill notes, not the `synaptic-tuner` submodule.

## Specialists

- Active: `pact_secretary` startup synthesis.
- Reusable: none recorded.
- Closed: none recorded.

## Blockers

- None from secretary startup. Actual runtime blockers are unknown until the orchestrator authorizes technical probing.

## 2026-08-28 Submodule-First Cloud Execution Resume

- Engine branch `feat/submodule-cloud-api-v1` is accepted and pushed at `1aa60de5333e86977d5edcab2f12db81d0c7ce79`; the host gitlink points to that exact commit.
- Host branch `feat/submodule-cloud-api-v1-host` was previously accepted and pushed through `02be1641`, including retained-root bundle durability, authenticated Docker source staging and mount resolution, complete same-key bundle serialization, and bounded Docker Desktop transport.
- Docker Desktop and the canonical Ubuntu WSL checkout were revalidated after the workstation restart: Docker Engine `29.3.1 linux`; WSL checkout `02be1641`.
- Docker control Slice 5.1 is accepted but not yet committed: typed `ps`/image-inspect/container-inspect results, strict bounded JSON parsing, exact `ai.synapticlabs.tuner.v1.*` labels, recursively authenticated projections, frozen-command/evidence/request/result binding, per-entry environment hashes, conservative state normalization, and no raw daemon output crossing `cli.py`.
- Independent PACT correctness verdict: ACCEPT. Independent PACT test verdict: PASS with 159 focused tests and 345 full `docker_v1` tests; compilation and diff/static checks are clean.
- Next implementation slice: host-owned authenticated Docker control contracts (5.2), followed by read-only image/lookup (5.3), at-most-once create/start (5.4/5.5), composition and the first actual coordinator-driven CPU smoke (5.6).
- Durable main-project persistence remains intentionally deferred until after the same-process smoke. No SQLite implementation belongs in the submodule.
- Known qualifications: mount verification narrows but does not eliminate WSL/Docker Desktop TOCTOU (B4.2c remains); same-process in-memory mutation authority does not prove restart recovery (B4.4 remains); Docker runtime timeout enforcement needs a later watchdog/cancel slice.

### 2026-08-28 Docker Control Slice 5.2 Accepted

- Host-owned Docker control contracts are accepted: authenticated create-path and workload-environment bindings, redacted ephemeral private environment transport, exact create specifications and CREATE/START intents, mutation ADMITTED/ATTEMPTED/VERIFIED records, request-bound admission/CAS/lookup results, and pinned authority boundaries.
- CAS embeds exact authenticated expected and replacement records and permits only ADMITTED→ATTEMPTED and ATTEMPTED→VERIFIED with exact predecessor, operation/effect, intent, and signer continuity.
- Independent PACT verdicts: correctness ACCEPT; test PASS. Final evidence: 32 focused tests, 376 full `docker_v1` tests, compilation/diff/static checks clean.
- No Docker mutation, SQLite, concrete repository, or engine/submodule change was introduced in this slice. Next: Slice 5.3 read-only image presence and container lookup.

### 2026-08-28 Docker Read-Only Control Slice 5.3 Accepted

- Added authenticated expected-create catalog bindings, canonical owned-label projections, exact image presence checks, and total read-only container lookup.
- Lookup binds every typed result to the exact image/name/container/repository operation; false absence requires exact zero-name inventory plus host mutation-record ABSENT and exact pinned absence issuance from an untouched content baseline.
- Single-container FOUND requires authenticated mutation ownership, exact catalog/intent/environment evidence, and complete identity/labels/runtime/arguments/environment-subset/mount/state comparison. Repository admission/CAS are never called.
- Independent PACT verdicts: correctness ACCEPT; test PASS. Final evidence: 74 focused tests, 418 full `docker_v1` tests, compilation/diff/static checks clean.
- Next mutation slice must add expected-catalog `publish_once` with exact-match convergence before admission, then implement at-most-once CREATE.

### 2026-08-28 Docker CREATE Boundary Slice 5.4a Accepted

- Added a sanitized typed CREATE result and strict bounded container-ID stdout parser; public results bind only target/command/evidence/projection digests and expose no argv, raw output, environment values, or paths.
- Added a redacted one-use private CREATE invocation and deterministic command factory with exact pinned image, submit labels, resource limits, distinct `/source` and `/artifacts` mounts, sorted environment, and workload ordering.
- The direct CLI boundary independently validates the complete engine-compatible grammar, semantic labels, workload count/byte bounds, mount identity, canonical numbers, and canonical UNC rules before spawn.
- Independent PACT verdicts: correctness ACCEPT; test PASS. Final evidence: 247 focused tests, 475 full `docker_v1` tests, compilation/diff/static checks clean.
- This slice does not yet orchestrate or execute a real CREATE. Next: 5.4b exact-match catalog publication and same-process atomic mutation store.

### 2026-08-28 Docker Atomic Store Slice 5.4b Accepted

- Added exact-match authenticated expected-create publication plus a writer-segregated publisher port.
- Added `InMemoryDockerControlStoreV1` implementing catalog resolve/publish and mutation admit/CAS/lookup under one instance-owned `RLock`, with recursive ingress/storage/egress snapshots and no retained aliases.
- Concurrent identical/conflicting calls converge to exactly one publication, admission, or applied CAS winner; invalid contracts fail closed rather than masquerading as uncertainty.
- Independent PACT verdicts: correctness ACCEPT; test PASS. Final evidence: 55 focused tests, 481 full `docker_v1` tests, compilation/diff/static checks clean.
- Scope claim remains same-process and shared-store-instance only. No persistence, restart, or cross-process durability is claimed. Next: 5.4c CREATE orchestration and recovery.

### 2026-08-28 Docker CREATE Orchestration Slice 5.4c R1 Accepted

- The upstream host checkpoint before this slice is committed through `c0ad44c2`. Slice 5.4c is accepted but remains uncommitted pending the orchestrator's scoped commit.
- Worker-reported Slice 5.4c files are modified `synaptic_host/docker_v1/control.py` and `synaptic_host/docker_v1/control_contract.py`, plus new `synaptic_host/docker_v1/create.py`, `synaptic_host/docker_v1/verification.py`, and `tests/synaptic_host/docker_v1/test_create.py`.
- CREATE orchestration preserves untouched local request baselines, passes distinct reconstructed snapshots to dependencies, and requires exact request/result equality at catalog publication, mutation admission, attempt CAS, and final CAS before consuming any disposition.
- Only an exact locally requested ADMITTED-to-ATTEMPTED `APPLIED` acknowledgement may authorize the one-shot CREATE call. Only an exact locally requested ATTEMPTED-to-VERIFIED `APPLIED` acknowledgement may return `CREATED`.
- Shared verification catches only known validation failures as ordinary mismatches. Unexpected verifier `RuntimeError` propagates to orchestration and totals to `INDETERMINATE` rather than being misclassified as collision.
- The original correctness rejection for cross-request dependency substitution and over-broad verifier exception handling is closed. Fresh independent verdicts are correctness **ACCEPT** and test **PASS**.
- Final evidence: **50 create tests passed**, **141 focused tests passed**, and **531 full `docker_v1` tests passed**. A direct concurrency gate reconstructed **32 hosts** over one shared in-memory store, produced exactly **one CREATE**, returned `CREATED` from all 32 callers, and finished at `VERIFIED`.
- Guarantees remain same-process and in-memory/shared-store-instance only. This slice made no real Docker call and does not implement START, persistence, restart durability, or cross-process durability.
- Next dispatch: **Slice 5.5 START**.

### 2026-08-28 Docker CREATE Orchestration Slice 5.4c Release Checkpoint

- Accepted Slice 5.4c was committed, pushed to `origin/feat/submodule-cloud-api-v1-host`, and synchronized to the canonical WSL checkout at `73058c671f456ae3fe5460e4b54f740482fc8d39`.
- Windows HEAD, the origin branch HEAD, and canonical WSL HEAD matched that exact commit.
- The WSL checkout retained two unrelated pre-existing manifest type changes; this workflow did not modify them.
- Next dispatch: **Slice 5.5 START**.

### 2026-08-28 Docker START Slice 5.5 Architecture Accepted

- Accepted bases are engine `1aa60de5` and host `73058c67`; no architecture blocker is recorded. Slice 5.4d is skipped and implementation proceeds directly to Slice 5.5.
- The sequential slices are **5.5a engine typed START protocol**, **5.5b host typed START effect boundary**, and **5.5c host START transaction**.
- START requires exact accepted CREATE provenance and owns an independent `ADMITTED` to `ATTEMPTED` to `VERIFIED` mutation record.
- Only the exact attempt-CAS winner may invoke START. Typed inspection with `started=True` is the required proof; `CREATED` never proves START, and an `ATTEMPTED` START record with a merely `CREATED` container never retries START.
- Every dependency boundary requires exact local request/result adjacency before consuming a disposition.
- Guarantees remain same-process and in-memory only. SQLite and persistence remain host-owned and no database implementation belongs in the engine.
- After Slice 5.5 acceptance, proceed to **Slice 5.6 thin composition and an actual coordinator-driven CPU smoke**.

### 2026-08-28 Docker START Slice 5.5a Engine Protocol Accepted

- Worker-reported engine files are `tuner/execution/providers/docker_provider_v1/model.py`, `tuner/execution/providers/docker_provider_v1/ports.py`, `tuner/execution/providers/docker_provider_v1/effects.py`, `tests/execution/providers/docker_provider_v1/conftest.py`, `tests/execution/providers/docker_provider_v1/test_model.py`, and `tests/execution/providers/docker_provider_v1/test_effects.py`.
- The engine now uses typed START dispositions and a typed START result; boolean START semantics were removed. START evidence binds the exact owned labels and typed references.
- R1 closes alias substitution by preserving an untouched canonical baseline, passing distinct deeply rebuilt CREATE and START copies, and reconstructing nested values rather than retaining caller-controlled aliases.
- Independent verdicts are audit **ACCEPT** and test **PASS**. Final evidence: **227 focused**, **448 provider**, **28 adversarial**, and **1,155 execution tests passed with 3 skips**; compile and diff checks passed.
- The accepted candidate is based on engine `1aa60de5` and is not yet committed or pushed.
- Next dispatch: **Slice 5.5b host typed START effect boundary**.

### 2026-08-28 Separate Non-Blocking Modal Contract Finding

- One pre-existing unrelated Modal contract check reports `requirements/modal-launcher-v1.lock` with expected `dependency_lock` digest beginning `8273...` and actual digest beginning `c99a...`.
- All other six contract members match, and the relevant files are clean against engine HEAD.
- This finding is tracked separately, does not block Slice 5.5a, and was not remediated in this slice.

### 2026-08-28 Docker START Slice 5.5a Engine Release Checkpoint

- Accepted engine Slice 5.5a was committed as `dc6b5197` and pushed by fast-forwarding remote `feat/submodule-cloud-api-v1` from `1aa60de5`.
- The submodule checkout was intentionally detached when the commit was created, and remote ancestry was verified before push.
- The host gitlink now reflects the engine change; committing that gitlink update remains pending the next host commit.
- Next dispatch: **Slice 5.5b host typed START effect boundary**.

### 2026-08-28 Docker START Slice 5.5a Final Release Checkpoint

- The host gitlink and ledger were committed and pushed at `9ca421d10df6fd4ae76b37e73772e2fb22b70f0a`, with the engine at `dc6b51973fe44263a2611d9e859a920307dcb1bc`.
- Windows, origin, and canonical WSL host and submodule revisions all matched those exact commits.
- The unrelated pre-existing WSL manifest type changes remained preserved and untouched.
- Next dispatch: **Slice 5.5b host typed START effect boundary**.

### 2026-08-28 Docker START Slice 5.5b Host Effect Boundary R2 Accepted

- Worker-reported files are `synaptic_host/docker_v1/control_model.py`, `synaptic_host/docker_v1/ports.py`, `synaptic_host/docker_v1/cli.py`, `synaptic_host/docker_v1/control_private.py`, `tests/synaptic_host/docker_v1/test_cli.py`, and `tests/synaptic_host/docker_v1/test_control_contract.py`.
- The host boundary adds a typed START execution kind, typed result, and exact request digest. The CLI independently accepts exactly one lowercase 64-hex container identifier, executes with bounded `shell=False` transport, and returns only sanitized evidence.
- The private START invocation is one-use and is consumed before the external call.
- R1 establishes deep ownership of START command/evidence values and normalizes hostile CREATE/START dependency contract errors without leaking arguments, `repr`, tracebacks, causes, or contexts.
- R2 extends deep ownership to CREATE evidence and projections. Both original rejection rounds are closed.
- Independent verdicts are auditor **ACCEPT** and test **PASS**. Final evidence: **274 focused**, **558 full**, and **21 causal tests passed**; compile, diff, and static checks passed.
- This slice made no real Docker call and does not add `start.py`, orchestration, or persistence. The accepted candidate remains uncommitted pending release.
- Next dispatch: **Slice 5.5c host START transaction**.

### 2026-08-28 Docker START Slice 5.5b Release Checkpoint

- Accepted Slice 5.5b was committed, pushed, and synchronized at `aaad0679b6396c233ef7fd258f6fcca626a11f5e`.
- Windows HEAD, the origin branch HEAD, and canonical WSL host HEAD matched that exact commit; the engine remains at `dc6b5197`.
- The unrelated pre-existing WSL manifest type changes remained preserved and untouched.
- Next dispatch: **Slice 5.5c host START transaction**.

### 2026-08-28 Docker START Slice 5.5c Host Transaction R2 Accepted

- Worker-reported files are modified `synaptic_host/docker_v1/control_contract.py`, `synaptic_host/docker_v1/create.py`, and `synaptic_host/docker_v1/control.py`; new `synaptic_host/docker_v1/start.py` and `tests/synaptic_host/docker_v1/test_start.py`; and updated `tests/synaptic_host/docker_v1/test_create.py` and `tests/synaptic_host/docker_v1/test_control.py`.
- `DockerStartVerification` carries a nullable execution digest. START requires exact verified CREATE provenance plus exact pre- and post-START inspection.
- START owns an independent `ADMITTED` to `ATTEMPTED` to `VERIFIED` mutation record. Only the exact attempt-CAS `APPLIED` result authorizes the START effect, and typed inspection with `started=True` is the sole success proof.
- An `ATTEMPTED` START record with a merely `CREATED` container never retries START. A lost final CAS converges only through exact lookup.
- The direct concurrency gate reconstructed **32 hosts** over one shared in-memory store, produced exactly **one START**, returned `STARTED` from all callers, finished at `VERIFIED`, and produced zero retry effects.
- R1 binds constructor authority object identity plus exact reference/key before and after dependency calls across START, CREATE, read, and absence paths. R2 adds non-vacuous CREATE mid-call mutation coverage.
- Independent verdicts are auditor **ACCEPT** and test **PASS**. Final evidence: **63 create**, **148 focused**, **614 full**, **16 repaired-matrix**, and **22 replay tests passed**; compile, diff, and static checks passed.
- This slice made no real Docker call and does not add persistence or composition. The accepted candidate remains uncommitted pending release.
- Next dispatch: **Slice 5.6 thin composition and an actual coordinator-driven CPU smoke**.

### 2026-08-28 Docker START Slice 5.5c Final Release Checkpoint

- Accepted Slice 5.5c was committed, pushed, and synchronized at `94b10d63415256a1dda467bade6d582f893f7252`.
- Windows HEAD, the origin branch HEAD, and canonical WSL host HEAD matched that exact commit; the engine remains at `dc6b5197`.
- The unrelated pre-existing WSL manifest type changes remained preserved and untouched.
- The typed CREATE and START stack is complete.
- Next dispatch: **Slice 5.6 thin facade/composition and an actual coordinator-driven CPU Docker smoke**.

### 2026-08-28 Docker Composition And CPU Smoke Slice 5.6 Architecture Accepted

- Slice 5.6 is sequential: **5.6a engine same-process Docker composition and public API**; **5.6b host concrete HMAC authorities, registries, path/environment adapters, WSL interoperability, and thin control facade**; then **5.6c provider-dispatched `python -m synaptic_host training smoke --config ...` plus a real CPU Docker execution**.
- Current blocker evidence is explicit: source sealing requires POSIX/WSL semantics, Docker Desktop control requires the Windows Docker `.exe`, production composition/adapters are missing, and no complete `DockerReadPort` implementation exists.
- A facade-only smoke at the current boundary would require test doubles or ad hoc wiring and would not prove the intended production architecture.
- The accepted design introduces an explicit WSL interoperability seam. Source and artifact roots remain config-first and may be arbitrary configured WSL locations.
- Exact artifact verification remains host-side. External diagnostics must be bounded, and cleanup must target only the exact disposable resources created by the smoke.
- This slice makes no product read-operation or persistence claim.
- Next dispatch: **Slice 5.6a engine same-process Docker composition and public API**.

### 2026-08-28 Docker Composition Slice 5.6a Engine R1 Accepted

- The engine same-process Docker composition and public API are accepted with deliberate same-process semantics only; no persistence, restart, or cross-process durability is claimed.
- Original rejection 1: public `DockerSameProcessLaunchV1` accepted a mutually self-consistent context, plan, and preflight whose `plan.basis` workload, runtime, or artifact-policy digest could disagree with the unchanged bound profile. R1 requires exact public-construction adjacency for all three digests, and independent hostile graphs for each now reject before composition or effects.
- Original rejection 2: public `DockerSameProcessRuntimeV1.start()` and `.reconcile()` annotated their results as `object` although consumers use `WorkflowRecordV1`. R1 changes both public and concrete annotations to exact `WorkflowRecordV1`; independent tests verify the annotations and actual returned values.
- Frozen accepted hashes are `docker.py` `12B6B07586E7CE3C00B125BE223EA4DC1C6AEF8F316FFB4666C3D093EF4C9AFB`, `composition.py` `5FB138D71BC158DD516F37AFE5E925257357FEC8B14E66F9000802FE59C77484`, and `test_composition.py` `8CBE7E414FFA3A978223C92AF43CF7181A18EFF8F7CAB266AB0B483E444F2AB4`.
- Independent verdicts are auditor **ACCEPT** and tester **PASS**. Final evidence: **29 focused**, **477 provider**, **1,184 execution tests passed with 3 expected skips**, **144 contract tests excluding the known Modal lock issue**, and **12 read-only/native tests**; exact hostile and concurrency proofs passed.
- The unrelated pre-existing Modal runtime-lock mismatch remains excluded from this acceptance and tracked separately.
- Next dispatch: release the exact accepted engine commit, update and synchronize the host gitlink and canonical WSL checkout, then begin **Slice 5.6b host adapters**.
