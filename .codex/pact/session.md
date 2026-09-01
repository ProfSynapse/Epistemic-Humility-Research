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

### 2026-08-28 Docker Composition Slice 5.6a Release And Integration Checkpoint

- The engine was committed and pushed as `a1d28a9fa5b68400843386ad95dd885599a47d8e` on `origin/feat/submodule-cloud-api-v1`, containing the exact accepted `docker.py`, `composition.py`, and `test_composition.py` candidate files.
- The host was committed and pushed as `c3b82ce1d3ed532db7d1b462dcfc45153992d206` on `origin/feat/submodule-cloud-api-v1-host`, containing only `.codex/pact/session.md` and the `synaptic-tuner` gitlink update.
- Windows, remote, and canonical WSL revisions matched exactly for both the host and engine. The canonical WSL host was fast-forwarded and its submodule checked out at the exact engine commit; the Windows host and engine repositories were clean after release.
- The canonical WSL host retained exactly two unrelated pre-existing type-change entries: `gemma4-e4b/eval_pool_manifest.json` and `gemma4-e4b/split_manifest.json`. Supplemental WSL diff-detail calls returned `E_ACCESSDENIED`, but status before and after showed the same two entries, so this is a preserved caveat rather than a release blocker.
- Slice 5.6a is released and integration-ready. Next dispatch: **Slice 5.6b host adapters**.

### 2026-08-28 Docker Host Adapter Slice 5.6b R1 Architecture Accepted

- Implementation order is fixed: **b.1 HMAC kernel, exact typed views, mapping-pair models, and mapping authority**; **b.2 capability stores, source/stage/mapping pairs, and acquisition ledger**; **b.3 pair-consuming path binder and explicit environment resolver**; **b.4 argv0-only WSL interoperability for Windows `docker.exe`**; then **b.5 closeable leased host facade/composition**.
- Reuse the engine binding store and existing host control store, source, mount, CLI, CREATE, START, and control implementations. Eliminate a host command catalog, duplicate control store, mutable source registry, and read/persistence scope.
- R1 repairs the mapping boundary with an outer-authenticated storage-to-WSL pair that binds the nested proofs, root, distro, purpose, and live verification identity and feeds the path binder directly.
- The host handle owns linear capabilities. Builder ownership transfers atomically, operations hold reentrant leases, every lease path unwinds in `finally`, and cleanup runs in reverse order exactly once to a terminal sanitized result. Host lifecycle cleanup never performs Docker cleanup.
- Residual risks are explicit: every projection must reauthenticate and reconstruct both outer and nested mapping-pair envelopes rather than trusting registry-time validation; capability-ledger aliasing must key the exact capability object plus `LocalFilesystemV1` instance identity rather than stable references or digests alone.
- Real Windows `docker.exe` from WSL, Docker Desktop context behavior, UNC mounts, and GPU behavior remain unproven until Slice 5.6c. All 5.6b stores and the host handle remain same-process with no restart persistence.
- Slice 5.6c remains the actual CPU smoke boundary. Product read operations and durable persistence remain later host work.
- Independent architecture auditor verdict: **ACCEPT**.
- Next dispatch is restricted to **Slice 5.6b.1 HMAC kernel, exact typed views, mapping-pair models, and mapping authority**.

### 2026-08-28 Docker Host Adapter Slice 5.6b.1 Trust Kernel R4 Accepted

- Accepted public contracts are `DockerStoragePathMappingPairV1`, `AuthenticatedDockerStoragePathMappingPairV1`, `DockerStoragePathMappingPairAuthorityPortV1`, the narrow typed HMAC authority classes, `DockerCommandBindingEnvelopeAuthorityViewV1`, and `DockerEvidenceAuthorityViewV1`.
- Domain separation is pinned to `synaptic-host-docker-source-declaration-authority/v1`, `synaptic-host-docker-stage-bundle-record-authority/v1`, `synaptic-host-docker-command-binding-authority/v1`, `synaptic-host-docker-storage-mapping-authority/v1`, `synaptic-host-docker-bundle-binding-authority/v1`, `synaptic-host-docker-source-seal-authority/v1`, `synaptic-host-docker-wsl-root-mapping-authority/v1`, `synaptic-host-docker-create-path-binding-authority/v1`, `synaptic-host-docker-workload-environment-binding-authority/v1`, `synaptic-host-docker-control-intent-authority/v1`, `synaptic-host-docker-mutation-record-authority/v1`, `synaptic-host-docker-absence-authority/v1`, `synaptic-host-docker-expected-create-binding-authority/v1`, and `synaptic-host-docker-storage-path-mapping-pair-authority/v1`.
- Mapping-pair structural validity remains distinct from authenticated authority. Trust-sensitive paths are closure-sealed, and call-time verification performs no replaceable global trust lookup.
- Live-capability admission binds the exact capability object together with the exact `LocalFilesystemV1` instance identity; stable references or digests alone are insufficient.
- Audit progression: R0 completed outer re-pinning, immutable exact typed schemas, and kernel-domain pinning; R1 eliminated replaceable global pin and schema anchors; R2 closure-sealed exact class, literal-schema, and private pins; R3 closure-sealed recursive reconstruction, digest, and live-identity paths; R4 closure-sealed the final four constructors.
- Frozen accepted hashes are: `model` `F4A733FFAC7881A967CC8D82AC657B5304DCF617EC8812EA9E1CDF6B5CF79D62`; `ports` `3BB2EDED562F166748C6FE8ED8C22554DE4FB7E1328ACE593F41C00CC9105C1C`; `authority` `2E1839056BAB50F26A7B283ACCAD28B328357969E5B94AD80129EAE657E9A047`; `test_authority` `513FFDFE800D2CF93F170598C87D180AA18950C89F2F6DCB7D125A79F1B19ECC`; `security` `50CD2B9F6D5E312971E8D4C13DD342D75A5A70ED4C53138839C2360DF0D7FA94`; and `test_security` `BE5F9E7B3EA30E7663E111ECC8190F36E727275CC061AC5EF401C63F0FBE1281`.
- The shared Windows HMAC initializer was repaired for binary key material and exact cleanup behavior.
- Final independent verdicts are correctness auditor **ACCEPT**, security auditor **ACCEPT**, and tester **PASS**. Evidence: **82 focused**, **18 security with 1 expected symlink skip**, **680 Docker**, **997 host with 5 expected skips**, and **47 R0-R4 tests passed**.
- Residual boundaries: explicit method or closure-cell modification is out of scope; Windows ACL remains directory policy; no restart persistence is claimed; four WSL ext4 skips and one symlink skip remain expected.
- Next dispatch: release the accepted host checkpoint, then begin **Slice 5.6b.2 capability stores and acquisition ledger**.

### 2026-08-28 Docker Host Adapter Slice 5.6b.1 Release Checkpoint

- Host commit `896369419588c199e6fb67a5b82fe486f63f87c7`, parent `c3b82ce1d3ed532db7d1b462dcfc45153992d206`, was released with exactly seven paths: `.codex/pact/session.md`, `synaptic_host/docker_v1/model.py`, `synaptic_host/docker_v1/ports.py`, `synaptic_host/docker_v1/authority.py`, `tests/synaptic_host/docker_v1/test_authority.py`, `synaptic_host/security.py`, and `tests/synaptic_host/test_security.py`.
- Windows HEAD, the remote host branch HEAD, and canonical WSL host HEAD matched the exact host commit. Windows status was clean after release.
- The engine gitlink and submodule remained unchanged at `a1d28a9fa5b68400843386ad95dd885599a47d8e`.
- The two unrelated pre-existing WSL type-change entries remained preserved and untouched.
- Slice 5.6b.1 is released. Next dispatch: **Slice 5.6b.2 capability stores and acquisition ledger**.

### 2026-08-28 Docker Host Adapter Slice 5.6b.2a Registries And Resolver R1 Accepted

- Accepted components and contracts are `DockerStoragePathMappingPairRegistryPortV1`, `InMemoryDockerStageBundleStoreV1`, `DockerSingleLaunchSourceDeclarationResolverV1`, `DockerImmutableBundleSourceRegistryV1`, and `ImmutableDockerStoragePathMappingPairRegistryV1` serving pair, storage, and WSL projections.
- `BundleSourceV1.source_digest` is the registry capability digest. The resolver separately pins the planned payload `source_digest`, requires the request and prepared plan to match that payload digest, and pins the exact live `BundleSourceV1` object by `source_ref`.
- R1 requires every collaborator call to preserve an untouched canonical expected baseline, pass a distinct presentation, reconstruct the returned value, and require exact equality with the baseline including live identities before retaining or returning it.
- The correction covers stage post-authentication publication and lost-return recovery, source issue/authentication against the exact local declaration and envelope, and mapping-pair construction/projection against the exact pair and live capability identity.
- Frozen accepted hashes are: `ports` `04E2DC3EC297A2529A40E3F0AD70ECE9FF18656037BC59F12E6F2FA1F74E3B42`; `memory` `48DD183E6236B5E20E47082C17641190F1B3628D0DC34717F7859AD11F4FCEA3`; `capabilities` `9B14C2536F96B8758D1CF881E915D13BC65D10FC3893E77AB048CC723799F095`; `test_memory` `361120F40FA2DC2032257DDF60EB5F144C72131A6961266FD4A85A335FE3F187`; and `test_capabilities` `1FE77DEC8C0E7B301AE3268CC67203B31EC74DAA085E87E2C1D41320374D6A66`.
- Independent verdicts are auditor **ACCEPT** and tester **PASS**. Evidence: **28 focused**, **702 Docker**, **1,019 host tests passed with 5 skips**, and **18 targeted tests passed**.
- All stores remain same-process, and capability authority depends on exact live object plus filesystem-instance identity; no restart persistence is claimed.
- Next dispatch: release the accepted b.2a checkpoint, then begin **Slice 5.6b.2b acquisition ledger**.

### 2026-08-28 Docker Host Adapter Slice 5.6b.2a Release Checkpoint

- Host commit `6d7e050a883f9400bc6d6a56dacc025ccf19c91b`, parent `896369419588c199e6fb67a5b82fe486f63f87c7`, was released with exactly six paths: `.codex/pact/session.md`, `synaptic_host/docker_v1/ports.py`, `synaptic_host/docker_v1/memory.py`, `synaptic_host/docker_v1/capabilities.py`, `tests/synaptic_host/docker_v1/test_memory.py`, and `tests/synaptic_host/docker_v1/test_capabilities.py`.
- Windows HEAD, the remote host branch HEAD, and canonical WSL host HEAD matched the exact host commit.
- The engine gitlink and submodule remained unchanged at `a1d28a9fa5b68400843386ad95dd885599a47d8e`.
- The two unrelated pre-existing WSL type-change entries remained preserved and untouched.
- Slice 5.6b.2a is released. Next dispatch: **Slice 5.6b.2b acquisition ledger**.

### 2026-08-28 Docker Host Adapter Slice 5.6b.2b Acquisition Ledger R2 Architecture Accepted

- The exact acquisition order is `SOURCE_ROOT_AUTHORITY`, `SOURCE_READ_BORROW`, `STAGE_ROOT_AUTHORITY`, `STAGE_CREATE_BORROW`, `STAGE_VERIFY_BORROW`, then `ARTIFACT_ROOT_AUTHORITY`.
- Initial audit **REJECT** identified acquisition/enrollment leaks, same-thread cleanup deadlock, and weak alias/parent identity.
- R1 remained **REJECTED** because an exact-object collision released the provisional capability before the existing child; that could hit `BORROW_IN_USE` and lose parent cleanup authority.
- R2 is **ACCEPTED**: exact-object collision is detected first, the guard becomes `DISARMED_ENROLLED_COLLISION`, no direct release or new node occurs, and sole cleanup remains at the original ledger position for unified reverse unwind. An equal-descriptor but distinct object is provisionally direct-released exactly once.
- Every child binds an exact parent-node token. Completion requires the exact six-slot gate rather than descriptor/count similarity.
- Same-thread cleanup reentry returns nonterminal `REENTRANT_CLEANUP_IN_PROGRESS`; other threads wait for and converge on the cached terminal result.
- Slice b.5 builds all fallible parts first, transfers ownership last, attaches the sole ownership token, and only then publishes the handle.
- Frozen implementation scope is new `synaptic_host/docker_v1/capability_assembly.py`, new `tests/synaptic_host/docker_v1/test_capability_assembly.py`, and one focused assertion in `tests/synaptic_host/docker_v1/test_boundaries.py`.
- Required residual tests cover exact release order and count; collisions at every slot including parents with children; provisional release count zero for exact collision and one for distinct conflict; nonterminal reentry observation; transfer/abort and concurrent-release convergence; and redaction.
- Same-process crash recovery remains a later persistence concern.

### 2026-08-28 Docker Host Adapter Slice 5.6b.2b Acquisition Ledger Implementation Accepted

- The first implementation audit **REJECTED** premature ownership transfer, lost cleanup failures, dataclass-based collision authority, and result contracts too narrow to preserve lifecycle truth.
- Remediation adds explicit `DockerLiveCapabilityBuildV1`, which owns the assembly until transfer or abort; cached serialized abort plus transfer/abort race handling; complete provisional and ledger cleanup accounting with `CLEANUP_FAILED`; and explicit root/borrow stable keys applied only after exact-object collision checks.
- Results are normalized immutable failure/count/digest DTOs, while same-thread nonterminal reentry observation remains a separate result. Boundary and high-risk tests were strengthened.
- Final independent verdicts are auditor **ACCEPT** and tester **PASS**. Evidence: **15 focused**, **716 `docker_v1`**, and **1,033 host tests passed with 5 expected skips**.
- Frozen implementation scope and hashes are `synaptic_host/docker_v1/capability_assembly.py` `83B976B2304C633242DC19A279F0E77999DA62CBEDEB40547703D041E1157A3A`; `tests/synaptic_host/docker_v1/test_capability_assembly.py` `00A7CF510043567403B792C59EF5C58CB184AE5DFA11A20BE871785FB4E8D42A`; and `tests/synaptic_host/docker_v1/test_boundaries.py` `44452F9E82ECD1E155971901E0CAC71A17DCA5A4D5375F7AABE80F9C500A3D9E`.
- Crash recovery remains same-process only. Slice b.5 must preserve transfer-last integration: build fallible parts first, attach the sole ownership token, transfer capability ownership last, then publish the handle.

### 2026-08-28 Docker Host Adapter Slice 5.6b.2b Release Checkpoint

- Host commit `87ca77679d628332d8ba4dcbec744e0f8fb8b905`, parent `6d7e050a883f9400bc6d6a56dacc025ccf19c91b`, released exactly `synaptic_host/docker_v1/capability_assembly.py` `83B976B2304C633242DC19A279F0E77999DA62CBEDEB40547703D041E1157A3A`, `tests/synaptic_host/docker_v1/test_capability_assembly.py` `00A7CF510043567403B792C59EF5C58CB184AE5DFA11A20BE871785FB4E8D42A`, and `tests/synaptic_host/docker_v1/test_boundaries.py` `44452F9E82ECD1E155971901E0CAC71A17DCA5A4D5375F7AABE80F9C500A3D9E`.
- Windows HEAD, the remote host branch HEAD, and canonical WSL host HEAD matched the exact host commit.
- The engine gitlink and submodule remained unchanged at `a1d28a9fa5b68400843386ad95dd885599a47d8e`.
- The `.codex` session-ledger append remained unstaged from the release commit, and the two unrelated pre-existing WSL type-change entries remained preserved and untouched.
- Slice 5.6b.2b is released. Next dispatch: **Slice 5.6b.3 pair-consuming path binder and explicit environment resolver**.

### 2026-08-28 Docker Host Adapter Slice 5.6b.3 R1 Architecture Accepted

- Initial architecture audit **REJECTED** `DockerCreatePathBindingV1` because it authenticated nested path proofs without binding the outer source and artifact mapping-pair proofs.
- The accepted clean correction adds required `source_mapping_pair_proof_digest` and `artifact_mapping_pair_proof_digest` fields through `DockerCreatePathBindingV1` canonical serialization, builder, and snapshot/reconstruction. There is no compatibility bridge; pre-R1 CREATE-path envelopes are intentionally invalid.
- The path binder consumes the exact authenticated source and artifact mapping-pair envelopes; pins and reauthenticates them; validates roles, references, proofs, distro, live source-verify identity, and strict component containment; derives WSL requests; and issues authenticated CREATE-path evidence committing both outer pair proofs without translation or process effects.
- The environment resolver consumes immutable explicit policy plus private redacted values and never ambient `os.environ`. Resolution order is deterministic: deny, unallowed, secret unavailable, override, base, then missing. It returns the existing private resolution.
- Public environment evidence proves only requested keys and final nonsecret value digests. Secret diagnostic codes remain local-only.
- Frozen production scope is modified `synaptic_host/docker_v1/control_contract.py` and new `synaptic_host/docker_v1/binding.py`.
- Test scope is modified `tests/synaptic_host/docker_v1/test_control_contract.py`, `tests/synaptic_host/docker_v1/test_authority.py`, and `tests/synaptic_host/docker_v1/test_boundaries.py`; new `tests/synaptic_host/docker_v1/test_binding.py`; and verification of `tests/synaptic_host/docker_v1/test_create.py`, with edits only if a duplicated fixture is discovered.
- Final architecture auditor verdict: **ACCEPT**. No engine change is required.

### 2026-08-28 Docker Host Adapter Slice 5.6b.3 Implementation Accepted

- The first audit/test candidate was **REJECTED** for a raw secret carrier/API path, mapping-pair collision weakness, and missing pre-call live-identity pinning.
- R2 remained **REJECTED** for mutation windows around issue/authentication callbacks and insufficient environment-policy/configuration pinning.
- Final remediation removes the raw secret carrier/API and unconditionally rejects local secret transport before evidence, authority, or private argv construction; performs independent mapping-pair collision checks; and maintains separate constructor-time source live pins.
- Every output callback is guarded by pre- and post-call identity checks. Policy and override baselines are pinned with identity checks around every environment-authority callback. Concurrency, cardinality, and mutation regressions were added.
- Final independent verdicts are auditor **ACCEPT** and tester **PASS**. Evidence: **243 focused**, **765 `docker_v1`**, and **1,082 host tests passed with 5 expected skips**.
- Frozen scope and hashes are `synaptic_host/docker_v1/control_contract.py` `5ACA95D9D447BDF93560879977B683B8FC4C803112AF7B02E60BE5E2C3EED435`; `synaptic_host/docker_v1/binding.py` `ED1872A9E0FFAC915943D60F1033299B92FAB8E4B339EDB578A3B0EF15161DDD`; `tests/synaptic_host/docker_v1/test_binding.py` `F52FF8B802A7C6809AFCD136BA6CDE289B17154A585DE8607AB9C9A837B2840C`; `tests/synaptic_host/docker_v1/test_control_contract.py` `C24A4AC22D1AC7E7BE6D8CE00AFC1462AAD9A8B70AFB98FB3288A008261073A8`; `tests/synaptic_host/docker_v1/test_authority.py` `6DBF8F80662AF12003300BBF3C75A57B8F44D2C32CB1AB1A3D4E7354CC1318BA`; and `tests/synaptic_host/docker_v1/test_boundaries.py` `BC4672F6255733B4AD8D2395D09FB0DCBDA4874D16310EBA212F18565EDBC0F2`.
- Slice b.4 must preserve the resolved nonsecret environment bytes exactly without shell use, ambient-environment reads, or secret transport.

### 2026-08-28 Docker Host Adapter Slice 5.6b.3 Release Checkpoint

- Host commit `19e2116099f9e395a533a743c441c46782268166`, parent `87ca77679d628332d8ba4dcbec744e0f8fb8b905`, released the exact six paths and hashes recorded in the accepted b.3 implementation entry above.
- Windows HEAD, the remote host branch HEAD, and canonical WSL host HEAD matched the exact host commit.
- The engine gitlink and submodule remained unchanged at `a1d28a9fa5b68400843386ad95dd885599a47d8e`.
- `tests/synaptic_host/docker_v1/test_create.py` remained unchanged. The current session-ledger append remained unstaged from the release commit.
- The two unrelated pre-existing WSL type-change entries remained preserved and untouched.
- Slice 5.6b.3 is released. Next dispatch: **Slice 5.6b.4 argv0-only WSL interoperability for Windows `docker.exe`**.

### 2026-08-28 Docker Host Adapter Slice 5.6b.4 R1 Architecture Accepted

- Initial audit **REJECTED** a four-key delegate environment containing only `SystemRoot`, `TEMP`, `TMP`, and `WINDIR`. Web verification confirmed that implicit WSL/Windows fallback exists but is fragile and is not an acceptable authority boundary.
- The accepted design adds an explicit private `WSL_INTEROP` channel capability. The delegate environment is closed to exactly this order: `SystemRoot`, `TEMP`, `TMP`, `WINDIR`, `WSL_INTEROP`.
- The interop socket is pinned by final `lstat` identity without mutable timestamps. Only argv element zero is translated; every tail argument and value crosses the delegate boundary exactly.
- The factory performs exactly one `Popen`, returns that exact process immediately, and never retries. There are no post-spawn identity checks.
- The runner owns binary stdout/stderr drains, deadlines, output bounds, wait, terminate/grace/kill/reap, stream close, and sanitized result/evidence construction.
- Frozen scope is new `synaptic_host/docker_v1/interop.py`, new `tests/synaptic_host/docker_v1/test_interop.py`, and modified `tests/synaptic_host/docker_v1/test_boundaries.py`.
- No released-host contract or engine change is required. Slice b.5 must acquire and own this interop capability within the closeable host composition.
- Residual races are explicit: there is an unavoidable window between the final `lstat` identity check and native exec; a socket may retain identity while its server becomes stale; WSL restart requires composition rebuild; and native launch, argument transport, and cancellation remain unproven until Slice 5.6c.

### 2026-08-28 Docker Host Adapter Slice 5.6b.4 Implementation Accepted

- The first implementation audit **REJECTED** mutable channel-path/callback redirection, executable-validator drift, and missing hostile-boundary tests.
- Remediation maintains separate immutable channel path/stat baselines and working identity pins, performs pre- and post-callback `lstat` revalidation, and returns only the reconstructed local baseline.
- Executable policy now has exact parity, including case-insensitive `.exe` handling and superscript reserved-name rejection. Callback substitution, concurrency, caller immutability, and stdio/environment rejection tests were added.
- Final independent verdicts are auditor **ACCEPT** and tester **PASS**. Evidence: **262 focused**, **817 `docker_v1`**, and **1,134 host tests passed with 5 expected skips**.
- Frozen scope and hashes are `synaptic_host/docker_v1/interop.py` `B8DA5FF8AE7BA7F54DAF7193E54291979BE9BCDD023B60D20F1BE1F909204623`; `tests/synaptic_host/docker_v1/test_interop.py` `FC899592A09EFDE856FC232E1EE0EC51FC846222C1827456EE65CA1024DE04CE`; and `tests/synaptic_host/docker_v1/test_boundaries.py` `8AD56E9EF5E6D01A4DB4045321CFE7DE131636529FB18285C1079DF9E181CC31`.
- Verification spawned zero real processes. The final `lstat`-to-native-exec race and native interop behavior remain explicit Slice 5.6c proof obligations.

### 2026-08-28 Docker Host Adapter Slice 5.6b.4 Release Checkpoint

- Host commit `89b2eb1f0aca502d793b0e4260cca3e91bebdc6c`, parent `19e2116099f9e395a533a743c441c46782268166`, released the exact three paths and hashes recorded in the accepted b.4 implementation entry above.
- Windows HEAD, the remote host branch HEAD, and canonical WSL host HEAD matched the exact host commit.
- The engine gitlink and submodule remained unchanged at `a1d28a9fa5b68400843386ad95dd885599a47d8e`.
- The current session-ledger append remained unstaged from the release commit, and the two unrelated pre-existing WSL type-change entries remained preserved and untouched.
- Slice 5.6b.4 is released. Next dispatch: **Slice 5.6b.5 closeable leased host facade/composition**.

### 2026-08-28 Docker Host Adapter Slice 5.6b.5 Architecture Accepted

- Slice b.5 is sequential: **b.5a closeable leased facade**, then **b.5b production composition builder**.
- Product verbs are exact: `start_run()` delegates to `runtime.start()`, `reconcile_run()` delegates to `runtime.reconcile()`, `effect_binding(effect_kind)` delegates to `runtime.binding(effect_kind)`, plus `close()` and `lifecycle_state`.
- b.2b ownership integration is exact: `DockerLiveCapabilityBuildV1.transfer()` yields `DockerCapabilityOwnershipV1`; `DockerCapabilityOwnershipV1.cleanup()` terminalizes as `DockerCapabilityCleanupStatusV1.CLEANED` or `CLEANUP_FAILED`.
- `DockerHostLifecycleStateV1` is closed to `OPEN`, `CLOSING`, `CLOSED`, and `CLOSED_WITH_FAILURES`; close status is `CLOSED` or `CLOSED_WITH_FAILURES`.
- A close requested by the active operation thread is deferred with `ACTIVE_OPERATION_CLOSE_DEFERRED`. Close-owner reentry observes `REENTRANT_CLOSE_IN_PROGRESS`. Concurrent close callers converge on one cached terminal result, and cleanup executes exactly once.
- Composition builds all fallible parts first. The sole ownership cell is assigned only after `transfer()` succeeds, and the facade is published only after that transfer-last assignment.
- b.5a scope is new `synaptic_host/docker_v1/facade.py` and new `tests/synaptic_host/docker_v1/test_facade.py`.
- b.5b scope is new `synaptic_host/docker_v1/composition.py`, new `tests/synaptic_host/docker_v1/test_composition.py`, and one narrow update to `tests/synaptic_host/docker_v1/test_boundaries.py`.
- No engine changes are required. Slice 5.6c must run through this public facade rather than internal or ad hoc wiring.

### 2026-08-28 Docker Host Adapter Slice 5.6b.5a Facade R3 Accepted

- Frozen hashes are `synaptic_host/docker_v1/facade.py` `BC51882C3852BCAF52943786C3C25F3DEBB29CCCC12B802A13BF25342846EFD0` and `tests/synaptic_host/docker_v1/test_facade.py` `C860503E2CA12C80463BC46C8CBCB1B9D0410C65676D86094594BAB9FE34D389`.
- Final verification passed **85 focused**, **887 Docker-v1**, and **1,204 host tests with 5 expected skips**. Independent audit verdict: **PASS**.
- The accepted security boundary is cooperative same-process callers. Arbitrary reflection or mutation of private interpreter state is excluded; untrusted tenants require process/IPC isolation.
- Slice 5.6b.5a is accepted. Next dispatch: **Slice 5.6b.5b production composition builder**.

### 2026-08-28 Docker Host Adapter Slice 5.6b.5b Recoverable Composition Accepted

- Initial audit found a fallible ownership-cell setter after capability transfer. Architecture replaced detached transfer with one shared recoverable handoff controller.
- The authoritative controller advances `BUILDER_OWNING` to `HANDOFF_PREPARED` to `HANDLE_OWNING` to `CLEANING` to `CLEANED`. There is no detached token, transfer, or fallible cell setter.
- If prepare is interrupted before receipt, the builder aborts exactly once. If committed ownership is held but the facade is unpublished, recovery runs exactly once. Facade close and orphan recovery use `cleanup_owned()`.
- A mixed **24-caller** close/recovery race converges on one cached terminal result with exactly six releases.
- Final independent audit verdict: **PASS**. Verification passed **129 focused**, **931 Docker-v1**, and **1,248 host tests with 5 expected skips**, including interruption and convergence proofs.
- Frozen scope and hashes are `synaptic_host/docker_v1/capability_assembly.py` `B278FDD360AF468FB61C78F86D8243165D9FFF84F0311BE2EB7134978D760176`; `synaptic_host/docker_v1/facade.py` `6ECA754E241EB761DD853CD41EDC17268D958F09BF8077ADD39C455AC6EC7C11`; `synaptic_host/docker_v1/composition.py` `79F5249EAD8EC348F28C562433A1AA9221A6B04A2B5A4FD30526DAC1153B24AC`; `tests/synaptic_host/docker_v1/test_capability_assembly.py` `2935704E7058102FCFCA3C7CEFD9803368FBAD23A87BC45F471E6AD86192C52B`; `tests/synaptic_host/docker_v1/test_facade.py` `BB3E1DA933494760852F02137E4C4A276C7E4ED1D94A69E81010BDDE367E4181`; `tests/synaptic_host/docker_v1/test_composition.py` `610325800EF4836BE672DADD8086D25E9DDB00DC8C3797761B64F05513C4EDB2`; and `tests/synaptic_host/docker_v1/test_boundaries.py` `5C61D511620892C26D8C55BF5A3BA2CD84CDBB939BE70B7B34262FD3EB45FE27`.
- Slice 5.6b host composition is accepted. Next dispatch: **Slice 5.6c public-facade real Docker CPU smoke**.

### 2026-08-28 Training Run Cutover Slice 5.6c Architecture And 5.6c.1 Accepted

- The engine owns only provider-neutral training intent. The sole future product verb is `training run`; provider, profile, filesystem path, runtime, destination, credentials, and persistence are excluded from `TrainingInputV1`.
- Arbitrary final destinations remain supported through local staging followed by a host-owned publisher. Lazy host composition must not import or initialize Modal or SQLite.
- R0 found raw `OverflowError` from huge numeric conversion, escaped arbitrary `Mapping` callbacks/mutation, incomplete filesystem/credential reference screening, and missing numeric maxima.
- R1 closed overflow, mapping, and maxima issues but still accepted `C:relative`, encoded file scheme/userinfo, `aws_access_key_id`, and `private_key_id`; annotations also claimed `Mapping` while runtime required exact `dict`.
- R2 uses exact one-round strict percent/UTF-8 projection `p0` to `p1`: reject malformed or invalid encoding, residual percent escapes, and encoded structural bytes; validate both `p0` and `p1`; then store `p1`.
- R2 also rejects every drive prefix, projected `file:` scheme or authority, userinfo, and fragments; applies generic access/private-key component rules; and uses exact `dict` annotations.
- Final verdicts are independent audit **PASS** with **227 focused** and **313 contract tests passed**, plus one unrelated known Modal runtime-lock failure.
- Frozen hashes are `synaptic-tuner/synaptic_tuner/api/v1/training_input.py` `0BED2AF4BAE42EC280626ED7602DFA14A16EDA2A10DF85517D4C2E56A7B32B32`; `synaptic-tuner/synaptic_tuner/api/v1/__init__.py` `9B693F3D5380D65A34F82BEF3726A84BE3C9FB0A28FBE5CB56B4DCEBF363F6EC`; `synaptic-tuner/tests/contract/test_public_training_input_v1.py` `2B2BE8899835323325A4710793E637CE33BAFD26438FB32E62046FFB4EBAA4C6`; and `synaptic-tuner/tests/contract/test_provider_neutral_foundation_v1.py` `1FBF5763B010703F34672E9C1E3E8A1F4EBE3B9BD865BF6DF499D686187EB454`.
- Slice 5.6c.1 `TrainingInputV1` is accepted. Next dispatch: **Slice 5.6c.2 Host lazy `training run` dispatch and Modal direct cutover**.

### 2026-08-28 Training Run Cutover Slice 5.6c.2a Public Cold Loader Accepted

- Cold-ingress R0 architecture was initially accepted, then audit **REJECTED** a self-rejecting `uv` symlink rule, raw/nonadjacent submission callback handling, and mutable engine-origin authority.
- A proposed R1 private loader was **REJECTED** because it introduced a second engine class, private host coupling, `sitecustomize` dependency, and credential coupling. The corrected design is a submodule-first public cold loader.
- Public contracts are `TrainingInputContractCodeV1`, `TrainingInputContractErrorV1`, `TrainingInputContractIdentityV1`, `LoadedTrainingInputContractV1(identity, input_type, parse_json)`, and `load_training_input_contract_v1()` returning one exact cached identity. There is no public parser object.
- Loader R0 audit found exception-context leakage, concurrency weakness, and direct-identity weakness. Arbitrary private mutation remains excluded by the cooperative same-process threat boundary.
- R2 removes the public parser and clears traceback locals. Final independent audit verdict: **PASS**.
- Verification passed **77 focused** and **332 contract tests with 1 skip**, with one unrelated Modal lock failure. Under concurrency, **64 successes** produced one build and one exact shared bundle; **64 failures** produced one failed build and 64 distinct fresh closed errors.
- Frozen hashes are `synaptic-tuner/synaptic_tuner/api/v1/training_input_loader.py` `3B911E88A0475F0288723BF67EB9C65C70CA7914ED42E5FB55D7C746581B71C4`; `synaptic-tuner/synaptic_tuner/api/v1/__init__.py` `7E87D965BF1222324C56C0C37717202CA236285827760E98BDAC57388585626B`; `synaptic-tuner/tests/contract/test_public_training_input_loader_v1.py` `1BC97FA1FD4957701D170AE88747B3EF1D0CF38416DE03D4AED49642C297FCED`; and `synaptic-tuner/tests/contract/test_provider_neutral_foundation_v1.py` `ADBE69016432F2DE0BA9B4F1FB5BAA2FFCD27268021CC8A29E5D3A359303733A`.
- Next dispatch: release the loader, then host R1 consumes the exact public bundle with no submission state, an isolated `-I` bootstrap, and explicit `uv` symlink proof.

### 2026-08-29 Host Training Run Ingress Slice 5.6c.2a R1 Accepted

- Remediation enforces a closed per-error-code result-field matrix; all **16 field-presence patterns** are covered.
- `TrainingRunIngressV1` is factory-issued only, with a lock-protected weak-reference/anchor identity registry and exact loader, input, digest, and baseline revalidation.
- Raw `uv` output grammar is closed to exactly `uv 0.12.0` or `uv 0.12.0 (x86_64-unknown-linux-gnu)`, each optionally followed by one LF.
- Real WSL proof reached pinned Python `3.11.15`, reconstructed the stored proof, published atomically, and ran the fixed `-I -c` child, which emitted canonical `COMMAND_INVALID` with exit code `2`.
- Independent audit, real-runtime verification, and final audit all **PASS**. Evidence: **1,311 host tests passed with 6 skips**; **66 focused audit tests passed with 1 skip**; real WSL **1 passed in 64.30 seconds**, proof digest `fe3188833b3c41689db1751e8f74252e5af1a66dd949d821b404a21dc89373d3`.
- Frozen hashes are `synaptic_host/cli.py` `34CE22E89F4C82B66CFB8EA7E1F0AF1A6DEAE943890D492F6C0FAA4D2EADFEB5`; `synaptic_host/__main__.py` `3312F734F984212E9169BE24AEF84AD5A9EE207A1579DEEFB123990E368CCB1D`; `synaptic_host/launcher.py` `A753DB21E3E1743AF3B9B52922072C366D6CFA609C93FC053F16DF9A01736433`; `tests/synaptic_host/test_cli.py` `BDCE289205C998FC218EB91161FB2CFA920AA1B5ED636FFC50BC20F20E9DE1C6`; and `tests/synaptic_host/test_cold_bootstrap.py` `75147B606DCEB6013A1E3F4489A479EF439E01E562F6FE2CF9BFEAA7DA505905`.
- No provider, Docker, training, or SQLite action occurred. Modal/provider submission remains intentionally unproven in 5.6c.2a.
- Residual risks: executable and path reads remain path-level rather than descriptor-bound, leaving concurrent filesystem-replacement TOCTOU outside this slice; first host engine-cache initialization assumes single-threaded CLI first load rather than concurrent first-load convergence; and 5.6c.2b must explicitly decide whether bounded `HOME`, `PATH`, and certificate-path forwarding is acceptable child authority.
- Next release dispatch: commit the exact accepted candidate while excluding `.codex/pact` and `.test-tmp`; `.test-tmp` is excluded release evidence only. Then begin **Slice 5.6c.2b Modal composition**.

### 2026-08-29 Host Training Run Ingress Slice 5.6c.2a Release Checkpoint

- Host commit `5299746e2d621b7cab918bf7b9beff225f342a95`, parent `e32fd1b90319cf6e11c6fceff5cde7f58c468c9c`, released exactly `synaptic_host/cli.py`, `synaptic_host/__main__.py`, `synaptic_host/launcher.py`, `tests/synaptic_host/test_cli.py`, and `tests/synaptic_host/test_cold_bootstrap.py`.
- Windows HEAD, the remote host branch HEAD, and canonical WSL host HEAD matched the exact release commit. The engine gitlink remained at `b831cee9cbf0ec1b9ab71ba08878789ba8ddf4b7`.
- Windows retained only the PACT memory/session edits and `.test-tmp`; `.test-tmp` remains excluded release evidence. Canonical WSL preserved the two unrelated pre-existing type-change manifests unchanged.
- Host Slice 5.6c.2a is complete.
- Next dispatch context: Slice 5.6c.2b enters only through public `training run`. The engine remains provider-neutral; the host owns Modal policy, runtime selection, credentials, transport, and observation.
- 5.6c.2b must implement the host direct resolver and compose the real current Modal load-to-start path while preserving host-owned arbitrary-destination publication and the no-engine-persistence boundary. This ledger checkpoint authorizes no provider call.

### 2026-08-29 Modal Direct Cutover Slice 5.6c.2b Architecture Accepted

- Direct host composition is fixed: `TrainingInputV1` enters host Modal policy/resolution, then the released engine load/plan/preflight/start path, then host SQLite effect authority, then Modal spawn.
- The engine remains unchanged and provider-neutral. No database migration or schema change is required. The host result contract advances to v2.
- Modal credentials are constructed explicitly, provider storage remains staging only, and final destination publication remains host-owned. Logs, publisher integration, and live smoke are deferred.
- Official pinned API conclusions for Modal SDK `1.5.4`: named deployed function lookup uses `Function.from_name(..., environment_name=..., client=...)`; detached mutation uses `Function.spawn()` and persists the returned `FunctionCall` object ID; reconciliation uses `FunctionCall.from_id()`; explicit credentials use `Client.from_credentials(token_id, token_secret)`, and that client is passed explicitly.
- Implementation is sequential: **2b.1 policy and runtime lock**; **2b.2 direct resolver**; **2b.3 composition, result v2, and explicit credentials**; then **2b.4 verification**.
- First coder scope is restricted to `synaptic_host/modal_provider.py`, `training/providers/modal.json`, and `tests/synaptic_host/test_modal_provider.py`.
- Next dispatch: **Slice 5.6c.2b.1 policy and runtime lock**.

### 2026-08-29 Modal Direct Cutover Slice 5.6c.2b.1 Accepted

- Remediation corrected accidental `load_in_4bit: true` workload drift to the accepted exact `false` policy and binds policy into the configuration digest.
- Authority no longer accepts internally consistent state/journal evidence from a different Modal environment; both state environments must exactly equal configuration.
- Host configuration rejects mapping proxies and collection/string subclasses through exact JSON-type snapshot validation and callback closure.
- Volume opaque identities bind account, environment, and volume name. This intentionally invalidates the unreleased candidate state; there is no compatibility layer.
- Local authority loading performs zero external effects.
- Independent architecture and audit verdicts are **PASS**. Verification passed **25 focused** and **1,328 full tests with 6 skips**.
- Frozen hashes are `synaptic_host/modal_provider.py` `3789D04D51BB07611952A98FB777A635C0CDFE408DFF3C89D1D2FB427DE89BC3`; `training/providers/modal.json` `15FA87BE87FD808C0E6897C8C4F6202469FA38F1A55D37E813A2EE563E669A2F`; and `tests/synaptic_host/test_modal_provider.py` `00074529B0409253F126339D6CC08A72CE8B28308A0233D73083E3DE5416803C`.
- Next release: commit exactly these three files while excluding PACT state and `.test-tmp`, then dispatch **Slice 5.6c.2b.2 direct resolver**.

### 2026-08-29 Modal Direct Cutover Slice 5.6c.2b.1 Release Checkpoint

- Host commit `52f9464ff6efbe64bad1fb6679406cf171c7ba8d`, parent `5299746e2d621b7cab918bf7b9beff225f342a95`, released exactly `synaptic_host/modal_provider.py`, `training/providers/modal.json`, and `tests/synaptic_host/test_modal_provider.py`.
- Windows HEAD, the remote host branch HEAD, and canonical WSL host HEAD matched the exact release commit. The engine gitlink remained unchanged at `b831cee9cbf0ec1b9ab71ba08878789ba8ddf4b7`.
- Existing PACT/`.test-tmp` state and the unrelated canonical WSL manifest changes remained preserved and untouched.
- Next dispatch context: Slice 5.6c.2b.2 replaces `StrictModalTrainingResolver` with direct `ModalTrainingResolverV1`, consuming exact `TrainingInputV1` and the public loader identity.
- The resolver translates SFT intent, dataset reference, and artifact intent, and binds input, contract, source, ingress, and policy digests into `ExecutionSource` and the plan fingerprint.
- Expected scope is `synaptic_host/modal_resolver.py`, `synaptic_host/__init__.py`, `tests/synaptic_host/test_modal_resolver.py`, and `training/smokes/modal-sft.json`.
- No engine change, compatibility parser, or provider call is authorized for 2b.2.

### 2026-08-29 Modal Direct Resolver 2b.2 imPACT/rePACT Engine-First Recovery Accepted

- Blocker: `SourceLock.configuration` can store the five required provenance digests, but released `ModalDualCloneSourceFinalizer` discards configuration when producing `ExecutionSourceV1`. Authenticated evidence binds only the Git/source tuple, so provenance changes neither authenticated source identity nor the plan fingerprint.
- Rejected Option B: duplicating the five digests into `resolved_config` or `execution_context` would create a second mutable authority outside pushed-source authentication, require equality plumbing, contaminate recipe/context semantics, and permit divergence.
- Accepted clean engine design adds `SourceLock.canonical_bytes` and `SourceLockBindingV1` with explicit schema/version and a domain-separated digest. The binding is mandatory inside the signed `AuthenticatedSourceEvidenceV1` payload under provider-neutral purpose `source-lock-evidence/v1`.
- `ExecutionSource` embeds the authenticated evidence, so the plan fingerprint transitively binds the source-lock configuration.
- Correct V1 replaces the incomplete contract in place: no old reader, default, migration, or compatibility layer.
- Engine production scope is `tuner/project/source_bundle.py`, `tuner/project/execution_source.py`, `tuner/project/git_verification.py`, `tuner/execution/evidence.py`, `tuner/execution/providers/modal/resolution.py`, `tuner/execution/providers/modal/composition.py`, `schemas/synaptic-execution-source-v1.schema.json`, `synaptic_tuner/api/v1/sources.py`, and `synaptic_tuner/api/v1/__init__.py`.
- Engine test scope is `tests/project/test_source_bundle.py`, `tests/project/test_git_verification.py`, `tests/execution/providers/test_modal_source_resolution.py`, `tests/execution/providers/test_modal_composition.py`, `tests/execution/providers/test_modal_bundle.py`, `tests/contract/test_public_training_api_v1.py`, `tests/contract/test_provider_neutral_foundation_v1.py`, `tests/trainers/sft/test_runtime_v1.py`, `tests/training/test_sft_compilation.py`, and `tests/training/test_training_service.py`.
- Nested sequence is mandatory: implement the engine contract, independently audit it, release the engine, update the host gitlink, then resume host Slice 2b.2.
- Parent-plan impact: host 2b.2 is paused behind this nested engine prerequisite. No database change or user decision is required.

### 2026-08-29 Nested Engine SourceLockBindingV1 Cycle Accepted

- The accepted contract provides strict canonical `SourceLock`, public `SourceLockBindingV1`, and mandatory inclusion inside signed authenticated source evidence under purpose `source-lock-evidence/v1`. Callbacks are sealed, values use exact built-in types, and correct V1 replaces the incomplete contract with no compatibility path.
- R1 closed nonfinite and Unicode canonicalization gaps; live-lock/evidence callback mutation; remote swap/restore; `AuthenticatedSourceEvidenceV1` and `GitSource` subclass bypass; mapping-proxy/raw callback leakage; and added actual five-key `TrainingPlan` fingerprint coverage through centralized sealed snapshots.
- R2 closed exact field-name `str`-subclass callback leaks and non-exact `ExecutionSource` identity strings through centralized exact built-in dictionary/key validation. Hostile callbacks remain zero-effect.
- Final architecture, audit, and test verdicts are **PASS**. Evidence: complete scoped gate **294 passed / 4 skipped**; hostile gate **103 passed / 1 skipped**; new nodes **20/20 passed**.
- Full-suite environmental blockers are separately classified: missing `sklearn` caused 10 failures, one Windows resource failure remained, and an old `huggingface_hub` lacking `sync_bucket` caused one failure.
- Frozen production hashes: `schemas/synaptic-execution-source-v1.schema.json` `BC385B6381487A1A061D3DD5E7F0F8F55F9FAD9383D0E18C39580BFA6EDBCF12`; `synaptic_tuner/api/v1/__init__.py` `A9E0810F020DC08506FA151C0DFCDEA7DCB39AD29292B9354B09DA116AD2A3E9`; `synaptic_tuner/api/v1/sources.py` `DA1FE5FDF0B973DE0187BE93C5C2D37F4F2DCF53C98BD38644BF26C54398C39C`; `tuner/project/source_bundle.py` `16368658DB727680F74326603E2D28F3AE9B5E481F7626C7BE1A8280B588ECEC`; `tuner/project/execution_source.py` `29B3B50910C751DEBCFEEFBB338BD29735718F6B9B1ED91840EAB3CCF1E28E0E`; `tuner/project/git_verification.py` `0CFE00560C704EDDBE688A0C7156C12F9ACD2F321046017F50EB5D9E3BB61710`; `tuner/execution/evidence.py` `A04CC6843A794E62A702608D28C8E82D0C57AF8227B3CB9743CF56B9605442CA`; `tuner/execution/providers/modal/resolution.py` `5C7268AA644103AE0712B03ED55918527D6E2ED6F4120EF169866B0FFD1CBF6F`; and `tuner/execution/providers/modal/composition.py` `57B64361FCDA60109D446258E0796898B3F8B6D1249E567336ED40AFA36ABBEB`.
- Frozen test hashes: `tests/project/test_source_bundle.py` `0AF06C79E107B73AFD7FBA148FB8CCF6A21C89142133C2D9CF7FBB6099D716A1`; `tests/project/test_git_verification.py` `50CDFDE9161B36E9C765511F243BA3E4B0BF2FEEF7E06C47B315924FFFCC143D`; `tests/execution/providers/test_modal_source_resolution.py` `56AF1E019EAE63E4CF3A1299759F6F510F558EBE4B12FA16541A25CF930D7F16`; `tests/contract/test_public_training_api_v1.py` `C3F3A10EFAA07BA1D9151DC63C3757C5E512D02D976C32814FB25A8ADB17C079`; `tests/contract/test_provider_neutral_foundation_v1.py` `E8086978EA18BA2A7A777CA6DEE52D17312F107748D8C341E23A83057B85B15B`; `tests/trainers/sft/test_runtime_v1.py` `8AC0E260426B2D98CF83ABA555F7039B7314F8A79DC3AC605E1EA297CA5D19E8`; `tests/training/test_sft_compilation.py` `6DB2D197499BB002BDFD1B9483B551F4EBC133AFF8A8F99530795332A66C842E`; and `tests/training/test_training_service.py` `A87E11B5DEF3DB6AC20B6D82D3942F2BCB1D8F021F162728D44C215E81ADE461`.
- Next release sequence: release the engine branch, update the host gitlink, then resume host Slice 2b.2.

### 2026-08-29 Nested SourceLockBindingV1 Release Complete

- The engine was released at `d57ebe63dbbc8d277cb31cf09a87fcefdc908439`, and the host gitlink was released at `e008436191118185b3b37e4a0258a75ad35801b3`.
- Windows, remote, and canonical WSL revisions matched exactly for both the engine and host.
- The two unrelated WSL type-change manifests remained preserved. Windows retained only PACT/`.test-tmp` state, and the engine retained only pytest residue.
- The nested `SourceLockBindingV1` cycle is complete.
- Host Slice 2b.2 resumes in its existing four-file scope with exact five-key `SourceLock.configuration`; provenance must not be duplicated into `resolved_config` or `execution_context`.
- The released authenticated source evidence now transitively binds those five keys into the plan fingerprint.

### 2026-08-29 Modal Direct Resolver Slice 5.6c.2b.2 R1 Accepted

- Blocker 1: the finalizer could mutate or reduce `SourceLock` and return matching evidence because comparison used the post-callback lock. R1 seals the canonical exact five-key lock/binding, passes only a distinct canonical clone, rechecks that clone, and reconstructs returned evidence against the untouched baseline.
- Blocker 2: contract, source, and ingress digests plus inspector/finalizer identities were not pinned at construction. R1 freezes the construction baseline and checks it at entry, around every callback, and before return.
- Blocker 3: returned deployment selection could differ from authority/resources, including 7,200 versus 3,600 seconds. R1 reconstructs returned execution/deployment evidence and requires exact equality with the authority-sealed selection.
- Blocker 4: dataset-path reopen TOCTOU left bytes unbound to the checked identity. R1 uses descriptor-bound no-follow hashing with pre/post `lstat`/`fstat` identity checks and descriptor-only streaming.
- Blocker 5: inspector/finalizer and ordinary I/O errors leaked raw context. R1 returns a fresh generic `TrainingResolutionError` with empty cause/context while leaving `KeyboardInterrupt` and `SystemExit` unswallowed.
- Independent tester verdict: **PASS**. Evidence: resolver **39 passed / 1 skipped**; provider plus resolver **64 passed / 1 skipped**; full host **1,362 passed / 7 skipped**; hostile plus prior critical **37 passed / 1 skipped**.
- Independent auditor verdict: **PASS**, no findings.
- Frozen hashes are `synaptic_host/modal_resolver.py` `8639AE152518368B27BABDC391C2C545C5418F061DB5F610BB77AC8134B7021D`; `tests/synaptic_host/test_modal_resolver.py` `3CEB404310D0E8CF0B3C4F8CBB3128C2433A2B65C620F553A05BA0C42A5426BA`; `synaptic_host/__init__.py` `42E5F783A1BC5B4BBDB17EDD98B0D94EE67844ED0CCCE291C092D69BC5410ADF`; and `training/smokes/modal-sft.json` `6AF4FBD115D63479586BDA897845650757D2651D7EFF877BFD3E4E15FFB162C5`.
- Slice 5.6c.2b.2 is accepted and ready for scoped release, followed by **Slice 5.6c.2b.3 composition, result v2, and explicit credentials**.

### 2026-08-29 Modal Composition Slice 5.6c.2b.3 Architecture Accepted

- No engine or database-schema change is required. The host reuses the existing SQLite attempt-before-spawn authority boundary.
- If Modal accepts the spawn but the `FunctionCall` object ID is not durably persisted, the operation becomes `RECONCILE_REQUIRED`; automatic respawn is forbidden.
- Implementation is host-only and sequential: **2b.3a result v2 plus Modal-child credentials**; **2b.3b composition plus durable outcome classification**; then **2b.3c sole public CLI wiring**.
- The database remains main-project owned at `.synaptic/state/training.sqlite3`.
- Credentials are forwarded only to the selected child process.
- Logs, publisher integration, and live Modal execution remain deferred.
- Current dispatch is restricted to **Slice 5.6c.2b.3a result v2 plus Modal-child credentials**.

### 2026-08-29 Modal Composition Slice 5.6c.2b.3a R1 Accepted

- Initial audit **REJECTED** Unicode category-C leakage through result fields, exact-string/category-C bypasses in allowlisted child environment values, and stale V1 result-helper names after the v2 cutover.
- R1 centralizes exact built-in-string validation for every V2 public reference field: values are UTF-8 bounded and reject every Unicode category beginning `C`. The emitter reconstructs exact V2 and totalizes hostile mutation to canonical `INTERNAL_FAILURE` without leakage.
- Every general or Modal-forwarded child environment value uses the same exact-string, category-C, and 4,096-byte validation; subclasses are rejected before callback, only detached UTF-8 round-trip snapshots are forwarded, and invalid values fail or are omitted before spawn.
- Result helpers are renamed to `emit_training_run_result_v2` and `bootstrap_unavailable_result_v2`; `__main__`, exports, and calls use the new names with zero aliases. Ingress V1 contracts remain intentionally unchanged.
- Independent re-audit verdict: **PASS**. Independent tester verdict: **PASS** with focused **181 passed / 1 skipped**, full host **1,477 passed / 7 skipped**, and hostile **89 passed / 0 skipped**.
- Frozen hashes are `synaptic_host/cli.py` `25D5EE1316581BA0BED2DC5F825858DE0968C8A5A5C94C378BC1914C7FACA949`; `synaptic_host/launcher.py` `9F9888B88BB0A703172478CCB48337972DA03B33986E80D868001B8E19338F68`; `synaptic_host/__main__.py` `79EADCC4E730716CC5202598003A67444FC4CE1BBDE6290CD166FCE6E0520913`; `tests/synaptic_host/test_cli.py` `7341EB7FA4AE088B33F90DF5A0341BED0AEB22B7AB49872AB476269AEBFD41CE`; and `tests/synaptic_host/test_cold_bootstrap.py` `BFC24543F7446AD9591868F184470B160F89424E2E94FE9FA7302B733E252AA4`.
- Slice 5.6c.2b.3a is accepted and release-ready. Next dispatch: **Slice 5.6c.2b.3b composition and durable classification**.

### 2026-08-30 User-Approved imPACT Engine Lifecycle Expansion

- Repeated Modal atomic-review cycles identified a systemic root cause: permissive generic lifecycle semantics rather than an isolated Modal adapter defect.
- Joseph authorized expanding the Synaptic-Tuner submodule scope to implement canonical event-message and effect-authority binding instead of continuing Modal-local patches or artificially narrowing behavior.
- The current released host remains at `8e13884`. Host 2b.3b and engine R4 candidates remain uncommitted and frozen.
- No provider effects occurred.
- Next work proceeds engine-first through the expanded provider-neutral lifecycle contract before host Modal composition resumes.

### 2026-08-30 Systemic Engine Lifecycle R1 And Modal Atomic Contract Accepted

- The root issue was permissive generic lifecycle semantics rather than a Modal-local defect. The final systemic R1 received architecture, audit, and test acceptance.
- Provider-neutral lifecycle guarantees now require full predecessor-history replay, exact event-message-to-payload mapping, active effect-authority and provider-outcome binding, and exact parser closure.
- The generic lifecycle supports valid `SUBMIT` to `CANCEL` progression and remains independent of Modal.
- No schema migration, compatibility layer, or generic Modal dependency was introduced.
- Verification evidence: **77 focused passed**, **1,275 execution passed / 3 skipped**, and **31 hostile passed**.
- The known runtime-lock mismatch and 12 environment collection errors remain separately classified as unrelated.
- The nested Modal atomic interface is stable through public `ModalPreparedRunV1` and `create_modal_prepared_run`.
- The engine candidate and host 2b.3b candidate remain uncommitted; the released host remains at `8e13884`.
- Next dispatch: implement the host adapter against the stable public Modal prepared-run interface.

### 2026-08-30 Modal Composition Slice 5.6c.2b.3b Released

- Engine commit `bf818dd19941f5922eac37d638eb27249f30221c` adds exact public-plan/operation fingerprint adjacency, a public provider-neutral five-key SourceLock provenance validator, and public detached execution-source extraction while keeping Modal bundle parsing private to the engine.
- Host commit `1719317a5f2a0137b0022be39b996a7cfc67b782` composes durable Modal submission against the released engine contract and the main-project SQLite repository at `.synaptic/state/training.sqlite3`.
- Durable lifecycle plus preparation creation is atomic. `ATTEMPTED` is persisted before spawn; replay and concurrent identical submissions never respawn; uncertain outcomes reconcile instead of retrying.
- Local durable pair loading and structural classification precede clock, source inspection, SDK loading, credentialed session construction, and provider reads. Only exact absence and statically validated `FOUND` cross the Modal session boundary.
- Durable replay validates exact plan fingerprint, project/run/effect adjacency, current Modal authority/policy, all five SourceLock provenance values, and exact known provider call identity.
- Every callback seam is ingress-authenticated before and after use, including preflight, rejection-time durable classification, and `FOUND` restoration. Callback mutation closes as `INTERNAL_FAILURE` without an operation-bearing result.
- The concurrency loser performs one read-only durable reclassification after authentic provider preflight rejection; exact concurrent state reconciles, while exact absence remains `PREFLIGHT_REJECTED`. There is no retry, polling, sleep, lock, or second spawn.
- Final independent evidence: engine provider **705 passed / 3 skipped**; engine focused **161 passed / 1 skipped**; host Modal focused **67 passed**; full host **1,536 passed / 7 skipped**; restoration audit **PASS**; 40 barrier concurrency cases passed with exactly one spawn each.
- No live provider call, credential use, database migration, compatibility layer, CLI wiring, artifact publisher, or observation loop occurred in this slice.
- Windows and remote heads match the released commits. Canonical WSL host and detached engine heads match exactly; the two unrelated WSL type-change manifests remain preserved.
- Next dispatch: **Slice 5.6c.2b.3c sole public `training run` CLI/API wiring**, followed by Docker observation/artifact publishing and a local CPU smoke before any paid Modal run.

### 2026-08-30 Public Training Run Wiring Slice 5.6c.2b.3c Released

- Host commit `afa9857562feeb248ab9e74ded5ed458a0b3f4a2` replaces the Modal `COMPOSITION_UNAVAILABLE` placeholder with the released private durable Modal executor while preserving the sole public `training run` dispatch.
- Direct API calls cannot bypass the isolated launcher. Modal execution requires a closure-private, factory-issued, one-use child authority minted only after exact runtime-proof, interpreter, root, ingress/contract digest, and credential-snapshot validation.
- Docker and rejected/cold-parent paths return before launcher import, Modal/provider/SQLite import, or credential access. The parent emits nothing; the authoritative child emits exactly one canonical V2 result.
- Dispatch reauthenticates ingress across launcher import, authority authentication and consumption, credential access, Modal executor import, executor call, and result reconstruction. Mutation before an effect yields `INTERNAL_FAILURE` with zero executor calls.
- The original audit reproduction—consume-time runtime-proof mutation on both return and raise—now produces zero Modal imports and zero executor calls. Authority-authentication, credential-environment, and executor-import mutation seams are also closed.
- Authority forgery, copy, replay, proof/interpreter/root/credential drift, and 64-way concurrent consumption are covered; exactly one consumer may reach the executor.
- Final independent evidence: remediation nodes **6 passed**; focused CLI/bootstrap **192 passed / 1 skipped**; critical controls **30 passed**; full host **1,547 passed / 7 skipped**; audit **PASS**; no external provider/process/database effects.
- No compatibility alias, second public verb, schema/database/engine/provider change, observation loop, publisher, or live provider call was introduced.
- Windows, remote, and canonical WSL host heads match `afa98575`; engine remains `bf818dd1`. The two unrelated WSL type-change manifests remain preserved.
- Next dispatch: design and implement provider-neutral observation plus host-owned artifact publication, beginning with Docker/local CPU proof before a paid Modal smoke.

### 2026-08-30 Post-Start Observation And Publication Architecture Accepted

- There is no honest successful submodule-first Docker smoke command yet. The public `training run --provider docker` path correctly returns canonical `PROVIDER_UNAVAILABLE`; the legacy `tuner.py local-run` path is GPU-oriented and bypasses the new Runs/Artifacts architecture.
- Docker Desktop is healthy and an offline pinned Alpine image is already local, but the released Docker public composition explicitly uses same-process in-memory workflow, grant, effect, binding, stage, and reconciliation stores. Restart durability is unproven by contract.
- The engine already contains authenticated Docker observation, bounded logs, verified artifact inventory/streaming, provider-neutral Runs operations, and a strong publication coordinator with claim/ownership/ambiguity/readback semantics.
- Two engine API generations coexist: legacy formally exported runs/artifact contracts and newer `runs_facade`/`artifacts_facade` contracts used by the current coordinator. The newer facades require exact boundary hardening and formal public promotion before host composition.
- `synaptic_host/artifacts.py` is obsolete as a coordinator: it accepts structural verified-source spoofs, retains mutable destination mappings, hardcodes five artifact filenames, performs external publication before any durable claim, retries ambiguous Hugging Face effects, leaks raw provider/database errors, and uses path-based local publication with containment/TOCTOU gaps.
- The project-level SQLite database location remains correct, but its receipt-only `artifact_publications` table cannot implement publication claim, fenced ownership, ambiguity, recovery, lookup, or verified readback and is tied to the Modal lifecycle family rather than Docker workflows.
- Accepted sequence: (1) engine public Runs/Artifacts contract consolidation with no compatibility aliases; (2) host authenticated verified-source, immutable destination registry, and project-level durable publication store; (3) capability-safe local destination adapter; (4) restart-capable Docker execution/reader bridge; (5) offline pinned-Alpine infrastructure smoke; (6) one-step cached/pinned CPU model smoke; (7) Hugging Face ambiguity/reconciliation; (8) Modal observation reuse.
- Docker same-process composition remains a focused test adapter. The product smoke requires a restart-capable host adapter that can reopen state, rediscover the exact container, reconcile without duplicate create/start, verify artifact bytes, publish once, and reopen the publication receipt.
- No source, provider, container, network, or database effect occurred during this architecture phase.
- Next dispatch: nested engine-first consolidation of the exact provider-neutral Runs/Artifacts public contract.

### 2026-08-30 Canonical Runs/Artifacts Public Cutover Released

- Engine commit `4ec0a13c9dff81cb91361358943c0bf00a1c278f` promotes the hardened `Runs` and `Artifacts` facades as the sole formal root API, adds the provider-neutral public publication coordinator composition surface, and deletes the competing legacy `runs.py` and `artifacts.py` contracts without compatibility aliases or readers.
- `PublicationResult` V1 now requires an exact `TrainingRunRef`; callback boundaries reconstruct nested identities, reject non-exact built-in representations, recheck mutation on return and raise, and suppress raw collaborator errors when mutation is detected.
- Host commit `e0bea5562eed59841ab0f0a59f5156838e8fa8c9` records that engine gitlink and deletes the obsolete host artifact publisher plus its tests. The old receipt-only SQLite methods remain untouched but unreferenced pending replacement by the durable publication state machine.
- Independent final evidence was **PASS**: focused facade **42 passed**; aggregate contract/provider **224 passed**; full host **1,544 passed / 7 skipped**; no provider, network, container, credential, or production-database effect occurred.
- Windows, remote, and canonical WSL revisions match exactly. The two unrelated WSL type-change manifests remain preserved as the only WSL differences.
- Next dispatch: host-owned immutable destination registry, authenticated verified-source adapter, and project-level durable `PublicationStorePortV1` state machine. No external destination effect is permitted until those authority and durability boundaries pass review.

### 2026-08-30 Durable Publication Engine Prerequisite Released

- Architecture review found that a host SQLite adapter would otherwise have to duplicate the engine's full publication-record grammar and transition rules. The submodule-first correction was therefore completed before host persistence work.
- Engine commit `1916d905595ec905933f1b99631fdb3ab7baece6` adds the complete bounded canonical `PublicationRecordV1` persistence envelope and the provider-neutral pure `PublicationTransitionKernelV1` used by the reference in-memory store and future durable stores.
- Canonical persistence covers command, claim, phase/revision, events, ownership, recovery permits, lookup evidence, receipts, tombstones, and record digest. Parsing requires closed exact fields, canonical UTF-8 JSON, duplicate-key rejection, bounded bytes, constructor/digest revalidation, and byte-identical reconstruction.
- The transition kernel owns claim, CAS, transfer admission/completion, fencing, ambiguity, recovery, and terminal finalization; the host is now responsible only for transactional storage, ownership liveness, and indexing.
- Independent verification passed **271/271** coordinator tests and **190/190** publication/export/import tests. Independent code audit passed with no blocker. Seven broad contract failures were classified as existing Windows fixture/runtime-lock conditions.
- Host commit `55373dd429553e6606221dd14d5c208dfbfd0800` records the engine gitlink. Windows, remote, and WSL parity match; the two unrelated WSL type-change manifests remain preserved.
- Next dispatch: replace the unreferenced receipt-only host SQLite surface with the project-level durable publication-record adapter and immutable authenticated destination registry.

### 2026-08-31 Project-Owned Durable Publication Store Released

- Host commit `1564f3f74916179c2d8f1e0342cc7a42fa8047bc` adds `SqlitePublicationStoreV1` at the main-project persistence boundary and removes the obsolete receipt-only publication methods and fresh-schema creation from `SqliteTrainingRepository`.
- The store persists the engine's canonical `PublicationRecordV1` bytes and delegates all claim, CAS, ownership-transfer, ambiguity, recovery, and terminal transitions to the exact public `PublicationTransitionKernelV1`; the host adds only SQLite transactions, canonical metadata indexes, and renewable process leases.
- Publication list reads now scan, reconstruct, validate, filter, and paginate within one explicit SQLite snapshot. Canonical bytes and every mirrored metadata column fail closed on drift or corruption.
- Lease renewal acquires the SQLite write lock before sampling time and requires the prior lease to remain unexpired. Store shutdown is terminal, linearized against operations and heartbeat creation, and waits for every registered heartbeat thread to terminate.
- SQLite failures are translated to the closed host error without leaking raw exception cause or context. Cold import remains lazy.
- Independent final evidence: API audit **PASS**; focused publication store **12 passed**; focused plus adjacent SQLite **34 passed**; full Host **1,556 passed / 7 expected skips**. Deterministic races cover atomic list snapshots, stale-time renewal, registered-before-start shutdown, blocked-heartbeat shutdown, and 32-way claim/admission convergence.
- Windows, remote, and canonical WSL host heads match `1564f3f7`; engine remains `1916d905`. The two unrelated WSL type-change manifests remain preserved.
- Existing databases may still physically contain the now-unreachable legacy `artifact_publications` table. It is not read, written, or created by the current code; physical removal is deferred to an explicit destructive migration decision rather than performed silently.
- No provider, network publication, Docker, credential, or production-database effect occurred.
- Next dispatch: immutable destination registry plus authenticated verified-source composition, followed by a capability-safe local destination adapter.

### 2026-08-31 Publication Trust And Destination Architecture Accepted

- No engine prerequisite is missing. The released `PublicationOperationsV1`, destination/source ports, authenticated envelopes, evidence authority, and `ArtifactsAPI` already define the provider-neutral composition boundary.
- This slice is host-only: domain-separated publication evidence under the project state root, an immutable adapter-registration-based destination registry, and an authenticated verified-source adapter over exact public `RunsAPI`.
- The registry remains destination-kind agnostic. `adapter_ref` selects a constructor-supplied exact registration; local paths, Hugging Face references, and future destination settings remain opaque adapter-specific canonical configuration.
- The currently unused `training/artifacts.json` is replaced in place with the closed v1 host destination contract; no compatibility reader or second configuration layer is added.
- Publication evidence uses a dedicated HMAC key and exact lowercase digest tags. Only typed destination/source issuers may mint descriptors; the engine-required verifier is the public validation surface.
- Verified source description requires a successful run, explicit `RunsAPI.reverify`, an unchanged second outcome, a nonempty canonical inventory, and a deterministic verification digest that excludes retry timestamps. Artifact bytes remain streamed and are independently rehashed by the engine before destination admission.
- Host `RunsAPI` composition remains a later Docker observation prerequisite for a real publication smoke, not an engine API gap.
- No CLI, database, Docker, Modal, provider, network, credential, or production-state effect is permitted in this slice.
- Implementation order: publication authority, immutable destination config/registry, verified-source adapter, then independent audit and full Host verification.

### 2026-08-31 Publication Trust And Destination Registry Released

- Host commit `db74e86b32077ad668e2a79aba9f5c49afc24171` adds provider-neutral publication evidence, a closed immutable destination registry, and an authenticated verified-source adapter over exact public `RunsAPI`.
- `training/artifacts.json` is replaced in place with the sole closed `synaptic-host-artifact-destinations/v1` contract. Destination-specific settings are canonical opaque configuration selected through immutable `adapter_ref` registrations; local, Hugging Face, and future adapters use the same registry code with no kind switch or compatibility reader.
- Publication HMAC evidence uses the project-owned `.synaptic/state/publication/evidence-hmac.key`, exact lowercase tags, engine-defined domain separation, typed issuers, and a verifier-only generic public surface. Closure-private anchors bind key continuity, each authority view, registry contents, adapter identity/callbacks, and the exact `RunsAPI` backing operations.
- Registry construction snapshots configuration, policy, registration, and descriptor state across factory callbacks. It rejects recursive credential-bearing configuration, factory mutation/substitution, adapter replacement, and raw callback error leakage.
- Verified source description requires successful run state, exact `show -> reverify -> show` inventory stability, deterministic source identity, authenticated evidence, and exact stream adjacency. The engine remains responsible for bounded streaming and full size/SHA-256/EOF verification before destination admission.
- Initial hostile review rejected key-path substitution, factory mutation, binding replacement, `RunsAPI` backing replacement, camelCase credential fields, and factory error leakage. R1 closed those paths; R2 moved trust anchors out of mutable slots/module globals into closure-private records. Final independent audit and verification both passed.
- Final evidence: focused **49 passed**; explicit remediation controls **9 passed**; adjacent **179 passed / 1 expected skip**; full Host **1,605 passed / 7 expected skips**; 32 concurrent descriptions converged on one source digest/tag; cold import and diff checks passed.
- Windows, remote, and canonical WSL host heads match `db74e86b`; engine remains `1916d905`. The two unrelated WSL type-change manifests remain preserved.
- No engine, database schema, CLI, Docker, Modal, provider, network, credential, or production-database effect occurred.
- Next dispatch: capability-safe local spool and destination adapter, then compose `PublicationOperationsV1` with `SqlitePublicationStoreV1` and prove durable publish/verify/reopen locally.

### 2026-08-31 Capability-Safe Local Publication Architecture Accepted

- The existing `StorageRegistryV1`, `PosixRetainedDirfdPortV1`, and `LocalFilesystemV1` already provide the required root authorization, retained-handle traversal, exclusive create, durable per-file journals, content revalidation, and restart recovery. The local publisher will be a thin composition over those capabilities, not a raw-path implementation.
- One engine-first prerequisite is required: exact public canonical codecs for the already-public destination inventory, receipt, and tombstone evidence types. Local restart lookup must persist and reconstruct those envelopes; duplicating the engine's private parsers in the host is prohibited.
- Local destination configuration is refined to capability references (`data_root_ref`, `control_root_ref`) with no compatibility reader. Actual project or external paths live only in `training/storage.json` and are governed by `StorageRegistryV1`.
- The authenticated destination identity must bind the resolved local root authority digest, so changing a path behind an unchanged textual root reference changes destination identity.
- Spooling uses its own authorized local root and a new exact publication-spool borrow purpose. Opaque spool refs bind the publication, role, nonce, size, digest, and retained file identity; adapters read only through `LocalFilesystemV1.iter_source`.
- Final artifacts use deterministic flat components derived from publication and role digests. A single exclusive terminal evidence component is written last and is the multi-artifact commit marker; partial artifact materialization without it remains incomplete.
- Lookup reconstructs exact signed terminal evidence. Receipt versus tombstone competes for the same exclusive terminal component, preventing both publication and definite absence from becoming authoritative.
- This capability is POSIX-only through the existing retained-dirfd port. Native Windows support is not claimed; WSL is the intended local execution environment for the first real proof.
- Implementation order: engine public evidence codecs; typed host evidence issuers; local root config refinement; local spool; local destination; engine in-memory composition; host SQLite restart proof; POSIX/WSL proof.

### 2026-08-31 Engine Publication Evidence Codec CODE Accepted Provisionally

- The engine CODE handoff is accepted as a complete candidate for the codec prerequisite. Independent audit, test/release review, checkpoint, and push remain pending.
- Exactly two engine paths changed:
  - `synaptic-tuner/tuner/execution/coordinator_v1/publication.py`
  - `synaptic-tuner/tests/execution/coordinator_v1/test_publication.py`
- The exact five already-public evidence surfaces now expose strict `to_dict`, `from_dict`, `canonical_bytes`, and byte-identical `from_canonical_bytes` reconstruction:
  - `DestinationArtifactV1`
  - `DestinationInventoryV1`
  - `AuthenticatedDestinationInventoryV1`
  - `AuthenticatedPublicationReceiptV1`
  - `AuthenticatedPublicationTombstoneV1`
- `DestinationInventoryV1.to_dict` received the accepted document correction so its emitted document matches the canonical public codec contract and reconstructs byte-identically.
- Focused codec verification passed **10 out of 10**.
- Broader publication verification passed **106 out of 106**.
- Scoped diff check passed.
- No commit or push was created by the coder.
- The engine coder is complete and retained for ownership-routed remediation.
- Host local spool and destination implementation remain blocked until fresh independent codec correctness, test/release review, checkpoint, push, and host gitlink update are accepted.
- No host production/test file, provider, network, Docker, WSL, credential, publication, or Git mutation was performed by this harvest.

### 2026-08-31 Engine Publication Codec Verification PASS And Audit REVISE

- Independent verification **PASSED** for the frozen two-file codec candidate:
  - Focused codec selection: **10 passed**.
  - Coordinator selection: **93 passed**.
  - Formal public-contract selection: **13 passed**.
  - Additional publication selection: **79 passed**.
  - Combined focused selection: **172 passed**.
  - Distinct broader selection: **185 passed**.
  - Compile, cold-import/import-boundary, and scoped diff checks passed.
  - Candidate file hashes remained stable across independent verification.
- Independent correctness audit returned **REVISE**, which takes precedence over the green test evidence for release readiness.
- Release-blocking finding: public direct-object parsing through `_record_fields` does not yet close callback and exact-built-in-type boundaries. Caller-controlled object behavior may be invoked or accepted where detached exact public values are required.
- Related release-blocking finding: scalar validators have corresponding callback/exactness gaps at the public object boundary rather than consistently reconstructing and validating exact built-in values.
- Hostile direct-object tests are incomplete for attribute/callback mutation, substitution, exceptions, subclasses, and non-exact scalar representations.
- Public-boundary coverage does not yet prove the five codec surfaces fail closed under those hostile object behaviors while preserving stable canonical bytes and suppressing raw callback context.
- No release, commit, push, host gitlink update, or host local-publication work is permitted from the verifier PASS alone.
- Next dispatch: the original engine codec coder for bounded remediation inside the same two files, followed by fresh independent verifier and auditor reruns.
- Host local spool and destination implementation remain blocked until remediation, rerun PASS, checkpoint, push, and host gitlink release are accepted.
- No durable-memory update is warranted by this routine candidate-specific finding.

### 2026-08-31 Engine Publication Codec Remediation CODE Accepted Provisionally

- The remediation CODE handoff is accepted as a complete candidate response to the public direct-object callback/exactness findings. Fresh independent verifier and auditor reruns remain mandatory.
- Exactly three engine paths changed:
  - `synaptic-tuner/tuner/execution/coordinator_v1/publication.py`
  - `synaptic-tuner/tests/execution/coordinator_v1/test_publication.py`
  - `synaptic-tuner/tests/contract/test_public_publication_v1.py`
- `_record_fields` now accepts only an exact built-in dictionary and performs callback-safe field extraction rather than traversing caller-controlled object attributes.
- Parser-local scalar validation requires exact built-in `str` and exact built-in `int` values and rejects subclasses or callback-bearing substitutes.
- Exactness is enforced recursively across nested destination artifacts, inventories, authenticated inventory evidence, receipts, and tombstones.
- Hostile public-boundary tests cover direct-object substitution, callback invocation/mutation, exceptions, subclasses, and non-exact nested scalar representations across the five public codec surfaces.
- Focused remediation selection: **8 passed**.
- Relevant codec/publication selection: **114 passed**.
- Broader selection: **381 passed, 1 skipped, 2 failed**.
- The two broader failures remain explicitly unclassified pending independent assessment:
  - an ignored fixture `.pyc` member;
  - a Modal runtime-lock digest mismatch.
- The coder classified both as outside the remediation scope, but release readiness does not rely on that classification until the independent verifier and auditor reproduce and assess them.
- Scoped diff check passed.
- No commit or push was created.
- The engine coder is complete and retained for ownership-routed remediation if the fresh gates find another issue.
- Host local spool and destination implementation remain blocked until fresh independent test and audit PASS, resolution/classification of the two broader failures, checkpoint, push, and host gitlink release.
- Durable memory remains unchanged.

### 2026-08-31 Engine Publication Codec Remediation Audit And Verification PASS

- Fresh independent correctness audit: **PASS**.
- The audit closes the prior hostile-key callback finding: direct-object parsing no longer invokes or trusts caller-controlled key/object behavior.
- The audit closes scalar-subclass retention: recursively reconstructed codec values retain only exact built-in scalar types.
- The audit closes the missing public test-boundary finding across all five public codec surfaces.
- Audit evidence passed **18 focused** and **114 relevant** tests.
- Fresh independent verifier: **PASS**.
- The exact three-file candidate hashes remained stable throughout verification.
- Verifier evidence passed **8 focused** and **114 relevant** tests.
- Contract/broader selection: **381 passed, 1 expected skip, 2 failed**.
- Both failures were independently reproduced and classified as unrelated to the codec candidate:
  - ignored pre-existing fixture `__pycache__` residue was collected as an unexpected fixture member;
  - CRLF working-byte mismatch affected unchanged Modal lock/manifest files whose HEAD blobs remained unchanged.
- These two baseline conditions do not block the codec candidate release and must remain documented rather than silently removed or attributed to the candidate.
- Compile, cold-import/import-boundary, and scoped diff checks passed.
- The exact three-file codec candidate is **READY FOR RELEASE OPERATIONS**.
- Host local spool and destination implementation remain blocked only until the engine codec commit/push, host gitlink commit/push, and Windows/origin/canonical-WSL parity verification are accepted.
- Coder, auditor, and verifier are complete; release operations are the next dispatch.
- Durable memory remains unchanged.

### 2026-08-31 Host Publication Cleanup-Owner Reentrancy Remediation Accepted Provisionally

- Re-audit confirmed the original same-thread lease/deferred-close and generic destination-installation findings are closed, then identified one new **HIGH** blocker: the thread that owns terminal cleanup can reenter `close()` from installation or spool cleanup and wait on its own in-progress cleanup.
- Partial verifier evidence before the release gate was stopped: engine publication contract **22 passed**; focused Host **68 passed, 2 expected skips**; real Linux Docker POSIX **2 passed**. Broader/full verification was intentionally not completed after the blocker was confirmed.
- The narrow remediation changes exactly two files:
  - `synaptic_host/publication_composition.py`
  - `tests/synaptic_host/test_publication_composition.py`
- Both cleanup-claim paths now record the cleanup-owner thread identity.
- If that owner thread reenters `close()` while cleanup is in progress, it returns immediately without waiting on itself. Non-owner callers continue to wait and converge on the one cached terminal result.
- Owner identity is validated throughout cleanup and cleared only when the facade reaches `CLOSED`, including failure paths.
- Added deterministic coverage for reentrant close from destination-installation cleanup, spool cleanup, cleanup failure, and **8 concurrent non-owner waiters** converging without duplicate cleanup.
- Focused lifecycle selection: **18 passed**.
- Adjacent composition selection: **72 passed**.
- Compile and scoped diff checks passed.
- No commit or push was created. The candidate remains unreleased pending final independent hostile audit and full/broader verifier PASS.
- Durable memory remains unchanged.

### 2026-08-31 Host Local Publication Remediation CODE Accepted Provisionally

- The revised combined candidate spans exactly ten files:
  - `synaptic-tuner/synaptic_tuner/api/v1/publication.py`
  - `synaptic-tuner/tests/contract/test_public_publication_v1.py`
  - `synaptic_host/artifact_destinations.py`
  - `synaptic_host/local_artifact_destination.py`
  - `synaptic_host/publication_composition.py`
  - `synaptic_host/__init__.py`
  - `tests/synaptic_host/test_artifact_destinations.py`
  - `tests/synaptic_host/test_local_artifact_destination.py`
  - `tests/synaptic_host/test_publication_composition.py`
  - `tests/synaptic_host/test_publication_local_posix.py`
- Host `artifact_destinations` now defines the narrow generic `DestinationAdapterInstallationV1` contract.
- Local-specific installation/result/status types are removed. The local registration builder returns the generic installation with an exact boolean cleanup closure.
- Composition imports no local-adapter implementation and performs no `LocalArtifactDestinationInstallationV1` type check; any registered Host installation satisfying the generic contract may be composed.
- Facade leases are tracked per thread. Same-thread reentrant `close()` marks cleanup deferred instead of waiting on its own lease.
- Exactly one eligible external/last-release caller becomes cleanup owner; all other external callers converge on the same cached sanitized terminal result, including cached failure semantics.
- Real POSIX durable recovery regression:
  - A durable destination journal state initially classifies `FOUND`, then the stored publication state is rewritten to `INDETERMINATE`.
  - The first composition closes ambiguously with an empty spool.
  - A completely new Host composition/store/adapter/spool instance reopens the same durable roots.
  - Journal-backed lookup returns `FOUND`, reconciliation reaches `VERIFIED`, and the recovered publication verifies successfully.
  - The recovery performs zero second create calls and produces no duplicate destination artifact.
- Windows focused remediation selection: **68 passed, 2 expected skips**.
- Registry/composition selection: **52 passed**.
- Real offline Linux Docker POSIX selection: **2 passed**.
- Compile and scoped diff checks passed.
- No commit or push was created. No cloud/provider, credential, network, paid execution, or remote publication occurred.
- The ten-file candidate remains unreleased pending fresh independent security audit and full/broader verification.
- Durable memory remains unchanged.

### 2026-08-31 Host Local Publication Independent Verification PASS, Audit REVISE

- Independent verifier verdict is **PASS** on the frozen exact eight-file engine/Host candidate:
  - Engine publication contract: **22 passed**.
  - Focused Host composition: **26 passed, 1 expected skip**.
  - Real offline Linux Docker local-POSIX end-to-end: **1 passed**.
  - Adjacent Host selection: **320 passed, 13 expected skips**.
  - Full Host selection: **1,700 passed, 18 expected skips**.
  - Hashes for all eight files remained stable; the verifier made no edits.
- Independent audit verdict is **REVISE** and controls release readiness:
  1. **HIGH:** same-thread reentrant `facade.close()` waits for its own outstanding facade lease and self-deadlocks.
  2. **MEDIUM:** `registration_builders` accepts only concrete `LocalArtifactDestinationInstallationV1`, so the supposedly arbitrary-destination composition cannot install another conforming Host destination family.
- Residual verification gap: close/reopen recovery after an indeterminate publication outcome has not been proven end to end.
- Required bounded remediation:
  - Track facade leases per thread; a reentrant close from a thread holding its own lease defers cleanup instead of waiting on itself. An external close/last-release path must perform the one terminal cleanup, and all external callers converge on the same sanitized result.
  - Replace the local-specific composition type with a narrow generic Host `DestinationAdapterInstallationV1` contract implemented by `LocalArtifactDestinationInstallationV1`; retain registration-factory ownership and cleanup without changing engine contracts.
  - Add deterministic tests for same-thread reentrant close, external convergence/cleanup-once, a non-local fake installation through `registration_builders`, and close/reopen recovery after indeterminate publication.
- No engine change, release, commit, push, cloud/provider action, or remote publication is authorized until remediation and fresh independent PASS.
- Durable memory remains unchanged.

### 2026-08-31 Host Local Publication Composition CODE Accepted Provisionally

- A clean supported-engine public gap was identified: `DestinationPublicationPortV1` requires `PublicationCommandV1`, but the supported public publication submodule did not export that command type. A proposed internal Host import was rejected.
- Root added an exact two-file engine public-boundary delta:
  - `synaptic-tuner/synaptic_tuner/api/v1/publication.py`
  - `synaptic-tuner/tests/contract/test_public_publication_v1.py`
- `PublicationCommandV1` is now available from the supported publication submodule; the root `synaptic_tuner.api.v1` facade remains frozen and unchanged. Focused engine publication contract: **22 passed**.
- The Host candidate spans exactly six files:
  - `synaptic_host/local_artifact_destination.py`
  - `synaptic_host/publication_composition.py`
  - `synaptic_host/__init__.py`
  - `tests/synaptic_host/test_local_artifact_destination.py`
  - `tests/synaptic_host/test_publication_composition.py`
  - `tests/synaptic_host/test_publication_local_posix.py`
- `host.local/v1` uses `LocalFilesystemV1` per-artifact create journals as the sole durable destination-recovery truth; terminal receipt/tombstone files are absent. Lookup is closed over exact all-present/all-absent/uncertain/conflict evidence and reconstructs authenticated receipts deterministically.
- `LocalArtifactDestinationInstallationV1` owns only the registration-factory-created local adapters and their cleanup.
- Host publication composition exposes exactly `destinations()`, `publications(destination_ref)`, `publish(request)`, `verify(publication)`, and `close()` over `PublicationOperationsV1`.
- Construction requires caller-supplied absolute `destination_config_path` and `storage_config_path`, plus opaque `spool_root_ref`; SQLite remains `SqlitePublicationStoreV1.from_context` at Host `<state_root>/training.sqlite3`.
- Permit proof remains configuration/project bound: composition issues/owns only the spool-root permit, and each installation factory issues only its canonical destination data/control permits.
- Terminal composition cleanup first revokes facade work, then closes owned destination installations, cleans the spool, and closes the Host SQLite store, continuing bounded cleanup and returning only a sanitized terminal result.
- Host adapter focused selection: **16 passed**.
- Combined Windows composition selection: **24 passed**, plus the expected POSIX-only skip.
- Real offline Linux Docker local-POSIX end-to-end selection: **1 passed**, covering publish, exact readback, listing, verification, close, and reopen/recovery.
- Compile and scoped diff checks passed.
- No commit or push was created. No cloud/provider, credential, network, paid execution, or remote publication occurred.
- The combined engine/Host candidate remains unreleased pending fresh independent security audit and broader verification.
- Durable memory remains unchanged.

### Host Local Publication Simplification Accepted

- The user explicitly chose **SIMPLIFY** for Host local publication composition.
- Remove terminal receipt and tombstone files. `LocalFilesystemV1` per-artifact create journals are the sole durable destination-recovery truth; no second terminal-evidence file family is introduced.
- Recovery classification is exact and closed:
  - All required artifact journal/identity/content observations resolve exact and present -> `FOUND`.
  - All required artifacts resolve authoritatively absent -> `DEFINITELY_ABSENT`.
  - Missing, partial, unreadable, or otherwise uncertain evidence -> `INDETERMINATE`.
  - Contradictory journal, identity, content, destination, command, or inventory evidence -> `CONFLICT`.
- A successful lookup deterministically reconstructs the exact authenticated publication receipt from the canonical command, journal-backed artifact identities, bounded inventory/readback, and Host evidence authority; it does not read or create a terminal receipt file.
- Narrow `LocalArtifactDestinationInstallationV1` owns the adapters produced by its registration factory and their bounded cleanup. This adds no generic destination-registry behavior and changes no engine contract.
- Composition is an exact five-method facade over `PublicationOperationsV1`:
  - `destinations()`
  - `publications(destination_ref)`
  - `publish(request)`
  - `verify(publication)`
  - `close()`
- Construction receives explicit caller-supplied absolute `destination_config_path: Path` and `storage_config_path: Path`, plus explicit caller-supplied opaque `spool_root_ref: str`; there are intentionally no hard-coded literal configuration paths.
- Host permit issuance remains configuration/project-bound and proof-carrying. Composition itself issues and owns only the spool-root permit; each destination installation factory issues only the data/control permits named by that destination's canonical configuration.
- SQLite persistence remains exactly `SqlitePublicationStoreV1.from_context` at the Host state root `<state_root>/training.sqlite3`; the engine transaction/recovery boundary is unchanged.
- Exact six-file scope remains unchanged:
  - `synaptic_host/local_artifact_destination.py`
  - `synaptic_host/publication_composition.py`
  - `synaptic_host/__init__.py`
  - `tests/synaptic_host/test_local_artifact_destination.py`
  - `tests/synaptic_host/test_publication_composition.py`
  - `tests/synaptic_host/test_publication_local_posix.py`
- No engine source/test, engine or Host schema, checked-in destination/storage configuration, CLI, cloud, provider, credential, network, paid execution, or external publication effect is authorized by this simplification.
- Durable memory remains unchanged.

### 2026-08-31 Host Local Destination And Publication Composition Architecture Accepted

- Existing prerequisite surfaces are complete and reused unchanged: engine publication transaction/recovery, Host SQLite persistence at `<state_root>/training.sqlite3`, publication-evidence authority, verified artifact source, destination registry/configuration, storage-root capabilities and local-I/O mutation verbs, and `LocalArtifactSpoolV1`.
- The only missing Host product surfaces are a `host.local/v1` destination adapter and lifecycle/publication composition.
- Exact six-file CODE/test scope:
  - Create `synaptic_host/local_artifact_destination.py`.
  - Create `synaptic_host/publication_composition.py`.
  - Add narrow exports in `synaptic_host/__init__.py`.
  - Create `tests/synaptic_host/test_local_artifact_destination.py`.
  - Create `tests/synaptic_host/test_publication_composition.py`.
  - Create `tests/synaptic_host/test_publication_local_posix.py`.
- The `host.local/v1` adapter uses a flat, opaque, deterministic content-bound blob identity under its pre-existing destination root. Public/engine values never expose a filesystem path.
- Source bytes enter the adapter only through the spool-private bounded verified stream; the adapter receives no spool root or arbitrary path authority.
- Adapter operations cover authorization, one-shot create/publication, recovery, exact inspection, and bounded inventory/byte iteration. Evidence is returned only as authenticated engine `DestinationInventoryV1`, `AuthenticatedDestinationInventoryV1`, `AuthenticatedPublicationReceiptV1`, or `AuthenticatedPublicationTombstoneV1` values.
- Recovery lookup is closed over the existing engine outcomes `FOUND`, `DEFINITELY_ABSENT`, `INDETERMINATE`, and `CONFLICT`; contradictory identity/inventory/readback cannot be treated as success.
- The engine publication state machine, transaction/effect protocol, reconciliation semantics, and Host SQLite transaction boundary remain unchanged.
- `publication_composition.py` supplies installed-registration builders and resolves the configuration-selected destination through the registry, so the composition is arbitrary-destination rather than hardwired to local storage.
- The composition owns the Host store, selected adapter instances, spool, engine publication facade, and their bounded terminal close/cleanup lifecycle. It must close all owned components without widening engine responsibility.
- All state, artifact, control, and spool roots must already exist and resolve through Host capability configuration. Supported execution follows the released Linux trusted-controller/no-fork-active boundary.
- No engine source/test, engine or Host schema, checked-in destination/storage configuration, CLI, provider, cloud, credential, network, or paid execution change is authorized in this slice.
- CODE implementation is authorized only after the assigned coder teaches back this exact architecture and file boundary; independent audit/test remain mandatory before release or any cloud/provider use.
- Durable memory remains unchanged.

### 2026-08-31 LocalArtifactSpoolV1 Release And Host Composition Phase Opened

- Accepted `LocalArtifactSpoolV1` release commit: `c0a32cb6d9dc068735dac03c7bcd81f2f3502af5`.
- The release contains exactly three files:
  - `synaptic_host/artifact_spool.py`
  - `synaptic_host/__init__.py`
  - `tests/synaptic_host/test_artifact_spool.py`
- Windows host, origin host branch, and canonical WSL host resolve to exact commit `c0a32cb6d9dc068735dac03c7bcd81f2f3502af5`.
- Engine repository and host gitlink remain unchanged at exact engine commit `13008e7581f47c6a78d95981543a7fb6a3b62c15`.
- Repo-focused `.codex/pact` state, test residue, and unrelated canonical-WSL manifest changes remain preserved outside the release commit.
- The `LocalArtifactSpoolV1` slice is **RELEASED AND COMPLETE**.
- A new read-only PREPARE/ARCHITECT phase is open for Host-owned SQLite lifecycle/publication persistence, arbitrary destination composition, and a local end-to-end proof using the released engine evidence codecs, authority/configuration, admission, and spool components.
- No CODE implementation, cloud/provider execution, credentials, network, paid job, publication to a remote service, or destination mutation is authorized before the architecture is accepted.
- Durable memory remains unchanged.

### 2026-08-31 LocalArtifactSpoolV1 Final Audit And Test PASS

- Final independent verifier verdict is **PASS** on the exact three-file spool candidate:
  - Windows spool selection: **35 passed, 1 expected skip**.
  - Linux spool selection: **36 passed**.
  - Scoped Linux Host selection: **327 passed, 4 expected skips**.
  - Full Host selection: **1,674 passed, 17 expected skips**.
  - Stable hashes confirmed for all three candidate files; scoped diff/finality checks are clean.
- Final independent security audit verdict is **PASS**:
  - Cleanup with an active reader remains nonterminal, returns `IN_USE`, and performs zero unlink/fsync/borrow/admission/authority release effects.
  - Cleanup retries after reader count reaches zero and publishes one cached terminal result.
  - Early iterator close preserves `GeneratorExit` quietly while releasing reader ownership exactly once.
  - Concurrent terminal-failure callers converge on one cleanup/release chain and the same sanitized cached result.
  - Startup validation/reclamation, finish durability ordering, bounded EOF/read verification, identity checks, and Host/engine/destination boundaries are accepted.
- Remaining checked-in test coverage gaps are classified nonblocking for this slice and do not represent an open product or security finding.
- No release blocker remains. The exact three-file `LocalArtifactSpoolV1` slice is **RELEASE-READY** for scoped commit, push, and Windows/origin/WSL parity verification.
- Durable memory remains unchanged.

### 2026-08-31 LocalArtifactSpoolV1 CODE Accepted Provisionally, Audit HALT

- The provisional spool implementation spans exactly three files:
  - `synaptic_host/artifact_spool.py`
  - `synaptic_host/__init__.py`
  - `tests/synaptic_host/test_artifact_spool.py`
- Verification evidence: full Host **1,649 passed, 17 expected skips**; Linux Host selection **302 passed, 4 expected skips**.
- Audit accepts the Host/engine/destination trust boundaries, admission-before-startup ownership, bounded two-phase validation/reclamation, finish durability sequence, flat-name/reference grammar, and strong identity/digest/reader enforcement.
- Audit verdict is **HALT** on two blockers:
  1. **HIGH:** cleanup while a reader is active caches a terminal failure and releases borrow/admission/authority ownership, so cleanup cannot safely retry after the reader exits.
  2. **MEDIUM:** early generator termination converts `GeneratorExit` into `IO_FAILED` instead of preserving generator-close semantics.
- Required cleanup correction: active-reader cleanup remains nonterminal in `CLOSING`, returns a closed `IN_USE` result, performs zero unlink/fsync/borrow/admission/authority release, and permits retry after reader count reaches zero. Only the successful/final retry may publish and cache `CLEANED` or `CLEANED_WITH_FAILURES`.
- `iter_finished` must preserve `GeneratorExit` while still decrementing reader ownership exactly once.
- Missing ordinary regression matrix that must be added before release:
  - Active-reader cleanup/zero-effect retry and early `generator.close()`.
  - Startup 4,097-entry overflow; unexpected list/stat value types; first-pass/second-pass identity drift with zero deletion.
  - Short write and write-failure ownership/cleanup.
  - Finish failures at file fsync, descriptor stat, close, path stat, and root fsync, proving exact ordering and state.
  - Read truncation/extension plus descriptor, path, read, and close failures.
  - Concurrent reader/release/cleanup behavior.
  - Factory rollback at every authority/admission/borrow/root acquisition stage.
  - Multi-failure cleanup that continues and preserves exact release order: borrow, then admission, then authority.
- No commit, push, release, DB, provider, cloud, destination-adapter, or engine work is authorized. Fresh remediation, verifier, and security audit PASS are required.
- Durable memory remains unchanged.

### 2026-08-31 LocalArtifactSpoolV1 Architecture Accepted

- No engine prerequisite or engine modification is required. This is a Host-owned ephemeral staging component.
- Exact production/test scope:
  - Create `synaptic_host/artifact_spool.py`.
  - Add narrow exports only in `synaptic_host/__init__.py`.
  - Create `tests/synaptic_host/test_artifact_spool.py`.
  - Add only the minimum existing Host boundary assertion if one is required; no other file is authorized by default.
- `LocalArtifactSpoolV1` exclusively owns the dedicated single-root authority, live admission, publication-spool borrow, and root capability for its lifetime.
- On-disk members use exact flat filename grammar `^synaptic-spool-v1-[0-9a-f]{64}\.blob$`; the separately opaque public/private handle is `local-spool-v1:<64hex>`. Both identities derive from CSPRNG material and are not paths.
- Startup acquires admission before examining the root and performs a bounded maximum **4,096-entry** two-phase pass: first snapshot and validate the complete flat root without mutation; only after all entries pass the closed grammar/type/link/containment checks may the second phase reclaim eligible stale spool entries. Any invalid/unrelated member fails before partial reclamation.
- A live sink is bound by strong exact-object identity, canonical spool/ref/content digest state, writer state, and authenticated root/file identity.
- Finish durability order is exact: transition to `FINISHING`; fsync file; descriptor-stat and require regular file, link count 1, exact size, and retained inode identity; close descriptor; path-stat and require the exact same identity; fsync directory; atomically publish finished state, remove live state, and return the opaque reference.
- Destination consumption is private and capability-bound: `iter_finished(ref, exact VerifiedArtifact)` yields only bounded verified bytes while reader counts are held; release is separately explicit. Destinations receive no filesystem path, raw root authority, or post-cleanup read surface.
- The trusted Host controller owns the spool and must not fork while the spool/admission is active or closing; workers use spawn/exec/separate provider processes.
- Cleanup lifecycle is exactly `OPEN -> CLOSING -> CLEANED | CLEANED_WITH_FAILURES`.
- Cleanup order is exact: revoke new operations; wait for bounded active operations; close live writers/readers; unlink only exact owned live and finished members; fsync the root; release borrow; release admission; release authority; cache and return a sanitized terminal result. Repeated cleanup returns the cached result with no effect.
- Host durable DB/state, destination-adapter implementation, provider/cloud behavior, engine code, and configuration remain unchanged and outside this slice.
- Stop and return to architecture if any requirement needs restart reference reconstruction, destination reads after spool close, unrelated/shared root members, more than 4,096 entries, fork or inherited-controller use, unreliable directory flock, engine-side cleanup, a durable spool reference, or DB/provider behavior.
- CODE implementation is authorized only after the assigned coder teaches back this exact scope, lifecycle, and stop boundary.
- Durable memory remains unchanged.

### 2026-08-31 docker_v1 Release Checkpoint And LocalArtifactSpoolV1 Resume

- Accepted `docker_v1` concurrent-close release commit: `61c3df294e432633dc60c6e94b79331fa970b1a2`.
- The release contains exactly two files:
  - `synaptic_host/docker_v1/facade.py`
  - `tests/synaptic_host/docker_v1/test_facade.py`
- Windows host, origin host branch, and canonical WSL host resolve to exact commit `61c3df294e432633dc60c6e94b79331fa970b1a2`.
- Engine repository and host gitlink remain unchanged at exact engine commit `13008e7581f47c6a78d95981543a7fb6a3b62c15`.
- Repo-focused `.codex/pact` state, test residue, and the unrelated canonical-WSL manifest changes remain preserved outside the release commit.
- The full Host gate is restored: **1,639 passed, 16 expected skips**.
- The `docker_v1` concurrent-close repair is **RELEASED AND COMPLETE** with no remaining blocker.
- Parent `LocalArtifactSpoolV1` work may now resume at a fresh read-only architecture refresh against the released simplified trusted-controller admission contract.
- No Host DB, destination adapter, provider, cloud, publication mutation, or spool CODE work is authorized before that refreshed architecture is accepted.
- Durable memory remains unchanged.

### 2026-08-31 docker_v1 Concurrent-Close Final Audit And Test PASS

- Final independent security audit verdict is **PASS**. The reentrant registry guard/depth, exact weak-reference removal/queueing, outermost post-unlock single-drainer ownership, atomic empty/release handoff, reentrant orphan cleanup, and preserved close lifecycle semantics are accepted with no finding.
- Final independent verifier verdict is **PASS**:
  - Repeated deterministic/stress selection: **60/60 passed**.
  - Facade plus capability selection: **94 passed**.
  - Full Host selection: **1,639 passed, 16 expected skips** in **22 seconds**, with no stall or deadlock.
  - Stable hashes confirmed for the exact two candidate files.
  - Compile, cold-import/import, scoped diff, and finality checks were clean.
- No release blocker remains. The exact two-file `docker_v1` concurrent-close repair is **RELEASE-READY** for scoped commit, push, and Windows/origin/WSL parity verification.
- Durable memory remains unchanged.

### 2026-08-31 docker_v1 Concurrent-Close CODE Accepted Provisionally

- The bounded deadlock correction is accepted provisionally across exactly two files:
  - `synaptic_host/docker_v1/facade.py`
  - `tests/synaptic_host/docker_v1/test_facade.py`
- Registry access now uses one concrete `RLock`-backed guard with explicit per-thread nesting depth.
- Weak-reference callbacks only exact-remove their still-current record or enqueue an orphan; they perform no cleanup while the registry guard is held.
- Only the outermost post-unlock path attempts a nonblocking single-drainer claim. Exactly one drainer performs orphan cleanup, including reentrant cleanup that constructs or closes another facade.
- Queue-empty observation and drainer-claim release are atomic, preventing an orphan enqueue from being lost between the final empty check and drainer release.
- A `contextlib` generator/contextmanager guard was deliberately avoided because generator teardown can mutate traceback state on sealed exception objects; the concrete guard preserves sealed exception identity/state.
- Existing close ownership, final lease, cleanup-once, terminal convergence, reentry, and failure-cache lifecycle semantics remain unchanged.
- Deterministic/stress selection: **80/80 passed**.
- Full facade selection: **76 passed**.
- Capability coverage: **18 passed**.
- Full Host selection: **1,639 passed, 16 expected skips**.
- Compile and scoped diff checks passed.
- No commit or push was created.
- The candidate remains unreleased pending fresh independent security audit and verifier PASS.
- Durable memory remains unchanged.

### 2026-08-31 docker_v1 Concurrent-Close PREPARE And Architecture Accepted

- Reproduction evidence: the isolated concurrent-close node passed twice and the full facade selection completed **70 passed**; the deadlock is schedule-dependent and appears only under the broader full-suite execution schedule.
- Root cause: a synchronous weak-reference callback can run during `state_for` registry allocation/garbage collection and reenter the non-reentrant registry lock. The owning thread self-deadlocks while other closer threads block at `facade.py:392`.
- The close ownership, final-lease, cleanup-once, terminal convergence, and failure-cache state machine is otherwise sound and must remain behaviorally unchanged.
- Exact minimal CODE scope is two files:
  - `synaptic_host/docker_v1/facade.py`
  - `tests/synaptic_host/docker_v1/test_facade.py`
- Centralize registry access behind one reentrant registry guard with explicit nesting depth.
- A weak-reference callback may only exact-remove its own still-current record or enqueue its orphan; it performs no cleanup, close, condition wait/notification, nested facade work, or user callback while the registry guard is held.
- Only the outermost guard exit, after unlocking, may invoke a single orphan drainer. The drainer performs cleanup outside the registry lock and safely handles cleanup that constructs or closes a nested facade.
- No cleanup action or condition wait/notification may execute while the registry lock is retained. The facade lifecycle and public error/state contracts remain unchanged.
- Exact deterministic regression matrix:
  1. Force GC/drop of the last unrelated facade reference inside outer and nested registry guards; the weak callback returns, and cleanup begins only after the outermost exit.
  2. Orphan cleanup constructs or closes a nested facade while proving no registry lock is retained.
  3. Run concurrent closers while unrelated facades repeatedly collect; exactly one cleanup occurs and all closers observe the identical terminal result.
  4. Nested registry lookup plus collection completes without self-deadlock.
  5. Queue multiple weak callbacks inside one outer registry section; each orphan cleans exactly once.
  6. A stale weak reference or Python object-ID reuse cannot remove a newer registry record.
- Retain existing close-ownership, final-lease, reentry, cleanup-once, terminal convergence, and failure-cache tests.
- Required gates are the exact deterministic matrix, full facade selection, repeated schedule stress, and the full Host suite with no timeout/deadlock.
- No admission, publication-spool, provider, engine, compatibility, or unrelated lifecycle change is authorized.
- Durable memory remains unchanged.

### 2026-08-31 Simplified Admission Release Checkpoint And docker_v1 Recovery Opened

- Accepted simplified trusted-controller admission release commit: `d7affa1331d1207ff0d38bdd3bd3a52f296f1bcf`.
- The release commit contains exactly eight paths:
  - `synaptic_host/local_io_v1/model.py`
  - `synaptic_host/local_io_v1/posix.py`
  - `synaptic_host/local_io_v1/filesystem.py`
  - `tests/synaptic_host/local_io_v1/conftest.py`
  - `tests/synaptic_host/local_io_v1/test_boundaries.py`
  - `tests/synaptic_host/local_io_v1/test_filesystem.py`
  - `tests/synaptic_host/local_io_v1/test_posix_spool_admission.py`
  - repository-root `AGENTS.md`
- Windows host, origin host branch, and canonical WSL host resolve to exact commit `d7affa1331d1207ff0d38bdd3bd3a52f296f1bcf`.
- Engine repository and host gitlink remain unchanged at exact engine commit `13008e7581f47c6a78d95981543a7fb6a3b62c15`.
- Repo-focused `.codex/pact` edits and test residue remain preserved outside the release commit.
- The two unrelated canonical-WSL manifest type changes remain preserved and untouched:
  - `gemma4-e4b/eval_pool_manifest.json`
  - `gemma4-e4b/split_manifest.json`
- The simplified admission slice is **RELEASED AND COMPLETE**.
- The separately user-approved `docker_v1` full-Host restoration slice is now open, scoped to the reproducible concurrent-close deadlock around `facade.py` `state_for` and `test_concurrent_closers_converge_and_cleanup_once`.
- Next dispatch is read-only PREPARE followed by ARCHITECTURE; no CODE remediation is authorized until those handoffs are accepted.
- Publication-spool implementation remains blocked until the `docker_v1` repair independently restores the full Host gate.
- Durable memory remains unchanged.

### 2026-08-31 Simplified Trusted-Controller Admission Final PASS

- Final cooperative security audit verdict is **PASS**. The capability canonicalization defect is fixed; no admission finding remains open.
- Auditor evidence: Linux focused selection **199 passed**; Windows focused selection **190 passed, 9 expected skips**; the exact real-Linux high-level capability tuple and its canonical digest were verified.
- Final independent verifier verdict is **PASS**:
  - Windows local-I/O plus bundle: **282 passed, 13 expected skips**.
  - Linux local-I/O plus bundle: **291 passed, 4 expected skips**.
  - Exact admission selection: **9/9**.
  - Stable hashes confirmed for all exact eight candidate files.
  - Compile, import, scoped diff, and whitespace checks were clean.
  - Canonical WSL state remained unchanged.
- No remaining simplified-admission product, security, resource-lifecycle, or boundary defect is known.
- The exact eight-file simplified trusted-controller admission slice is **RELEASE-READY** for scoped commit, push, and Windows/origin/WSL parity verification.
- The unrelated `docker_v1` concurrent-close/full-Host restoration remains a separate blocked slice and may begin only after this admission release checkpoint completes.
- Durable memory remains unchanged.

### 2026-08-31 Simplified Admission Verification PASS, Audit HALT On Capability Canonicalization

- Independent verifier verdict is **PASS** on the exact eight-file simplified candidate: Windows local-I/O plus bundle completed **282 passed, 12 expected skips**; Linux completed **290 passed, 4 expected skips**; exact inventory verification is **8/8**.
- Cooperative-boundary audit closes all admission exclusivity, process/resource lifecycle, one-close release, PID/fork boundary, trusted-object, capability-predicate, and Host/engine ownership concerns except one novel finding.
- One **HIGH** canonicalization defect blocks release: filesystem capability construction appends admission capability names after the existing base features, but the capability DTO requires one globally sorted tuple. The resulting noncanonical tuple makes the real-Linux high-level capability report unavailable.
- Minimal bounded remediation:
  - Sort the complete combined capability tuple globally before capability digest computation and DTO construction.
  - Add a real-Linux regression that exercises the high-level `LocalFilesystem` capability and proves the exact admission capabilities are available/canonical.
- No other product or security defect remains open from this audit.
- No broader CODE, release, commit, push, spool-facade continuation, provider work, or `docker_v1` repair is authorized until the narrow correction receives fresh verifier/audit PASS.
- Durable memory remains unchanged.

### 2026-08-31 Simplified Trusted-Controller Admission CODE Accepted Provisionally

- The simplified admission implementation is accepted provisionally across exactly eight files:
  - `synaptic_host/local_io_v1/model.py`
  - `synaptic_host/local_io_v1/posix.py`
  - `synaptic_host/local_io_v1/filesystem.py`
  - `tests/synaptic_host/local_io_v1/conftest.py`
  - `tests/synaptic_host/local_io_v1/test_boundaries.py`
  - `tests/synaptic_host/local_io_v1/test_filesystem.py`
  - `tests/synaptic_host/local_io_v1/test_posix_spool_admission.py`
  - repository-root `AGENTS.md`
- The Host retains strong references to exact live authority/admission/lease/borrow objects in one process-local mutex-protected registry.
- Linux admission opens a fresh directory file description, acquires nonblocking directory flock, and validates the exact retained root device/inode/type identity.
- Release transitions once, performs exactly one close with no retry, publishes the closed success/failure code, removes live records, and completes owned cleanup.
- Fork-child behavior is limited to best-effort cleanup while idle plus permanent PID/process-instance invalidation; fork while admission is active or releasing is outside the supported contract.
- Publication effects reauthenticate the exact live admission and root path/identity before mutation.
- Exact capabilities are `directory-inode-admission`, `nonblocking-directory-flock`, `crash-released-admission`, and `exec-closed-admission`.
- Repository-root `AGENTS.md` now records the trusted-controller boundary, no fork during active/releasing admission, spawn/exec or separate-provider workers, Host-owned filesystem/DB/destinations, and engine provider/filesystem/persistence agnosticism.
- Removed strict-hostile-runtime surfaces include the mutable/fixed lock-file lifecycle, fork/close gate, frozen release claims, adversarial issuance seals, quarantine maps, follower events/waits/cached outcomes, compatibility paths, and indeterminate-release machinery.
- Windows focused selection: **190 passed, 8 expected skips**.
- Windows local-I/O plus bundle selection: **282 passed, 12 expected skips**.
- Linux admission selection: **8 passed**.
- Linux local-I/O plus bundle selection: **290 passed, 4 expected skips**.
- Compile and scoped diff checks passed.
- No commit, push, publication spool facade, provider integration, engine change, Host DB implementation, or `docker_v1` change was made.
- The candidate is not release-ready; fresh independent verifier and security audit PASS remain mandatory.
- Durable memory remains unchanged.

### 2026-08-31 Simplified Trusted-Controller Admission Architecture Accepted

- The trusted Host controller is the sole owner of local publication-spool admission. Fork is prohibited while an admission is `ACTIVE` or `RELEASING`; worker execution uses spawn, exec, or a separate provider process.
- The supported platform contract is Linux/POSIX directory-inode flock. OS descriptor teardown releases admission on process crash, and close-on-exec releases it across exec.
- Admission uses simple strong references to the exact issued authority/admission/lease records under one process-local mutex; it does not defend against hostile same-process mutation outside the trusted-controller contract.
- Lifecycle is exactly `ACTIVE -> RELEASING -> RELEASED | RELEASED_WITH_FAILURE`.
- Release performs exactly one close and never retries. Concurrent or replayed release is invalid rather than a follower/wait/replay surface.
- Fork-child behavior is limited to best-effort descriptor cleanup and permanent PID/process-instance invalidation of inherited objects; the child cannot use inherited admission APIs.
- Exact capability names are `directory-inode-admission`, `nonblocking-directory-flock`, `crash-released-admission`, and `exec-closed-admission`.
- Delete the abandoned strict-hostile-runtime machinery: private fork/close gate, frozen release claims, canonical issuance seals/digests used for adversarial DTO defense, root quarantine maps, follower events/waits/cached outcomes, post-callback mutation probes, and related compatibility surfaces.
- Ownership boundary remains submodule-first: the consuming Host project owns filesystem capabilities, durable DB/state, credentials, destination adapters, and publication roots; the engine remains provider/filesystem/persistence agnostic.
- Authorized CODE scope is exactly eight paths:
  - `synaptic_host/local_io_v1/model.py`
  - `synaptic_host/local_io_v1/posix.py`
  - `synaptic_host/local_io_v1/filesystem.py`
  - `tests/synaptic_host/local_io_v1/conftest.py`
  - `tests/synaptic_host/local_io_v1/test_boundaries.py`
  - `tests/synaptic_host/local_io_v1/test_filesystem.py`
  - `tests/synaptic_host/local_io_v1/test_posix_spool_admission.py`
  - repository-root `AGENTS.md`
- `AGENTS.md` must state the trusted-controller/no-fork-active operational boundary. No engine skill, engine source, or engine test change is authorized.
- Add no compatibility layer, alias, migration adapter, or retained strict-surface fallback.
- Implementation against this exact scope is now authorized. Release remains blocked pending fresh independent verifier and security audit PASS.
- Durable memory remains unchanged.

### 2026-08-31 User Decision: SIMPLIFY Admission Trust Boundary

- The user explicitly chose **SIMPLIFY** instead of continuing strict hostile-runtime, adversarial same-process hardening.
- New governing trust boundary: a trusted Host controller exclusively owns spool admission and its exact issued objects.
- Fork is prohibited while a spool admission is `ACTIVE` or `RELEASING`. Worker execution must use spawn, exec, or a separate provider process rather than fork from the owning controller during that interval.
- Retained guarantees are independent-process directory-inode flock contention, OS/crash lock release, root identity/path reauthentication, and strong references to the exact issued authority/admission/lease/borrow objects.
- Remove the private fork/close gate, adversarial callback/DTO mutation machinery, and asynchronous-exception hardening from the target design and implementation.
- Add no compatibility layer, alias, adapter, or fallback for the abandoned strict-hardening surface.
- A fresh read-only architecture handoff must freeze the simplified contracts, removals, tests, and migration of the current unreleased candidate before any CODE work resumes.
- No admission implementation, release, commit, push, or parent spool-facade work is authorized yet.
- The unrelated `docker_v1` concurrent-close deadlock repair remains a separate second slice and may begin only after the simplified admission slice receives independent PASS and release clearance.
- Durable memory remains unchanged.

### 2026-08-31 Final Admission Hostile Audit HALT And Architecture Choice Required

- Requested prior hostile reproductions are independently **CLOSED**: post-claim public DTO mutation cannot alter terminal identity, and clean/ambiguous descriptor reuse plus fork cannot close the reused unrelated descriptor.
- Independent verifier evidence remains green: **287 passed, 23 expected skips**, plus **19 Linux passed**.
- Audit verdict is **HALT** on two findings:
  1. **HIGH — repeated sealed-issuance invariant:** active and release records retain only `id(lease)`, not a strong reference to the issued lease object. Deterministic CPython object-ID reuse can make an equal forged DTO appear to have the same issuance identity and allow release of the genuine descriptor.
  2. **MEDIUM — gate acquire-then-raise closure:** if private gate acquisition succeeds and the acquisition wrapper then raises, both acquire and release paths can leave the non-reentrant gate permanently locked. A terminal result may be signaled, but later admission acquisition or fork can deadlock.
- If the strict adversarial in-process threat model continues, required remediation is frozen to:
  - Retain the original lease object strongly across active, release-claim, and terminal state, and compare issuance identity with `is`.
  - Never use that strong reference for registry keys, seals, terminal keys, or post-claim DTO field reads.
  - Make gate acquisition owner-aware and cleanup-safe when an exception occurs after acquisition.
  - Add exact acquire-then-raise regressions for admission acquire and release, proving gate recovery and subsequent acquire/fork progress.
- The further-recurrence user-decision gate is **ACTIVE**. No additional code, release, commit, push, parent spool work, or separate `docker_v1` repair may proceed without explicit direction.
- Architectural alternative for user decision: narrow the cooperative boundary to trusted internal DTOs, prohibit fork while a spool owner is active, and simplify admission instead of continuing adversarial same-process DTO/fork hardening.
- Durable memory remains unchanged.

### 2026-08-31 Frozen-Claim Release/Fork Gate CODE Accepted Provisionally

- The bounded release/fork implementation is accepted provisionally across exactly two files:
  - `synaptic_host/local_io_v1/posix.py`
  - `tests/synaptic_host/local_io_v1/test_posix_spool_admission.py`
- Active issuance and release now operate from frozen primitive claims; terminal finalization performs no post-claim reread of public lease, nested-root, or directory DTOs.
- Close candidates are immutable sealed snapshots captured before the raw close effect.
- At-fork handling snapshots proven pre-close candidates before fork; the parent restores gate ownership/state, while the child closes only those candidates without an inherited mutex and installs fresh fork-invalid registry state.
- A private fork/close gate remains held from close admission through immutable terminal publication and follower signaling.
- On ambiguous close, the descriptor is forgotten and the authenticated root is quarantined before the gate is released.
- Unsupported same-thread reentrant fork from an active raw-effect callback is cooperatively rejected; ordinary cross-thread fork remains serialized and supported.
- New hostile regressions prove post-claim DTO mutation cannot alter the terminal key/outcome/event, fork-winning-before-close cleanup, fork waiting through terminal publication, and immediate descriptor reuse after both clean and ambiguous close without closing the reused descriptor.
- Linux release/fork selection: **19 passed**.
- Focused boundary selection: **7 passed**.
- Scoped diff check passed.
- No broader local-I/O, publication spool, provider, `docker_v1`, compatibility, commit, push, or release change was made.
- The candidate remains unreleased pending fresh independent hostile audit and verifier PASS.
- Durable memory remains unchanged.

### 2026-08-31 Directory Admission Release/Fork Micro-Architecture Accepted

- The accepted minimal contract freezes a private primitive release claim before close. Terminal finalization uses only that claim and must not reread public lease, nested root, or directory DTOs after claim creation.
- A private non-reentrant fork/close gate serializes ordinary cross-thread fork with close admission, the raw close effect, immutable terminal publication, and follower signaling.
- Registered at-fork handling uses explicit before/parent/child phases. The child acquires no inherited mutex, closes only descriptors proven to be genuine pre-close admission candidates, installs fresh child-local registry/gate state, and marks all inherited public/live objects fork-invalid.
- If close is ambiguous, the parent forgets the descriptor and irreversibly quarantines the authenticated root before publishing/signaling the terminal result.
- Ordinary fork initiated by another thread remains supported and waits on the private gate where required.
- Explicit unsupported boundary: same-thread reentrant fork from a raw effect callback or signal handler. This slice adds no `pthread_sigmask`, Linux-only public error/API, or filesystem surface expansion.
- Exact hostile-test matrix:
  1. Mutate or replace the public lease, nested root, and directory DTOs after claim; the terminal key, outcome, and event must remain unchanged.
  2. Let fork win the gate before close; the child closes the genuine inherited admission descriptor and rejects all inherited admission APIs.
  3. Fork from another thread after the close effect begins; fork waits through terminal publication and preserves an immediately reused unrelated descriptor.
  4. Ambiguous close plus descriptor reuse plus fork never permits child cleanup to close the reused descriptor.
  5. Every injected post-claim exception publishes a closed terminal/quarantine result and signals all followers.
  6. Retain regressions for clean and ambiguous two-release concurrency, bounded follower timeout, acquire-during-release zero-effect behavior, direct `FD_CLOEXEC`/`posix_spawn`, and fork/PID/quarantine/errno/capability contracts.
- No CODE remediation, release, commit, push, spool-facade continuation, or `docker_v1` slice is authorized until implementation is separately dispatched against this exact contract.
- Durable memory remains unchanged.

### 2026-08-31 Final Directory-Admission Audit HALT: Release/Fork Micro-Architecture Required

- Concurrent normal-release and ambiguous-release regressions pass. Independent verifier evidence is **287 passed, 19 expected skips**, and the Linux admission selection is **15 passed**.
- Audit verdict is **HALT** on two novel findings:
  1. **HIGH:** the owner closes outside the lock while the stale file descriptor remains recorded in the active registry. If the descriptor number is reused, a later fork-child cleanup can close an unrelated inherited descriptor. A deterministic Docker reproduction yields `EBADF`.
  2. **MEDIUM:** terminal finalization rereads mutable public lease/directory DTOs instead of a sealed claim snapshot. Hostile `lease_ref` mutation can strand `ACTIVE`/`RELEASING` state and its event while publishing or looking up the terminal outcome under the wrong key.
- No further CODE remediation is authorized directly from this finding. A bounded read-only micro-architecture decision is required first.
- The micro-architecture must define immutable, sealed release-claim snapshots captured before close, safe serialization between fork and close/descriptor retirement, and child cleanup that does not acquire or depend on an inherited mutex.
- No admission release, commit, push, parent spool-facade continuation, or separate `docker_v1` deadlock slice may proceed until that architecture is accepted and then independently implemented/audited.
- Durable memory remains unchanged.

### 2026-08-31 Linearizable Directory-Admission Release CODE Accepted Provisionally

- The bounded release correction is accepted provisionally across exactly two files:
  - `synaptic_host/local_io_v1/posix.py`
  - `tests/synaptic_host/local_io_v1/test_posix_spool_admission.py`
- Release now atomically transitions the live admission from `ACTIVE` to `RELEASING` while creating a sealed root-level releasing claim.
- Exactly one claim owner performs the underlying close outside the registry mutex; no follower can close the descriptor.
- Followers wait for a bounded interval on the in-flight release and receive only the published terminal result.
- Clean release or ambiguous release is atomically committed to the immutable terminal root/code snapshot before followers are awakened.
- Root quarantine/acquisition fencing remains checked before open/flock and again before admission issuance, including while a root has an active releasing claim.
- The obsolete lease-keyed quarantine path is removed; terminal authority is root-node keyed and cannot be bypassed through a reconstructed lease.
- Linux release/admission selection: **15 passed**.
- Focused boundary selection: **7 passed**.
- Scoped diff check passed.
- No broader local-I/O, publication spool, provider, `docker_v1`, compatibility, commit, push, or release change was made.
- The candidate remains unreleased pending fresh final independent hostile audit and verifier PASS.
- Durable memory remains unchanged.

### 2026-08-31 Surgical Admission Re-Audit HALT: Linearizable Release Required

- Independent verifier verdict remains **PASS** on stable candidate hashes: local-I/O plus bundle completed **287 passed, 16 expected skips**, and the Linux admission selection completed **12 passed**.
- Independent audit confirms all prior **HIGH** admission findings are closed, including raw root quarantine/exclusivity, and the direct `FD_CLOEXEC` concern is closed.
- One novel **MEDIUM** concurrency defect remains: release quarantine lookup, live-admission validation, and terminal result population occur across separate lock regions.
- A deterministic synchronized two-thread reproduction yields one raw `KeyError` and one closed indeterminate error. Exactly one underlying close occurs and the authenticated root fence remains intact.
- This defect is therefore **not a recurrence of the admission exclusivity/root-quarantine invariant** and does not trigger another user-decision cycle.
- Bounded remediation remains authorized within the existing user-approved surgical slice:
  - Make release use one atomic, linearizable claim/state transition.
  - Permit exactly one underlying close.
  - Make every follower return only the same closed, cached outcome; no raw exception may escape.
  - Add deterministic synchronized regressions for both successful close and close ambiguity.
- No broader local-I/O, spool-facade, provider, `docker_v1`, compatibility, commit, push, or release work is authorized yet.
- The candidate remains halted pending the bounded correction and fresh independent audit/verifier PASS.
- Durable memory remains unchanged.

### 2026-08-31 Final Surgical Raw Root-Quarantine CODE Accepted Provisionally

- The user-approved final surgical admission correction is accepted provisionally across exactly two files:
  - `synaptic_host/local_io_v1/posix.py`
  - `tests/synaptic_host/local_io_v1/test_posix_spool_admission.py`
- Raw root-node quarantine is irreversible and sealed within the immutable port/process identity; callers cannot clear, replace, or transfer it through reconstructed values.
- Acquisition-rollback close ambiguity and release close ambiguity both populate the root-node quarantine.
- The exact authenticated root node is checked against quarantine before open/flock and checked again before a new admission is published.
- Quarantine lookup, acquisition, issuance, rollback, and release transitions are serialized so no concurrent issuance can cross a quarantine transition.
- Root aliases are fenced by authenticated node identity, and reconstructed admission/lease DTOs cannot bypass the live sealed quarantine state.
- Repeated operations on a quarantined root return the cached closed result with zero open, flock, issuance, or other provider effect.
- Checked-in coverage directly proves `FD_CLOEXEC` and uses isolated `posix_spawn` execution rather than relying only on the at-fork close hook.
- Linux admission selection: **12 passed**.
- Focused boundary selection: **7 passed**.
- Scoped diff check passed.
- No `docker_v1` implementation, spool facade, provider integration, model change, commit, or push was made.
- The candidate remains unreleased pending fresh independent hostile audit and verifier PASS.
- Durable memory remains unchanged.

### 2026-08-31 User APPROVED Sequential Admission And docker_v1 Recovery Slices

- The user explicitly **APPROVED** two strictly sequential, non-overlapping remediation slices.
- **Slice 1 — final surgical raw admission correction:**
  - Add irreversible raw quarantine keyed to the authenticated root-node identity.
  - Consult that root quarantine before open/flock and again before issuing an admission.
  - Apply the same fence to acquisition rollback ambiguity and release/close ambiguity.
  - Add hostile zero-effect, close-after-effect, and reacquisition tests proving no new raw admission can issue for a quarantined root.
  - Add direct `FD_CLOEXEC` proof rather than relying on the at-fork hook closing before exec.
  - Require fresh focused verification, hostile security re-audit, and an admission release gate.
  - This slice authorizes no publication spool facade, provider integration, compatibility work, commit, push, release, or `docker_v1` edit.
- **Slice 2 — unrelated full-Host restoration:** only after Slice 1 receives independent PASS and release clearance, separately repair the reproducible `docker_v1` facade concurrent-close deadlock and rerun the full Host gate.
- The two scopes must remain disjoint. The `docker_v1` repair is blocked until the admission correction has passed its independent gates; admission work must not absorb the unrelated deadlock repair.
- Durable memory remains unchanged.

### 2026-08-31 Cycle-3 Admission TEST/AUDIT HALT: Raw Root Quarantine Recurrence

- Candidate-owned verification is green: local-I/O plus bundle completed **287 passed, 13 expected skips**; real-process Linux Docker completed **9 passed**; compile, import, scoped diff, and stable seven-file hash checks passed.
- The full Host gate **HALT** also reproduced an unrelated existing `docker_v1` facade concurrent-close deadlock at `facade.py:392` / `test_facade.py:337`; thread stacks were captured. This failure is outside the admission candidate and is not reclassified as an admission defect.
- Independent admission audit closes the original pathname-replacement overlap, fork defect, post-effect/custom-close defect, high-level quarantine fence, contention-errno mapping, and capability-detection findings.
- One **HIGH** release blocker remains and repeats the prior raw-quarantine invariant: POSIX quarantine is keyed only by lease identity; acquisition does not consult quarantine bound to the root; after a close-after-effect error, a new raw admission can be issued for that same root.
- Required bounded remediation is an irreversible, authenticated root-node quarantine checked before open/flock and again before issuance. It must cover acquisition rollback and release uncertainty, and add a hostile raw close-after-effect test proving that no new admission can issue.
- **LOW:** current `CLOEXEC` testing is indirect because the at-fork hook closes the inherited descriptor before exec. Add direct `FD_CLOEXEC` verification or a separately isolated exec path.
- Because the same raw-quarantine invariant recurred after the user-approved cycle-three remediation, the further-recurrence user-decision gate remains **ACTIVE**. No additional remediation may begin without a new explicit user decision.
- No audit edits, release, commit, push, or parent spool-facade work is authorized.
- Durable memory remains unchanged.

### 2026-08-31 User-Approved Cycle-3 Directory Admission CODE Accepted Provisionally

- The bounded cycle-three admission-only implementation is accepted provisionally across exactly seven files:
  - `synaptic_host/local_io_v1/model.py`
  - `synaptic_host/local_io_v1/filesystem.py`
  - `synaptic_host/local_io_v1/posix.py`
  - `tests/synaptic_host/local_io_v1/conftest.py`
  - `tests/synaptic_host/local_io_v1/test_boundaries.py`
  - `tests/synaptic_host/local_io_v1/test_filesystem.py`
  - `tests/synaptic_host/local_io_v1/test_posix_spool_admission.py`
- Authority, admission, retained lease, and borrow values capture immutable construction/process identity. A fork child permanently invalidates every inherited live object.
- All affected port and filesystem entrypoints apply pre-state fork/process guards before inherited descriptor, mutex, registry, open, flock, or other live-object interaction.
- Borrow effects, callbacks, and custom-close paths now perform post-effect validation of the admission seal, retained root identity, and reauthenticated root path before reporting success.
- Quarantine is terminal at both layers: a quarantined high-level authority/admission cannot reacquire or issue admission, and a quarantined raw retained-directory lease cannot validate, act, or return to active state.
- Exact capability names remain `directory-inode-admission`, `nonblocking-root-admission`, and `fork-revoked-admission`; detection requires the complete accepted native-POSIX `fcntl`/`os`, flag, directory-FD, retained-directory, and at-fork predicate set and otherwise fails closed.
- Only `EAGAIN` and `EWOULDBLOCK`, and only when raised by the `flock` call site, map to `ROOT_IN_USE`. Other access and I/O failures retain their closed error classification.
- Checked-in regressions cover exec/`CLOEXEC`, permanent fork invalidation before state access, hostile callback/effect/custom-close mutation, terminal high-level/raw quarantine, capability predicate removal, and exact contention mapping.
- Focused admission selection: **195 passed**.
- Real-process Docker/Linux selection: **9 passed**.
- Scoped diff check passed.
- No commit, push, spool facade, provider integration, or WSL change was made.
- The candidate is not release-ready; fresh independent hostile re-audit and verifier PASS remain mandatory.
- The parent spool coder remains paused pending admission release.
- Durable memory remains unchanged.

### 2026-08-31 User APPROVED Bounded imPACT Cycle-3 Admission Remediation

- The user explicitly **APPROVED** one bounded imPACT cycle-three remediation for the repeated cross-process admission invariant.
- Frozen remediation scope:
  1. Reject a forked child from every affected public/port/filesystem entrypoint before any inherited object state, descriptor, mutex, open, or flock interaction; inherited authority, admission, borrow, lease, and related live objects become permanently invalid in that child.
  2. Add mandatory post-effect and post-callback revalidation, including custom-close validation, so hostile mutation cannot return success after only a precheck.
  3. Enforce a terminal authority-quarantine fence: once quarantined, the authority cannot reacquire or issue a new admission.
  4. Make `fcntl`/`os` capability detection exact and fail-closed, preserving only the exact capability names `directory-inode-admission`, `nonblocking-root-admission`, and `fork-revoked-admission` when every required primitive is present.
  5. Narrow contention mapping to the exact accepted contention errno set; unrelated access or I/O failures must not map to `ROOT_IN_USE`.
  6. Add checked-in exec/`CLOEXEC` verification and hostile regressions for every closure above.
- This approval authorizes only the frozen admission remediation and its tests. It does not authorize a publication spool facade, destination/provider integration, compatibility work, commit, push, or release.
- The admission candidate and parent spool work remain paused outside this scope until fresh independent hostile audit and verifier PASS.
- The cycle count is now **cycle 3 by explicit user decision**; any further unresolved recurrence returns to the user rather than silently opening another remediation cycle.
- Durable memory remains unchanged.

### 2026-08-31 Cycle-2 Directory Admission Independent Audit HALT And User-Decision Gate

- Independent audit verdict is **HALT**. The original mutable lock-entry/path-replacement overlap is independently **CLOSED**, but the cycle-two admission candidate is not releasable.
- Release blockers:
  1. **Repeated fork-admission invariant:** port acquisition and `LocalFilesystem` entrypoints fail to reject a child PID before inherited descriptor, mutex, open, or flock activity. This repeats the previously retained fork-admission requirement.
  2. **Novel post-effect/callback closure defect:** `_pin_borrow` and custom close paths perform only prevalidation; a hostile fake `mkdir` mutation can complete and return success without required post-effect revalidation.
  3. **Novel terminal-quarantine fencing defect:** an authority placed in terminal quarantine can reacquire a new admission instead of remaining fenced.
- Medium findings: exact `fcntl` capability detection is incomplete, and `EACCES` is mapped too broadly to `ROOT_IN_USE` rather than preserving closed error semantics.
- Focused audit evidence: **187 passed, 3 skipped**, plus **2 hostile reproductions**. The auditor made no edits.
- The third-cycle/user-decision gate is now **ACTIVE specifically because the fork-admission invariant repeated after cycle-two remediation**. The two novel defects do not independently establish the repetition; the fork defect does.
- No remediation, release, commit, push, or parent spool-facade work is authorized until the user makes the required architecture/scope decision.
- The admission coder remains paused and retained; the main orchestrator must obtain the user decision before any next implementation dispatch.
- Durable memory remains unchanged.

### 2026-08-31 Cycle-2 Directory-Inode Admission Replacement CODE Accepted Provisionally

- The accepted cycle-two admission-only replacement is implemented across exactly seven local-I/O files:
  - `synaptic_host/local_io_v1/model.py`
  - `synaptic_host/local_io_v1/filesystem.py`
  - `synaptic_host/local_io_v1/posix.py`
  - `tests/synaptic_host/local_io_v1/conftest.py`
  - `tests/synaptic_host/local_io_v1/test_boundaries.py`
  - `tests/synaptic_host/local_io_v1/test_filesystem.py`
  - `tests/synaptic_host/local_io_v1/test_posix_spool_admission.py`
- Obsolete lock-file identity and file-lifecycle behavior is removed, including lock-entry creation, `O_CREAT`, `O_EXCL`, first-create fsync, and `LOCK_UN` release.
- Directory-inode admission obtains a fresh, distinct open-file description with `openat(retained_fd, ".", O_RDONLY | O_DIRECTORY | O_CLOEXEC | O_NOFOLLOW)`, applies nonblocking exclusive flock, and creates no directory entry.
- Port results, root authority, high-level admission, and spool-borrow issuance are immutable sealed snapshots rather than caller-mutable/live-map authority.
- Every borrow/effect is admission-bound and revalidated; the root path is reauthenticated around authority-sensitive boundaries.
- Fork is rejected while the pre-lock transition is active; child state is freshly revoked/reinitialized and cannot reuse the parent's admission.
- Release uncertainty is terminal and quarantines the admission rather than permitting reuse.
- No publication spool facade, spool lifecycle, destination, or publication mutation is present. No commit or push was created.
- Focused Windows selection: **187 passed**.
- Real-process Linux Docker selection: **3 passed**.
- Local-I/O plus bundle selection: **279 passed, 7 expected skips**.
- Scoped diff check passed.
- Residuals: independent hostile audit remains pending; raw `os.close` ambiguity is reachable only through the host-injected port boundary; Docker Linux evidence is not canonical WSL ext4 evidence.
- The candidate is not release-ready until independent audit/test PASS.
- imPACT remains **cycle 2**. If the same admission invariant fails after this remediation, it is the third unresolved cycle and work must stop for a user decision.
- The parent spool coder remains paused pending admission release.
- Durable memory remains unchanged.

### 2026-08-31 imPACT Cycle 2 Replacement Architecture: Stable Directory-Inode Admission

- This accepted architecture supersedes the mutable lock-file admission design and controls the cycle-two replacement CODE slice.
- Admission acquires a fresh open-file description for the root directory via `openat(retained_parent_or_root_fd, ".", O_RDONLY | O_DIRECTORY | O_CLOEXEC | O_NOFOLLOW)`, then applies nonblocking exclusive flock. It does not use `dup` and does not create or trust a data-namespace lock entry.
- New immutable `LocalAdmissionRootNodeV1` fields are exactly `device`, `inode`, `file_type`, and `node_digest`.
- New immutable `RetainedDirectoryAdmissionV1` fields are exactly `lease_ref`, `root_node`, `process_id`, `process_instance_ref`, and `lease_digest`.
- Corrected immutable `LocalSingleRootAdmissionV1` binds exactly `admission_ref`, `authority_digest`, the retained-directory `lease_digest`, `PUBLICATION_SPOOL` purpose, process ID/reference, and `admission_digest`.
- Renamed exact port APIs:
  - `acquire_directory_admission(directory)`
  - `validate_directory_admission(directory, admission)`
  - `release_directory_admission(directory, admission)`
- Port results, host admissions, and every spool-borrow issuance are reconstructed into immutable snapshots and bound by their canonical seals/digests before use.
- The root path and retained device/inode/type identity are reauthenticated, and the admission plus issuance seal is revalidated, around every borrow, effect, callback, close, and release boundary.
- Fork handling rejects fork while an admission transition is pre-lock/in flight; registered at-fork handling revokes inherited child state, and the child must acquire fresh process-local locks and admission.
- Admission lifecycle is closed over `ACTIVE`, `RELEASING`, `RELEASED`, and `QUARANTINED`. Release is descriptor close, never `LOCK_UN`; an uncertain close/release enters `QUARANTINED` rather than permitting reuse.
- Closed error vocabulary is exactly `ROOT_IN_USE`, `ADMISSION_INVALID`, `ADMISSION_RELEASE_INDETERMINATE`, `ROOT_CHANGED`, `CAPABILITY_UNAVAILABLE`, `BORROW_IN_USE`, and `IO_FAILED`.
- Capability names are exactly `directory-inode-admission`, `nonblocking-root-admission`, and `fork-revoked-admission`.
- Those capabilities are available only when all predicates hold: native POSIX; callable `fcntl.flock`; `LOCK_EX` and `LOCK_NB`; callable `os.open`, `os.close`, `os.fstat`, `os.getpid`, and `os.register_at_fork`; `O_RDONLY`, `O_DIRECTORY`, `O_CLOEXEC`, and `O_NOFOLLOW`; directory-FD support; and retained-directory support. Otherwise capability detection fails closed.
- Remove the obsolete fixed `.synaptic-publication-spool-admission-v1.lock` design completely, including lock-entry creation/unlink assumptions, `LocalAdmissionLockIdentityV1`, `RetainedExclusiveRootLeaseV1`, acquire/validate/release-exclusive-root-lease APIs, the old capability flags, and their obsolete tests.
- Required gates include real-process single-winner contention, independent same-process opens, crash/normal release, path replacement and root reauthentication, inode/type drift, fork-during-transition and child revocation, exec closure, immutable DTO/live-map substitution, per-effect/per-callback validation, close uncertainty/quarantine, exact error mapping, capability predicate failure, and absence of every obsolete lock-file surface.
- Stop and return to architecture if any retained directory identity, immutable issuance seal, per-boundary revalidation, fork rule, lifecycle transition, close-as-release behavior, capability predicate, obsolete-surface removal, or required cross-process gate cannot be proven.
- Replacement CODE scope remains local-I/O directory-admission groundwork only. It must not add the publication spool facade, lifecycle, destination, or publication mutation.
- imPACT count remains **cycle 2**. If the same admission invariant fails after this remediation and independent audit, it is the third unresolved cycle and requires a user decision before further work.
- The admission coder remains paused until revised to this exact design; the parent spool coder remains paused until the replacement lease is audited and released.
- Durable memory remains unchanged.

### 2026-08-31 Directory-Inode Flock Mini-PREPARE Evidence Accepted

- Empirical Linux/WSL2 Docker overlayfs evidence proves nonblocking exclusive `flock` on a directory file descriptor opened with exact flags `O_RDONLY | O_DIRECTORY | O_CLOEXEC | O_NOFOLLOW`.
- Separate opens within one process contend, and independent processes contend, for the same directory inode lock.
- Normal descriptor close and process crash release the lock.
- File and directory mutations beneath the retained root preserve the directory inode and its held lock.
- Replacing the root path creates a distinct, separately lockable inode; path replacement is therefore not covered by the old lock and requires exact root reauthentication.
- `openat(retained_fd, ".", O_RDONLY | O_DIRECTORY | O_CLOEXEC | O_NOFOLLOW)` produces a fresh open-file description on the same directory inode and is safer than `dup` for fork ownership separation.
- A fork child can close its dedicated fresh directory descriptor without `LOCK_UN`; the parent lock remains held and is not orphaned.
- `O_CLOEXEC` behavior was proven for the tested path.
- Proven scope is Linux/WSL2 Docker overlayfs only. NFS and native Windows are explicitly untested and unclaimed.
- Accepted architecture inputs for imPACT cycle 2:
  - Select a fresh `openat` directory lock rather than a mutable data-namespace lock file.
  - Bind stable device, inode, and directory-type identity.
  - At fork, privately close the child's dedicated descriptor without issuing `LOCK_UN`.
  - Maintain an explicit trusted-parent and path-reauthentication boundary because pathname replacement creates a new inode.
- This PREPARE evidence informs the replacement architecture only; admission implementation and parent spool CODE remain paused pending the accepted architect HANDOFF.
- Durable memory remains unchanged.

### 2026-08-31 Cross-Process Spool Admission TEST PASS, Audit HALT, imPACT Cycle 2

- Independent verifier verdict is **PASS** on stable hashes for the exact seven-file admission candidate:
  - Focused admission selection: **186 passed**.
  - Adjacent selection: **278 passed, 10 expected skips**.
  - Full Host selection: **1,629 passed, 13 expected skips**.
  - Real-process Linux selection: **6 passed**.
  - Canonical WSL state remained unchanged.
- The accepted replacement auditor verdict is **HALT** and controls readiness despite the verifier PASS. The original security-agent output was unavailable and is superseded by this accepted replacement audit.
- Release-blocking findings:
  1. **HIGH:** the reserved lock entry is mutable through spool operations, while borrows do not retain and revalidate the admission for each effect. Replacing the lock entry can therefore allow overlapping authorities.
  2. **HIGH:** fork state and lock ownership are not fully closed, and release retry plus error mapping contain gaps that can strand or misclassify lease state.
  3. **MEDIUM:** authority/admission DTOs and live-map entries remain mutable without immutable issuance snapshots and digest recomputation at use.
- Additional residuals requiring architectural disposition: retry behavior for first-create fsync failure and trustworthy capability detection.
- imPACT classification is **cycle 2, upstream architecture redo**. This is the second architecture cycle, not the third, and no user decision is required yet.
- The next architect must evaluate stable, non-mutable arbitration, specifically including a design that locks a duplicated retained root-directory inode instead of a mutable file inside the spool data namespace.
- The admission coder remains paused and retained. No remediation, release, spool-facade continuation, commit, or push is authorized before the replacement architecture HANDOFF is accepted.
- Durable memory remains unchanged.

### 2026-08-31 Cross-Process Spool Admission CODE Accepted Provisionally

- The admission-only nested CODE handoff is accepted provisionally across exactly seven files:
  - `synaptic_host/local_io_v1/model.py`
  - `synaptic_host/local_io_v1/filesystem.py`
  - `synaptic_host/local_io_v1/posix.py`
  - `tests/synaptic_host/local_io_v1/conftest.py`
  - `tests/synaptic_host/local_io_v1/test_boundaries.py`
  - `tests/synaptic_host/local_io_v1/test_filesystem.py`
  - `tests/synaptic_host/local_io_v1/test_posix_spool_admission.py`
- Final exact model and purpose surface: `LocalIOCodeV1.ROOT_IN_USE`, `LocalIOCodeV1.ADMISSION_INVALID`, `SingleRootPurposeV1.PUBLICATION_SPOOL`, `BorrowPurposeV1.PUBLICATION_SPOOL`, `LocalAdmissionLockIdentityV1`, `RetainedExclusiveRootLeaseV1`, `LocalSingleRootAdmissionV1`, and `LocalSingleRootAuthorityV1`.
- The fixed persistent lock is `.synaptic-publication-spool-admission-v1.lock`; its inode is retained and the implementation never unlinks it as part of normal release/recovery.
- The POSIX port implements `acquire_exclusive_root_lease`, `validate_exclusive_root_lease`, and `release_exclusive_root_lease`; opening is no-follow and close-on-exec, acquisition uses a nonblocking exclusive flock, and validation binds retained identity plus owner, mode, and link count.
- `LocalFilesystem` implements `acquire_single_root_admission`, `release_single_root_admission`, and admission-gated `borrow_single_root`.
- Admission is bound to the live process instance, with at-fork invalidation. Inherited child state cannot exercise the parent admission.
- Existing dual-root borrows and new single-root borrows remain type- and purpose-fenced. Dependent borrows and owned cleanup release before the single-root admission; the host admission releases before the retained OS lease.
- Capability flags are exactly `nonblocking-root-lease` and `fork-safe-root-lease`.
- No publication spool facade, spool lifecycle, destination, or publication mutation is implemented in this candidate.
- Focused Windows selection: **186 passed**.
- Real-process Linux Docker admission selection: **6 passed**.
- Scoped diff check passed.
- Canonical WSL verification was unavailable because pytest is not installed there; no WSL changes were made.
- This candidate is not release-ready. It requires independent security audit and full verification on the exact seven-file state before a release checkpoint.
- The admission coder is complete and retained for any ownership-routed remediation; the parent spool coder remains paused.
- Durable memory remains unchanged.

### 2026-08-31 Nested rePACT Architecture Accepted: Cross-Process Spool Admission

- This accepted architect HANDOFF controls the bounded `cross-process-spool-admission` nested slice.
- Admission uses the persistent fixed lock file `.synaptic-publication-spool-admission-v1.lock` and retains a nonblocking exclusive POSIX `fcntl.flock(LOCK_EX | LOCK_NB)` for the owning facade lifetime.
- Exact model surface:
  - `LocalIOCodeV1.ROOT_IN_USE`
  - `LocalIOCodeV1.ADMISSION_INVALID`
  - `LocalAdmissionLockIdentityV1`
  - `RetainedExclusiveRootLeaseV1`
  - `LocalSingleRootAdmissionV1`
- Exact POSIX port APIs:
  - `acquire_exclusive_root_lease(directory, *, lock_component)`
  - `validate_exclusive_root_lease(directory, lease, *, lock_component)`
  - `release_exclusive_root_lease(lease)`
- Exact `LocalFilesystem` APIs:
  - `acquire_single_root_admission(authority, *, purpose)`
  - `borrow_single_root(authority, admission, request)`
  - `release_single_root_admission(authority, admission, *, purpose)`
- The unreleased broad `borrow_root` direction is superseded by admission-gated `borrow_single_root`; no single-root borrow is valid without the exact live admission for the same authority and purpose.
- Acquisition must validate the fixed lock entry and retained handle identity, require the accepted mode/owner/link-count invariants, and bind the raw lease to the exact root, lock component, purpose, authority, process, and live registry entry.
- Separate live registries track raw retained leases and host admissions. State transitions and release order are closed: validate the live admission for every borrow, release all dependent borrows/owned cleanup first, then release host admission, then release the retained OS lease.
- Fork safety is mandatory: install `register_at_fork` handling, invalidate inherited child-side registry/admission state, and prevent a fork child from treating the parent's retained lease as its own authority.
- Crash closes the process-held flock through OS handle teardown; a later process may acquire only after proving the fixed lock identity and invariants again. Exec/restart receives no reconstructed Python admission or borrowed reference; every new process performs fresh acquisition and startup proof.
- Error mapping is closed: current contention maps to `LocalIOCodeV1.ROOT_IN_USE`; malformed, substituted, drifted, unsupported, or non-live admission/lease state maps to `LocalIOCodeV1.ADMISSION_INVALID`; raw platform exception context must not cross the boundary, and partial acquisition must close owned handles.
- Capability reporting may advertise retained-exclusive-root admission only where these exact primitives and lifecycle guarantees are supported; missing or false support is a stop condition.
- Required gates cover cross-process single-winner admission, live-owner contention, crash release and restart acquisition, exec/fork behavior, fixed-entry and retained-identity substitution, mode/owner/link-count rejection, registry/state/order misuse, error closure, handle cleanup, and regression compatibility for existing local-I/O capability fences.
- Stop implementation and do not resume the spool facade if any exact API, retained lifetime, identity proof, fork guard, registry transition, release order, closed error mapping, or required cross-process gate cannot be met.
- Nested CODE scope is local-I/O admission groundwork only. It must not implement the spool lifecycle, facade, destination, or publication mutation.
- The parent spool coder remains paused and may resume facade/spool work only after this lease slice receives independent audit/test PASS and a scoped release checkpoint.
- Durable memory remains unchanged.

### 2026-08-31 Local Publication Spool Stage 1 Partial CODE And imPACT

- The accepted spool handoff is safe partial groundwork only; it is not phase completion and is not release-ready.
- Stage 1 changed exactly three files:
  - `synaptic_host/local_io_v1/model.py`
  - `synaptic_host/local_io_v1/filesystem.py`
  - `tests/synaptic_host/local_io_v1/test_boundaries.py`
- The partial implementation establishes the dedicated single-root publication-spool authority, purpose, and type fences.
- Focused local-I/O boundary evidence: **184 passed**.
- The unsafe spool draft and its exports were removed. No spool lifecycle implementation or spool lifecycle tests remain in this partial candidate.
- Hard blocker: the design lacks an exact cross-process retained-directory-handle admission/lease. Exclusive marker creation alone cannot distinguish a live owner from a crashed stale marker, so safe stale admission/reclamation is not yet defined.
- Parent spool CODE is paused; the spool coder is retained but must not resume implementation against the incomplete admission model.
- imPACT classification: **upstream architecture gap** rather than a local coding defect.
- Chosen bounded nested rePACT scope: `cross-process-spool-admission`.
- Next phase: a bounded architecture design for the POSIX retained-dirfd lease and its cross-process admission/recovery contract. No user decision is required yet.
- No commit, push, provider, Docker, WSL, or release action is claimed by this partial handoff.
- Durable memory remains unchanged.

### 2026-08-31 Local Publication Spool Controlling Architecture Accepted

- The accepted architect HANDOFF is the controlling design for the local publication-spool slice.
- Add the distinct capability purpose `SingleRootPurposeV1.PUBLICATION_SPOOL` and the exact `LocalSingleRootAuthorityV1`; publication-spool authorities use a separate authority registry and type fence from other local-I/O roots.
- Add `BorrowPurposeV1.PUBLICATION_SPOOL`. The spool borrow contract is fail-closed: only the publication-spool action allowlist is admitted, and every action outside that matrix is denied.
- The spool owns both live and finished references. `release_finished` releases a finished reference, while terminal `cleanup_owned` is cached/idempotent for the spool's owned state.
- Cleanup completes before the borrow token and root authority are released; reversing or weakening that order is prohibited.
- Acquisition performs a bounded scan of stale files and may reclaim only eligible stale entries within the exclusive, flat publication-spool root. The design does not reconstruct references after restart.
- Destination publication may consume spool contents only through `iter_finished`; it receives no direct root authority or alternate path-based read surface.
- Stop conditions are fail-closed: do not proceed when the dedicated purpose/type fence or exclusive flat-root invariant is absent, an action is outside the allow matrix, stale scanning/reclamation exceeds its bound or authority, cleanup-before-release cannot be maintained, or destination access would bypass `iter_finished`.
- Residual limitation: on POSIX, a same-user process may still replace entries where filesystem ownership and permissions allow it. This is recorded as a residual rather than silently claimed closed.
- Staged implementation order is frozen:
  1. Implement the local-I/O single-root capability and dedicated publication-spool purpose/authority fence.
  2. Implement the spool lifecycle, bounded acquisition cleanup, finished iteration, and release semantics.
  3. Integrate facade ownership and terminal cleanup/release ordering.
- The existing spool coder remains paused with no edits and must revise its teachback to this exact controlling architecture before receiving PROCEED.
- Final destination implementation remains pending and outside this spool slice.
- Durable memory remains unchanged.

### 2026-08-31 Host Publication Authority And Configuration Release Checkpoint

- Accepted host release commit: `946056a4f732036a38da2f2efff23d3de8ccefec`.
- The release commit contains exactly the nine accepted authority/config paths:
  - `synaptic_host/publication_authority.py`
  - `synaptic_host/artifact_destinations.py`
  - `synaptic_host/__init__.py`
  - `training/artifacts.json`
  - `training/storage.json`
  - `tests/synaptic_host/test_publication_authority.py`
  - `tests/synaptic_host/test_artifact_destinations.py`
  - `tests/synaptic_host/test_verified_artifact_source.py`
  - `tests/synaptic_host/local_io_v1/test_config.py`
- The host commit was pushed normally. Windows host, origin host branch, and canonical WSL host resolve to exact commit `946056a4f732036a38da2f2efff23d3de8ccefec`.
- The engine gitlink and engine repository remain unchanged at exact commit `13008e7581f47c6a78d95981543a7fb6a3b62c15`.
- Repo-focused `.codex/pact` edits remain preserved outside the release commit.
- The two unrelated canonical-WSL manifest type changes remain preserved and untouched:
  - `gemma4-e4b/eval_pool_manifest.json`
  - `gemma4-e4b/split_manifest.json`
- Existing host test residue remains preserved and excluded from release evidence.
- No source, review, or provider blocker remains for this checkpoint. The host publication authority/configuration slice is **COMPLETE**.
- Next dispatch: implement the local publication spool and its dedicated publication-spool borrow purpose. Final destination implementation remains pending as a later slice.
- Durable memory remains unchanged.

### 2026-08-31 Engine Publication Codec Release Checkpoint

- Accepted engine release commit: `13008e7581f47c6a78d95981543a7fb6a3b62c15`.
- The engine commit contains exactly three files:
  - `synaptic-tuner/tuner/execution/coordinator_v1/publication.py`
  - `synaptic-tuner/tests/execution/coordinator_v1/test_publication.py`
  - `synaptic-tuner/tests/contract/test_public_publication_v1.py`
- Accepted host release commit: `bc0b64d6643c62ffc14ce9df3d8ff08d82787b37`.
- The host release commit contains only the `synaptic-tuner` gitlink update to exact engine commit `13008e7581f47c6a78d95981543a7fb6a3b62c15`.
- Windows host, origin host branch, and canonical WSL host resolve to exact host commit `bc0b64d6643c62ffc14ce9df3d8ff08d82787b37`.
- Windows engine/submodule, origin engine branch, and canonical WSL engine/submodule resolve to exact engine commit `13008e7581f47c6a78d95981543a7fb6a3b62c15`.
- The canonical WSL engine checkout is detached at the gitlink commit, which is normal submodule state rather than a release defect.
- Repo-focused `.codex/pact` edits remain preserved outside the release commit.
- The two unrelated canonical-WSL manifest type changes remain preserved and untouched:
  - `gemma4-e4b/eval_pool_manifest.json`
  - `gemma4-e4b/split_manifest.json`
- Existing host `.test-tmp` and engine pytest residue remain preserved and excluded from release evidence.
- No tests were rerun during release operations because the accepted fresh independent verifier and auditor gates already passed on the exact stable candidate.
- No provider, network, Docker, WSL workload, credential, publication, or paid action occurred during this checkpoint harvest.
- No release blocker remains. The engine canonical publication-evidence codec prerequisite is **COMPLETE**.
- Next dispatch: host typed publication-evidence issuers plus capability-root destination configuration, followed by local spool and destination implementation under the accepted architecture.
- Coder, auditor, verifier, and release roles are complete; the secretary remains reusable for host-slice harvests.
- Durable memory remains unchanged.

### 2026-08-31 Host Publication Authority And Capability Configuration CODE Accepted Provisionally

- The host authority/config CODE handoff is accepted as a complete candidate for this slice. Fresh independent audit and test gates remain pending; no release is authorized yet.
- Exactly nine host paths changed:
  - `synaptic_host/publication_authority.py`
  - `synaptic_host/artifact_destinations.py`
  - `synaptic_host/__init__.py`
  - `training/artifacts.json`
  - `training/storage.json`
  - `tests/synaptic_host/test_publication_authority.py`
  - `tests/synaptic_host/test_artifact_destinations.py`
  - `tests/synaptic_host/test_verified_artifact_source.py`
  - `tests/synaptic_host/local_io_v1/test_config.py`
- New `PublicationEvidenceAuthorityV1` owns exactly four typed publication-evidence issuers aligned to the released engine codecs.
- The authority exposes no legacy unpacking path, generic signer, generic arbitrary-document issuer, or compatibility surface.
- Typed issuance reconstructs and returns exact engine public values rather than host-shaped dictionaries or private parser output.
- `ResolvedDestinationAdapterV1` now binds exact immutable adapter identity, descriptor/configuration identity, and the resolved capability authorities required by that adapter.
- The destination registry computes destination identity itself from the exact declared canonical configuration plus role-labelled resolved authority digests; adapter factories do not supply or override that digest.
- Role labels are part of the digest input, so exchanging otherwise valid data/control authorities changes identity and fails exact binding.
- `training/artifacts.json` is capability-only: destination entries carry opaque adapter/configuration and capability references, never raw local paths, credentials, or provider-native authority material.
- `training/storage.json` declares distinct capability roots for final artifact data, publication control/evidence, and publication spool storage.
- Final-data, control, and spool authority references are distinct and cannot alias by configuration.
- The future local adapter must resolve and supply the actual data-root and control-root authority digests through the accepted capability ports. Local spool and destination mutation remain intentionally outside this slice.
- Focused authority/config selection: **40 passed**.
- Full Host selection: **1,611 passed, 7 expected skips**.
- Scoped diff check passed.
- No commit or push was created.
- The coder is complete and retained for ownership-routed remediation.
- Host local spool/destination implementation remains blocked until fresh independent audit/test PASS and this exact nine-file candidate is released.
- Durable memory remains unchanged.

### 2026-08-31 Host Publication Authority Verification PASS And Audit REVISE

- Independent verification **PASS** is accepted for the frozen nine-file authority/config candidate: **54 focused passed**; adjacent selection **180 passed, 1 expected skip**; full Host selection **1,611 passed, 7 expected skips**.
- The verifier confirmed stable hashes for all nine candidate files, import checks, JSON validation, and scoped diff checks.
- Independent audit verdict is **REVISE** and controls release readiness despite the green test evidence. Four release-blocking findings remain:
  1. Leaf issuers are not sealed to their evidence purpose; cross-purpose dispatch can produce a valid HMAC under the wrong authority.
  2. Raw callback-discovery exceptions can escape the authority boundary and disclose uncontrolled context.
  3. Post-factory invariant reconstruction does not fully enforce the exact nonempty role, allowing an empty role to be accepted.
  4. `PublicationEvidenceAuthorityV1` is publicly constructible and replaceable rather than being a factory-issued, closure-private authority bundle.
- Confirmed strengths remain accepted: artifact destination configuration contains capability references only; final-data, control, and spool roots are distinct; the registry owns destination-digest computation; and the digest binds canonical declared configuration plus role-labelled resolved authority digests, so role swaps change destination identity.
- The future local adapter must still authenticate the actual data-root and control-root authority digests. That authenticity proof is outside this slice and remains a residual for local-adapter implementation.
- No commit, push, or release is authorized. Local spool/destination implementation remains blocked.
- Immediate next dispatch: return the candidate to the original host coder to seal typed issuers against cross-purpose use, close callback exception leakage, enforce exact post-factory role invariants, and make the authority bundle factory-issued and non-replaceable; then require fresh independent verifier and auditor PASS.
- Durable memory remains unchanged.

### 2026-08-31 Host Publication Authority Audit Remediation CODE Accepted Provisionally

- The remediation CODE handoff is accepted for the unchanged exact nine-file authority/config candidate. All four prior audit findings are dispositioned as remediated, but fresh independent final audit and test gates remain required before release.
- Finding 1 closure: each typed issuer is closure-private and sealed to its one evidence purpose; cross-purpose dispatch is rejected rather than producing a valid wrong-authority HMAC.
- Finding 2 closure: adapter callback discovery uses a pinned, closed probe and maps callback failures across the boundary without leaking raw exception context.
- Finding 3 closure: the complete adapter factory result is detached and reconstructed under the full invariant set, including the exact nonempty role, before acceptance.
- Finding 4 closure: `PublicationEvidenceAuthorityV1` is a factory-only sealed aggregate and cannot be publicly constructed or replaced with arbitrary leaf issuers.
- Hostile focused remediation selection: **68 passed**.
- A full Host run completed before the final narrow aggregate-validation addition: **1,625 passed, 7 expected skips**.
- After that final addition, the directly affected selection completed: **54 passed**. This focused result does not replace the required full Host rerun on the final candidate hashes.
- Scoped diff check passed. No commit or push was created.
- Release remains blocked pending a fresh independent auditor PASS and verifier PASS, including one full Host rerun against the final stable nine-file hashes.
- The future local adapter must still authenticate the actual data-root and control-root authority digests; that next-slice responsibility is unchanged and is not claimed by this remediation.
- The coder is complete and retained for any ownership-routed follow-up.
- Durable memory remains unchanged.

### 2026-08-31 Host Publication Authority Final Verification PASS And Re-Audit REVISE

- Final independent verifier verdict is **PASS** on the final nine-file hashes: **68 focused passed**; adjacent selection **194 passed, 1 expected skip**; full Host selection **1,625 passed, 7 expected skips**.
- Compile, cold-import/import, JSON validation, scoped diff, and status checks passed on that final candidate.
- The independent re-audit verdict is **REVISE** and controls release readiness. Two remaining **HIGH** blockers require narrow remediation:
  1. The shared issuer base remains insufficiently sealed: inherited `__getattribute__` behavior or issuer-surface substitution can occur before the purpose pins are enforced.
  2. An adapter callback descriptor can mutate `authority_bindings`; the subsequent unguarded post-probe equality check can raise and leak raw exception text.
- All other prior audit findings and their remediation dispositions are independently closed: cross-purpose typed dispatch after established pins, ordinary callback-discovery failure closure, exact nonempty-role reconstruction, and factory-only sealed aggregate construction remain accepted outside the two refinements above.
- Previously confirmed strengths remain intact: capability-only artifact configuration; distinct final-data, control, and spool roots; registry-owned destination-digest computation; and canonical configuration plus role-labelled resolved authority digests that make role swaps change identity.
- No commit, push, or release is authorized. Local spool/destination implementation remains blocked.
- Immediate next dispatch: the original host coder performs a narrow remediation that seals the shared issuer base before any inherited/surface substitution and closes the mutating-descriptor post-probe comparison without raw exception leakage.
- After remediation, require a fresh hostile audit and focused verifier run. Repeat the full Host suite only if the final code scope justifies it.
- The future local adapter's actual data-root and control-root authenticity proof remains a separate next-slice responsibility.
- Durable memory remains unchanged.

### 2026-08-31 Host Publication Authority Final Narrow Remediation CODE Accepted

- The final narrow-remediation CODE handoff is accepted across exactly four files:
  - `synaptic_host/publication_authority.py`
  - `synaptic_host/artifact_destinations.py`
  - `tests/synaptic_host/test_publication_authority.py`
  - `tests/synaptic_host/test_artifact_destinations.py`
- The shared issuer base is now sealed before inherited `__getattribute__` behavior or issuer-surface substitution can bypass purpose pins.
- The raw post-callback equality comparison was removed. Pre-probe and post-probe values are independently detached through `_reconstruct_resolved_binding` into exact snapshots before comparison, closing callback-descriptor mutation and raw exception leakage.
- The exact two bypass regressions passed: **2 passed**.
- Complete directly affected focused selection: **56 passed**.
- Final full Host selection on this remediation: **1,627 passed, 7 expected skips**.
- Scoped diff check passed. No configuration or engine files changed; no commit or push was created.
- The final nine-file authority/config candidate is ready for fresh independent audit and verification, but is not released yet.
- The final auditor must rerun the exact two bypass probes; the verifier must freeze and validate the final nine-file candidate.
- Durable memory remains unchanged.

### 2026-08-31 Host Publication Authority Final Audit And Test PASS

- Final independent audit verdict is **PASS**: both exact issuer-base and mutating-callback bypass probes passed, the focused audit selection completed **82 passed**, every prior audit finding is closed, and no new finding was reported.
- Final independent verifier verdict is **PASS** on stable hashes for the exact nine-file authority/config candidate:
  - Exact bypass selection: **2 passed**.
  - Authority/registry selection: **56 passed**.
  - Focused host selection: **70 passed**.
  - Adjacent selection: **196 passed, 1 expected skip**.
  - Full Host selection: **1,627 passed, 7 expected skips**.
- Compile, cold-import/import, JSON validation, scoped diff, and status checks were clean on the stable final candidate.
- Confirmed strengths remain intact: capability-only artifact configuration; distinct final-data, control, and spool roots; registry-owned destination-digest computation; and canonical configuration plus role-labelled resolved authority digests that make role swaps change identity.
- The sole remaining residual belongs to the next local-adapter slice: authenticate the actual data-root and control-root authority digests. It does not block release of this authority/config candidate.
- The exact nine-file host candidate is **RELEASE-READY** for a scoped commit, push, and Windows/origin/WSL parity verification.
- Coder, auditor, and verifier are complete; release operations are the next dispatch.
- Durable memory remains unchanged.

### 2026-08-31 Host Local Destination And Publication Composition Release Checkpoint

- Final independent hostile audit verdict: **PASS — 94 passed, 2 expected skips**.
- Final independent verifier verdict: **PASS**:
  - Engine publication contract: **22 passed**.
  - Focused Host composition: **72 passed, 2 expected skips**.
  - Real offline Linux Docker POSIX end-to-end: **2 passed**.
  - Adjacent Host selection: **322 passed, 13 expected skips**.
  - Full Host selection: **1,710 passed, 19 expected skips**.
- Accepted engine commit/push: `42833b5ab835ebf11d1c8ca37e16f28b0e680b67`, containing exactly:
  - `synaptic-tuner/synaptic_tuner/api/v1/publication.py`
  - `synaptic-tuner/tests/contract/test_public_publication_v1.py`
- Accepted Host commit/push: `9f3cd500d371f55b74c7a3beb8c03d94b00d4a5d`, containing exactly the engine gitlink update plus eight Host paths:
  - `synaptic_host/artifact_destinations.py`
  - `synaptic_host/local_artifact_destination.py`
  - `synaptic_host/publication_composition.py`
  - `synaptic_host/__init__.py`
  - `tests/synaptic_host/test_artifact_destinations.py`
  - `tests/synaptic_host/test_local_artifact_destination.py`
  - `tests/synaptic_host/test_publication_composition.py`
  - `tests/synaptic_host/test_publication_local_posix.py`
- Windows engine/Host, origin engine/Host branches, and canonical WSL engine/Host resolve to exact engine SHA `42833b5ab835ebf11d1c8ca37e16f28b0e680b67` and Host SHA `9f3cd500d371f55b74c7a3beb8c03d94b00d4a5d`.
- The two unrelated canonical-WSL manifest type changes remain preserved and untouched:
  - `gemma4-e4b/eval_pool_manifest.json`
  - `gemma4-e4b/split_manifest.json`
- Repo-focused `.codex/pact` state and test residue remain preserved outside the release commits; engine and Host Git indexes are empty.
- No cloud/provider execution, credential use, network action, paid job, or remote publication effect occurred during these release operations.
- Host local destination/publication composition is **COMPLETE**.
- Next sequence: first prove the Docker bridge/local CPU smoke, then proceed to Modal-first integration under separate gates.
- Durable memory remains unchanged.

### 2026-08-31 Docker Public Dispatch Proof-First Checkpoint

- Current Docker public dispatch remains unavailable; this checkpoint is not final release acceptance.
- Exact discovered blocker: the existing executable policy/binding assumes a Windows `C:\...` Docker CLI path maps into WSL as `/mnt/c/...`, while this Docker Desktop installation exposes the working Windows CLI at `/Docker/host/bin/docker.exe`.
- Accepted external evidence:
  - Docker Desktop WSL 2 backend guidance: `https://docs.docker.com/desktop/features/wsl/`.
  - Docker Desktop general FAQ Unix-socket guidance: `https://docs.docker.com/desktop/troubleshoot-and-support/faqs/general/`.
  - Docker for Windows issue corroborating `/Docker/host/bin/docker.exe`: `https://github.com/docker/for-win/issues/14939`.
- The official Docker guidance favors WSL-integrated CLI/Unix-socket access over translating a Windows executable path through `/mnt/c`.
- Accepted proof-first sequence:
  1. Minimally correct executable binding for the actual Docker Desktop/WSL environment.
  2. Run a real offline facade smoke with an exactly pinned Alpine image.
  3. Only after that proof passes, resume Docker bridge and public training-run wiring.
- Exact five-file candidate inventory:
  - `synaptic_host/docker_v1/model.py`
  - `synaptic_host/docker_v1/interop.py`
  - `tests/synaptic_host/docker_v1/test_cli.py`
  - `tests/synaptic_host/docker_v1/test_interop.py`
  - `tests/synaptic_host/docker_v1/test_real_docker_wsl.py`
- Windows focused evidence: **263 passed, 1 expected WSL skip**.
- Candidate checkpoint commit/push: `581b472e`. It remains unreleased pending the real WSL/Docker offline proof and fresh gate assessment.
- No model execution, training, cloud/provider action, credential use, network publication, paid job, or remote effect occurred.
- Durable memory remains unchanged.

### 2026-08-31 Real Docker/WSL Public-Facade Proof Release Checkpoint

- Host branch: `feat/submodule-cloud-api-v1-host`.
- Engine commit remains `42833b5ab835ebf11d1c8ca37e16f28b0e680b67`.
- Current Host HEAD is `25428f3b`, including the diagnostic commits through the final parser correction.
- The real public-facade offline smoke passed under WSL Python 3.10 with the exactly pinned Alpine image and wrote the expected exact artifact.
- Root cause: Python 3.10 `datetime.fromisoformat` rejected Docker `StartedAt` timestamp values carrying nanosecond fractional precision.
- Final parser correction validates the exact 1–9 digit fractional-second grammar, then normalizes fractional precision to six digits only for semantic datetime parsing; the original transport value remains governed by the exact grammar.
- The transient retry workaround was removed after the deterministic parser correction.
- Windows Docker suite: **939 passed, 1 expected WSL-only skip**.
- WSL focused selection: **40 passed**.
- The exact smoke container was cleaned after verification.
- The real Docker/WSL public-facade proof is **COMPLETE**.
- No model training, cloud/provider execution, credential use, network publication, paid job, or remote effect occurred in this proof.
- Durable memory remains unchanged.

### 2026-08-31 Current Docker Public Training PREPARE Accepted

- The accepted `/root/docker_public_prepare` HANDOFF is the current basis for the next Docker Architect dispatch; the preparer completed read-only and made no repository changes.
- Public Docker ingress exists, but its current implementation returns `PROVIDER_UNAVAILABLE` rather than composing a training run.
- The canonical public planning contract is `synaptic_tuner.api.v1.training.TrainingPlan`.
- The legacy same-process Docker stack consumes the distinct legacy `synaptic_tuner.api.v1.planning.TrainingPlan`; this type split must be resolved rather than bridged through an implicit compatibility path.
- The canonical training worker is `Trainers/sft/runtime_v1.py`, with invocation groundwork in `tuner.runtime.dispatch`.
- The current runtime path still carries Modal, dual-clone, and canonical-stdin assumptions that cannot be treated as a Docker worker contract without an explicit architecture decision.
- The Docker sealed bundle does not yet carry an authenticated logical workload file/byte transport suitable for the canonical worker.
- Host-owned SQLite lifecycle persistence and Host-owned artifact publication are real, released foundations and should be composed rather than reimplemented inside Docker or the engine.
- No relevant current `docs/plans` implementation plan exists for this Docker public-training convergence.
- Prior `local-run` simplicity explains historical behavior but is evidence only; it must not become the public `training run` implementation or bypass durable lifecycle/publication boundaries.
- CPU SFT is not currently viable under the existing CPU-only, network-none Docker policy because the trainer path is Unsloth/GPU oriented. A local CPU smoke may prove infrastructure/worker transport, but must not be represented as viable CPU SFT training.
- Required next Architect scope:
  - Converge all public Docker planning and dispatch on the canonical public `TrainingPlan` with no legacy alias.
  - Freeze an engine-owned Docker worker contract and authenticated logical workload-file transport into the sealed bundle.
  - Freeze the Host resolver, durable Docker lifecycle/effect/recovery wiring, observation, and Host-owned publication boundaries.
  - Define an honest provider capability/readiness result for unsupported CPU SFT and separate infrastructure proof from model-training proof.
- No CODE, test mutation, provider call, model execution, network, credential, paid, or publication effect is authorized by this PREPARE checkpoint.
- Durable memory remains unchanged; no new cross-session memory candidate is promoted from this routine preparation evidence.

### 2026-08-31 Docker Public Training ARCHITECT Accepted

- The accepted Docker public-training architecture makes `synaptic_tuner.api.v1.training.TrainingPlan` the sole canonical plan. No adapter to the legacy Docker `synaptic_tuner.api.v1.planning.TrainingPlan` is permitted.
- Retain and generalize `Trainers/sft/runtime_v1.py` as the canonical worker rather than introducing a Docker-specific trainer.
- The engine owns authenticated workload byte/file transport and a typed `WorkerInvocationV1` in `tuner.runtime.dispatch`; Docker transports the sealed invocation without inventing workload semantics.
- Replace the Modal-named runtime schema with a provider-neutral runtime contract in a coordinated cutover, with no compatibility alias. Retain dual-clone topology for now as an explicit current constraint.
- The Host adds Docker provider configuration, source/runtime resolution, and public training composition. Low-level Docker mechanics already proven by the real facade smoke are retained rather than rewritten.
- Host project-level SQLite remains the durable lifecycle authority and should evolve to persist opaque provider preparation/control records; neither the engine nor a Docker worker owns a database.
- Final artifacts flow through the configured Host publication destination. Provider staging is internal execution state and is not a public destination or publication surface.
- Implementation sequence is frozen:
  1. Engine contract slice: canonical plan convergence, provider-neutral runtime schema, authenticated workload transport, and `WorkerInvocationV1`.
  2. Host admission slice: honest Docker configuration/resolution/composition and capability reporting, with unsupported SFT rejected before Docker, SQLite, spool, or publication effects.
  3. Canonical Docker execution slice: durable prepare/submit/observe/recover/verify/publication composition over the proven low-level facade.
  4. Closed NVIDIA capability slice and cached, pinned Unsloth one-step public SFT smoke; the observed cached image and RTX 3090 are read-only feasibility evidence, not an implemented or verified capability.
  5. Remove the legacy same-process Docker planning surface after all callers have migrated; do not preserve it through aliases or adapters.
- Until the capability path is implemented and independently verified, public SFT requests that Docker cannot honestly satisfy must fail closed before any Docker or durable-state effect.
- No CODE, test mutation, provider/model execution, network, credential, paid, or publication effect is authorized by this architecture checkpoint.
- Architect is complete/read-only; no code specialist is active. The next safe dispatch is the bounded engine-contract CODE slice, followed by an independent contract barrier before Host admission work.
- Durable memory remains unchanged; no new cross-session memory candidate is promoted from this accepted architecture handoff.

### 2026-08-31 Docker Engine Contract CODE Slice 1A Candidate

- CODE Slice 1A is a provisional engine candidate pending independent contract and security audit; it is not released and must not yet be consumed by Host implementation.
- The coder changed exactly eight engine files:
  - `synaptic-tuner/tuner/runtime/dispatch.py`
  - `synaptic-tuner/Trainers/sft/runtime_v1.py`
  - `synaptic-tuner/tuner/project/execution_source.py`
  - `synaptic-tuner/schemas/synaptic-execution-source-v1.schema.json`
  - `synaptic-tuner/tuner/execution/providers/modal/modal-runtime-v1.lock.json`
  - `synaptic-tuner/tests/runtime/test_dispatch.py`
  - `synaptic-tuner/tests/trainers/sft/test_runtime_v1.py`
  - `synaptic-tuner/tests/training/test_sft_compilation.py`
- The candidate adds immutable `CanonicalWorkloadBytesV1` and `CanonicalWorkloadFileV1` variants as a closed workload transport union plus typed `WorkerInvocationV1`.
- File-backed workloads use secure, bounded, no-follow ingestion rather than trusting caller paths or unbounded reads.
- The runtime contract is renamed to provider-neutral `synaptic-training-runtime/v1`; there is intentionally no alias for the former Modal-named schema.
- Focused/direct evidence: **164 passed, 7 skipped**. Broader evidence: **617 passed, 10 skipped, 4 failed**.
- The coder attributed the four broader failures to two Qwen expectation mismatches, generated `__pycache__` residue in a frozen-host fixture, and a pre-existing Modal requirements-lock mismatch. These classifications remain provisional until the independent verifier/auditor confirms them.
- `git diff --check` passed for the candidate. No Host files, commits, staging, provider calls, network effects, credentials, paid jobs, or model execution were involved.
- The coder remains available for remediation and owns these eight engine files until the independent barrier completes; no other code worker is active on this scope.
- Release and Host dependency remain blocked pending independent contract/security audit, hostile transport/schema checks, and independent disposition of all four broader failures.
- Durable memory remains unchanged; no stable cross-session memory candidate is promoted from this provisional CODE handoff.

### 2026-08-31 Docker Engine Contract Slice 1A Independent Audit FAIL

- The independent audit **FAILS** the provisional Slice 1A candidate. Slice 1B, Host dependency, release, and commit remain blocked.
- **HIGH — canonical plan binding:** the caller-supplied plan fingerprint is not cryptographically/canonically bound to the exact canonical `synaptic_tuner.api.v1.training.TrainingPlan` and workload bytes that the worker will execute.
- **HIGH — invocation authority:** directly constructible `WorkerInvocationV1` accepts arbitrary entrypoint/interpreter values, overlapping roots, and arbitrary canonical JSON; the materializer then executes that caller-constructed authority rather than a capability-restricted factory product.
- **MEDIUM — file identity:** file ingestion validates ancestry and later opens the target without retaining a directory descriptor/control-root identity across the boundary. POSIX `O_NOFOLLOW` protects only the final component, and Windows lacks an equivalent complete ancestry guarantee in this implementation.
- Verified strengths: factory-path binding and environment isolation are sound; direct consumers use the renamed provider-neutral schema cleanly; the Modal runtime lock carries the exact new runtime hash; Python 3.10 grammar checks pass.
- Independent evidence: focused selection **93 passed, 5 skipped**; direct selection **190 passed, 1 skipped**.
- The four broader failures are independently classified as unrelated to this candidate: Qwen expectation mismatch, preserved frozen-fixture `__pycache__` residue, and CRLF-versus-LF Modal lock portability behavior.
- The existing eight-file candidate remains owned by its coder for remediation, but remediation must wait for bounded Architect clarification of canonical plan/fingerprint issuance, nonconstructible worker invocation authority, and retained-root file transport semantics.
- No fixes, code/test changes, provider calls, commits, staging, or release actions occurred during the read-only audit.
- Durable memory remains unchanged; no cross-session memory candidate is promoted from this failed audit checkpoint.

### 2026-08-31 Docker Engine Contract Slice 1A Remediation Architecture Accepted

- The accepted remediation surface is a factory `build_worker_invocation(plan: TrainingPlan, layout, optional CanonicalWorkloadFileLocationV1)`; callers do not supply a plan fingerprint, entrypoint, interpreter, canonical payload, or other executable authority.
- The factory must independently recompile the exact canonical `TrainingPlan` workload and derive the workload bytes, plan/workload fingerprint bindings, entrypoint, interpreter, runtime layout, and every `WorkerInvocationV1` field from trusted contracts.
- `WorkerInvocationV1` and both canonical workload transports become factory-only issued values. The materializer must authenticate issuance and revalidate all invariant bindings immediately before producing an executable invocation.
- The seven runtime roots plus the workload control root must be pairwise non-overlapping after canonical resolution; equality, ancestry, aliases, and link/reparse-based overlap fail closed.
- Canonical byte transport remains the portable path on all supported hosts.
- Canonical file transport is POSIX-only and must retain an authenticated control-root directory descriptor, traverse with bounded `openat`/no-follow operations, and read the sealed file through that retained identity. Missing primitives and Windows file transport fail closed rather than weakening the guarantee.
- Required hostile coverage includes caller fingerprint/entrypoint/interpreter/payload substitution, direct or reconstructed DTO issuance bypass, stale/mutated plan and transport bindings, all pairwise root overlaps, ancestor replacement/link races, final-component replacement, missing POSIX primitives, Windows rejection, malformed/oversized files, and valid byte/file round trips.
- Remediation must not expand production or test ownership beyond the existing eight Slice 1A engine files. The existing coder remains the sole remediation writer; Architect and auditor are complete/read-only.
- Slice 1B, Host dependency, release, and commit remain blocked until the remediated candidate passes fresh independent contract/security audit and focused verification.
- Durable memory remains unchanged; no cross-session memory candidate is promoted from this remediation architecture checkpoint.

### 2026-08-31 Docker Engine Contract Slice 1A Remediation Candidate

- The remediated Slice 1A candidate changes exactly nine engine files:
  - `synaptic-tuner/tuner/runtime/dispatch.py`
  - `synaptic-tuner/tuner/runtime/__init__.py`
  - `synaptic-tuner/Trainers/sft/runtime_v1.py`
  - `synaptic-tuner/tuner/project/execution_source.py`
  - `synaptic-tuner/schemas/synaptic-execution-source-v1.schema.json`
  - `synaptic-tuner/tuner/execution/providers/modal/modal-runtime-v1.lock.json`
  - `synaptic-tuner/tests/runtime/test_dispatch.py`
  - `synaptic-tuner/tests/trainers/sft/test_runtime_v1.py`
  - `synaptic-tuner/tests/training/test_sft_compilation.py`
- `DispatchSpec` is removed. The only construction path accepts the exact canonical `TrainingPlan` and runtime layout, independently recompiles its workload, and derives every executable binding without caller-supplied fingerprint, entrypoint, interpreter, or payload.
- `WorkerInvocationV1` and canonical byte/file transports are factory-issued and sealed; the materializer authenticates issuance and revalidates their plan, workload, transport, layout, and executable invariants before materialization.
- All runtime roots and the workload control root must remain non-overlapping. File transport uses retained-directory-descriptor POSIX traversal and fails closed when the required primitives are unavailable or on Windows; portable byte transport remains supported.
- Package exports were updated for the new contract with no legacy aliases.
- Candidate evidence: Windows focused/direct selection **194 passed, 14 skipped**; actual Linux Docker hostile selection **10 passed, 59 deselected**; compile, Black, and `git diff --check` passed.
- The pre-existing unrelated Modal CRLF-versus-LF runtime-lock mismatch is unchanged and was not repaired or reclassified by this remediation.
- No Host files, commits, staging, provider calls, network effects, credentials, paid jobs, or model execution occurred.
- This nine-file candidate is not released. The coder retains ownership for possible remediation, and a fresh independent contract/security audit is required before Slice 1B or Host dependency may proceed.
- Durable memory remains unchanged; no cross-session memory candidate is promoted from this provisional remediation handoff.

### 2026-08-31 Docker Engine Contract Slice 1A Re-audit FAIL — FIFO Open

- The independent re-audit confirms all three original findings are closed: canonical plan/workload fingerprint binding, controlled invocation construction/materialization, and descriptor-anchored ancestry/platform handling.
- One new **MEDIUM** blocker remains: both final workload-member opens omit `O_NONBLOCK`, so a hostile FIFO can block before the implementation reaches `fstat` and rejects the non-regular file.
- The required remediation is strictly bounded: add `O_NONBLOCK` to both the initial and confirmation workload-member opens and add a real POSIX prompt-FIFO rejection regression proving prompt failure without blocking.
- Evidence on the remediated candidate: focused selection **102 passed, 12 skipped**; adjacent selection **190 passed, 1 skipped**; Python 3.10 grammar and `git diff --check` passed.
- No other contract, schema, runtime, Host, provider, or publication change is authorized by this finding.
- Slice 1B and Host dependency remain blocked only on this bounded FIFO fix plus fresh independent review. The existing coder remains the sole writer; the auditor remains read-only.
- Durable memory remains unchanged; no cross-session memory candidate is promoted from this narrow re-audit checkpoint.

### 2026-08-31 Docker Engine Contract Slice 1A FIFO Remediation Candidate

- The runtime now requires and applies `O_NONBLOCK` on both final workload-member opens, closing the pre-`fstat` FIFO blocking path; the POSIX primitive-capability gate also requires `O_NONBLOCK`.
- A real POSIX prompt-FIFO rejection regression runs the hostile open in a spawned child with a two-second deadline and proves fail-closed completion without blocking.
- The Modal runtime-lock member was updated to the exact remediated runtime hash.
- Candidate evidence: Windows runtime selection **58 passed, 12 skipped**; Linux Docker hostile selection **11 passed, 59 deselected**. The named test container was absent both before and after the Docker run.
- Black, compile, and `git diff --check` passed.
- No Host files, commits, staging, provider calls, network effects, credentials, paid jobs, publication effects, or model execution occurred.
- This remains a provisional Slice 1A candidate pending final independent audit. The existing coder retains ownership for remediation; the auditor will be reused read-only.
- Slice 1B and Host dependency remain blocked until that final audit passes.
- Durable memory remains unchanged; no cross-session memory candidate is promoted from this bounded remediation checkpoint.

### 2026-08-31 Docker Engine Contract Slice 1A Final Independent Audit PASS

- The final independent auditor returns **PASS** with no remaining blockers.
- The FIFO finding is closed: both final workload-member opens use `O_NONBLOCK`, the POSIX primitive gate requires it, and the real FIFO timeout regression proves prompt rejection without blocking.
- Earlier findings remain closed: canonical plan/workload binding, factory-only invocation and transport issuance, materializer authentication/revalidation, pairwise root/control separation, and retained-descriptor ancestry traversal.
- The Modal runtime-lock hash exactly matches the accepted runtime candidate; the supplied audit evidence reports digest prefix `5eae…`.
- Independent evidence: focused selection **102 passed, 13 expected skips**; Python 3.10 grammar and `git diff --check` passed.
- Supplied Linux Docker evidence is **11 passed, 59 deselected**. Its mutable image-tag provenance limitation remains explicitly documented and does not alter the contract/security PASS.
- Canonical file transport remains POSIX-only and fails closed elsewhere. Restart reconstructs a fresh issued invocation from the canonical `TrainingPlan`; issued invocation objects are not durable restart authority.
- Slice 1A is release-ready, and Host Slice 1B may consume the accepted engine contract after the exact nine-file engine checkpoint is committed and published.
- The coder remains owner only through release checkpointing; the auditor is complete/read-only. No Host implementation, provider call, commit, staging, or release action occurred during this audit.
- Durable memory remains unchanged; no cross-session memory candidate is promoted from this final audit checkpoint.

### 2026-08-31 Docker Engine Contract Slice 1A Released

- Slice 1A was committed in the engine as `593199881dc7428c64703fba93833148f1820388` with message `Generalize provider-neutral SFT runtime dispatch`.
- The release contains exactly nine engine files:
  - `synaptic-tuner/tuner/runtime/dispatch.py`
  - `synaptic-tuner/tuner/runtime/__init__.py`
  - `synaptic-tuner/Trainers/sft/runtime_v1.py`
  - `synaptic-tuner/tuner/project/execution_source.py`
  - `synaptic-tuner/schemas/synaptic-execution-source-v1.schema.json`
  - `synaptic-tuner/tuner/execution/providers/modal/modal-runtime-v1.lock.json`
  - `synaptic-tuner/tests/runtime/test_dispatch.py`
  - `synaptic-tuner/tests/trainers/sft/test_runtime_v1.py`
  - `synaptic-tuner/tests/training/test_sft_compilation.py`
- Commit `593199881dc7428c64703fba93833148f1820388` was pushed to `origin/feat/submodule-cloud-api-v1`; engine local/origin parity is **0 ahead / 0 behind**.
- Engine tracked state is clean. Existing untracked test/residue directories were preserved and are not part of the release.
- The Host index was untouched. Its engine gitlink movement from `42833b5a` to `59319988` remains intentionally unstaged for the later Host Slice 1B checkpoint.
- Existing `.codex/pact` modifications and all unrelated Host/WSL residue were preserved.
- Tests were not rerun during release because the frozen candidate had already passed the accepted independent audit and verification gates.
- Slice 1A release is complete. The next safe dispatch is Host Slice 1B consuming the published provider-neutral engine contract; no Host implementation was performed by this release step.
- Durable memory remains unchanged; no cross-session memory candidate is promoted from this routine release checkpoint.

### 2026-08-31 Host Docker Admission Slice 1B Candidate

- Host Slice 1B is a provisional eight-file admission/composition candidate pending independent audit:
  - `synaptic_host/docker_provider.py`
  - `synaptic_host/docker_training.py`
  - `training/providers/docker.json`
  - `synaptic_host/cli.py`
  - `synaptic_host/__main__.py`
  - `tests/synaptic_host/test_docker_training.py`
  - `tests/synaptic_host/test_cli.py`
  - `tests/synaptic_host/test_cold_bootstrap.py`
- Public Docker planning uses the exact canonical `synaptic_tuner.api.v1.training.TrainingPlan` through `TrainingService`; no legacy Docker plan adapter is introduced.
- Final publication destination is required and validated strictly. Provider staging is internal execution state and is rejected when supplied as a final destination.
- Host composition returns closed destination, resolution, and capability results/codes rather than leaking implementation exceptions or claiming unsupported readiness.
- The initial profile intentionally advertises no supported training method. It returns `CAPABILITY_UNSUPPORTED` before effects, with zero Docker, SQLite, spool/publication, or timestamp mutation.
- Candidate evidence: full Host **1715 passed, 20 skipped**; focused admission **3 passed**; CLI/cold-bootstrap **195 passed, 1 skipped**; compile and `git diff --check` passed.
- The current live command honestly returns `RESOLUTION_UNAVAILABLE` because Host `HEAD` still records the prior engine gitlink while the working submodule is at released engine `59319988`. After audit, the Host checkpoint must include that exact gitlink update.
- No files were staged or committed, and no Docker/provider command, database mutation, publication effect, credential use, network access, paid job, or model execution occurred in this candidate handoff.
- The Host coder owns these eight files for remediation. Independent audit is the next gate; release and execution Slice 1C remain blocked.
- Durable memory remains unchanged; no cross-session memory candidate is promoted from this provisional Host admission handoff.

### 2026-08-31 Host Docker Admission Slice 1B Independent Audit HALT

- Independent audit verdict is **HALT**. The candidate must not be released or used for Docker execution despite its passing tests.
- **CRITICAL — fabricated source trust:** `docker_training` coerces inspected sources to `dirty=False` and `pushed=True`, then creates ephemeral HMAC source evidence instead of consuming an established Host provenance authority.
- **CRITICAL — incomplete binding:** the constructed `SourceLock.configuration` does not bind the Docker provider profile, final destination, ingress, or dataset identity and does not validate their provenance.
- **CRITICAL — root/dataset mislabeling:** ingress is not bound to the project and engine roots, while working-tree dataset bytes can be labeled with the project commit. The currently untracked Docker profile demonstrates a concrete configuration-provenance risk.
- **MEDIUM — private engine coupling:** Host imports private `tuner.training` modules and manually assembles a registry instead of composing through a stable public engine planning/resolution API.
- Current tests use a fake resolver and cold dispatch and therefore do not exercise the real clean-superproject provenance/trust boundary.
- Verified strengths remain valid: the produced plan type is the exact canonical public `TrainingPlan`; no legacy adapter exists; destination parsing is read-only; unsupported admission produces zero Docker, SQLite, or publication effects; capability results are stable and closed.
- Updating the Host gitlink to released engine `59319988` remains mechanically necessary but is not sufficient and does not lift this release HALT.
- Required next step is bounded Architect remediation defining established Host provenance issuance and complete provider/destination/ingress/dataset bindings, a public engine planning API, and a real clean-superproject trust-boundary test before returning the same Host coder to remediation.
- No source/test fixes, staging, commit, provider call, database/publication effect, credential use, network access, paid job, or model execution occurred during this read-only audit.
- The Host coder retains ownership of the candidate for later remediation; the auditor is complete/read-only. Slice 1C remains blocked.
- Durable memory remains unchanged; no cross-session memory candidate is promoted from this critical audit checkpoint.

### 2026-08-31 Host Docker Admission Provenance Remediation Architecture Accepted

- Remediation is split into two strictly sequential slices; the engine public compiler must be released before Host provenance work consumes it.
- **Engine slice:** add import-light public `compile_training_plan_v1(training_input, context, resolver) -> TrainingPlan` under `synaptic_tuner.api.v1`. Default `TrainingService` and registry construction remain private implementation details behind this public function.
- The engine compiler slice must pass its independent boundary checks, then be committed and pushed; the Host gitlink must be updated to that exact released engine commit before Host remediation can pass provenance admission.
- **Host slice:** bind ingress to the exact project root, engine root, and committed configuration bytes. Admission requires real clean and pushed superproject and engine repositories, an exact matching gitlink, and verified upstream relationships.
- Host reads provider profile, destination configuration, dataset, and other bound configuration only from exact committed Git blobs, never mutable working-tree bytes.
- Host constructs closed `SourceLock.configuration` and input records binding provider, final destination, ingress, dataset identity/content, project/engine commits, gitlink, configuration bytes, and upstream evidence.
- Provenance authority is single-use, admission-only, and in-process; it may authorize one exact compilation through the public `compile_training_plan_v1` surface and is not durable/replayable execution authority.
- An honestly unsupported method still returns `CAPABILITY_UNSUPPORTED` before Docker, SQLite, spool, publication, timestamp, or other durable effects.
- Delete coerced `dirty=False`/`pushed=True` flags, temporary HMAC evidence, private `tuner.training` imports, manual registry assembly, working-tree dataset reads, and the fake-resolver trust-boundary test.
- Add an artifact-destination bytes parser so committed destination blobs can be parsed without substituting working-tree paths.
- Required Host proof uses real temporary clean superproject and engine repositories with local bare remotes, pushed commits, exact gitlink, and committed profile/destination/dataset/config blobs. Negative cases cover dirty/unpushed state, gitlink/upstream mismatch, mutated working-tree bytes, and provenance substitution.
- The current dirty worktree is a required negative provenance case and must not be normalized or treated as an eligible live source.
- Engine and Host coders are idle; dispatch must be sequential: engine compiler CODE and independent barrier, engine release/gitlink update, then Host remediation CODE and fresh independent audit. Slice 1C remains blocked.
- Durable memory remains unchanged; no cross-session memory candidate is promoted from this remediation architecture checkpoint.

### 2026-08-31 Engine Public Training Compiler Slice 1B-E Candidate

- Slice 1B-E is a provisional three-file engine candidate pending independent audit:
  - `synaptic-tuner/synaptic_tuner/api/v1/training.py`
  - `synaptic-tuner/synaptic_tuner/api/v1/__init__.py`
  - `synaptic-tuner/tests/contract/test_public_training_api_v1.py`
- The public API adds `compile_training_plan_v1` with exact public training input/context values and a public resolver protocol; callers do not construct private services or registries.
- Internally, the compiler builds the canonical document and default registry, then uses `TrainingService` for the load, resolve, and plan sequence.
- It returns the exact public `TrainingPlan` and eagerly evaluates its fingerprint before returning, so deferred malformed state cannot cross the public boundary.
- The package export is lazy and preserves the import-light `synaptic_tuner.api.v1` facade.
- Candidate evidence: focused public-contract selection **27 passed**; adjacent selection **198 passed**; compile and `git diff --check` passed.
- The existing whole-file Black baseline remains red and unchanged; this candidate did not widen formatting scope or claim that baseline as repaired.
- No files were staged or committed, and no Host change, provider call, database/publication effect, credential use, network access, paid job, or model execution occurred.
- This candidate must pass a fresh independent public-boundary/security audit before commit/push, Host gitlink update, or Host provenance remediation may proceed.
- Durable memory remains unchanged; no cross-session memory candidate is promoted from this provisional compiler handoff.

### 2026-08-31 Engine Public Training Compiler Independent Audit FAIL

- Independent audit verdict is **FAIL** on one **HIGH** public-boundary issue.
- Runtime `Protocol` `isinstance` validation can invoke a hostile resolver's `__getattr__` on Python 3.10 and 3.11 before the intended resolver call. Both public `compile_training_plan_v1` and internal `TrainingService` repeat this unsafe dynamic check.
- Current Python 3.12 coverage does not reproduce the older-runtime behavior and therefore masks the supported-version defect.
- Other audited properties remain sound: public API shape, lazy/import-light facade, canonical load/resolve/plan composition, exact `TrainingPlan` return, and eager fingerprint validation.
- Required remediation is static, side-effect-free resolver validation plus a concrete safe adapter, or an equivalent construction that performs no pre-call dynamic attribute lookup on caller objects.
- Add hostile regressions under Python 3.10 and Python 3.11 proving `__getattr__` is not invoked during admission/validation, then rerun focused tests and the independent audit.
- The three-file compiler candidate remains unreleased. Commit/push, Host gitlink update, and Host provenance remediation remain blocked pending that fix and re-audit.
- Durable memory remains unchanged; no cross-session memory candidate is promoted from this failed compiler audit.

### 2026-08-31 Engine Public Training Compiler Resolver Remediation Candidate

- Resolver admission now uses static class-method validation and an engine-owned safe adapter; caller objects are no longer subjected to runtime `Protocol` `isinstance` checks.
- Hostile descriptors, dynamic `__getattr__`, and instance-level method substitutions are rejected without invocation. After successful admission, the safe adapter makes exactly one deliberate resolver call.
- Python 3.12 evidence: focused selection **31 passed**; combined relevant selection **202 passed**.
- A dependency-free exact-source adapter probe passed under Python **3.11.9**, including hostile dynamic/descriptor cases. Python 3.10 was unavailable in the current environment and remains an explicit cross-version verification residual.
- Compile and `git diff --check` passed.
- No files were staged or committed, and no Host change, provider call, database/publication effect, credential use, network access, paid job, or model execution occurred.
- The three-file compiler candidate remains provisional pending fresh independent re-audit; commit/push and Host provenance remediation remain blocked until PASS.
- Durable memory remains unchanged; no cross-session memory candidate is promoted from this resolver-remediation handoff.

### 2026-08-31 Engine Public Training Compiler Final Independent Audit PASS

- Final independent audit verdict is **PASS** with no remaining compiler-slice blocker.
- Python 3.11 hostile resolver probes caused zero dynamic `__getattr__` or descriptor calls during validation/admission.
- The engine-owned safe adapter preserves the private `TrainingService` boundary, and a valid resolver receives exactly one legitimate call after successful admission.
- Independent evidence: compiler-focused selection **10 passed**; full public contract selection **31 passed**; the import-light probe produced empty output; `git diff --check` passed.
- The exact three-file public compiler slice is release-ready. Commit/push and the subsequent Host gitlink update may proceed before Host provenance remediation resumes.
- No commit, staging, Host change, provider call, database/publication effect, credential use, network access, paid job, or model execution occurred during this read-only audit.
- Durable memory remains unchanged; no cross-session memory candidate is promoted from this final compiler audit checkpoint.

### 2026-08-31 Engine Public Training Compiler Released

- The public compiler slice was committed in the engine as `d203ea71cbb9287b1aad87b2bb3011728d73a5f6` with message `Expose canonical public training compiler`.
- The release contains exactly three engine files:
  - `synaptic-tuner/synaptic_tuner/api/v1/__init__.py`
  - `synaptic-tuner/synaptic_tuner/api/v1/training.py`
  - `synaptic-tuner/tests/contract/test_public_training_api_v1.py`
- Commit `d203ea71cbb9287b1aad87b2bb3011728d73a5f6` was pushed to the engine feature branch on origin; local/origin parity is **0 ahead / 0 behind**.
- Engine tracked state is clean. Existing untracked test/residue directories were preserved and are not part of the release.
- The Host index was untouched. Its cumulative engine gitlink movement from `42833b5a` to `d203ea71` remains intentionally unstaged for the Host provenance checkpoint.
- Existing `.codex/pact` modifications and all unrelated Host/WSL residue were preserved.
- Host provenance remediation is now unblocked and may consume the released public compiler and cumulative engine gitlink update.
- Durable memory remains unchanged; no cross-session memory candidate is promoted from this routine release checkpoint.

### 2026-08-31 Host Docker Provenance Remediation Candidate

- The remediated Host candidate changes exactly nine files:
  - `synaptic_host/docker_provider.py`
  - `synaptic_host/docker_training.py`
  - `training/providers/docker.json`
  - `synaptic_host/artifact_destinations.py`
  - `synaptic_host/cli.py`
  - `synaptic_host/__main__.py`
  - `tests/synaptic_host/test_docker_training.py`
  - `tests/synaptic_host/test_cli.py`
  - `tests/synaptic_host/test_cold_bootstrap.py`
- Admission binds the exact project and engine roots and requires both repositories clean and pushed, the superproject gitlink equal to the engine commit, and the expected upstream relationships.
- Provider profile, destination configuration, dataset, and bound configuration are read from exact committed Git blobs rather than mutable working-tree files.
- The resulting `SourceLock` contains exactly nine closed configuration keys and four closed inputs binding the provider, destination, ingress, dataset, roots, commits, gitlink, configuration bytes, and provenance evidence.
- Provenance authority is process-local, single-use, and admission-only. It authorizes one exact call through public `compile_training_plan_v1`, producing the exact canonical public `TrainingPlan` without becoming durable execution authority.
- Private `tuner.training` imports, manual registry construction, coerced clean/pushed flags, temporary HMAC source authority, mutable working-tree dataset reads, and the fake-resolver trust-boundary test were removed.
- A real positive test builds clean temporary superproject and engine repositories with local bare remotes, pushed commits, an exact gitlink, committed configuration blobs, and verified upstreams.
- Unsupported admission remains fail-before-effects with zero Docker, SQLite, spool/publication, timestamp, or other durable mutation.
- Candidate evidence: focused/adjacent selection **196 passed, 1 skipped**; full Host **1716 passed, 20 skipped**; `git diff --check` passed.
- No files were staged or committed. The cumulative engine gitlink update to released compiler commit `d203ea71` remains intentionally unstaged for the eventual Host checkpoint.
- This candidate is provisional pending fresh independent provenance/security audit; Docker execution Slice 1C remains blocked.
- Durable memory remains unchanged; no cross-session memory candidate is promoted from this provisional Host remediation handoff.

### 2026-08-31 Host Docker Provenance Re-audit HALT and imPACT Recovery

- Re-audit confirms genuine candidate closures: coerced clean/pushed flags, temporary HMAC authority, private engine planning imports/manual registry, mutable working-tree dataset reads, and fake-resolver trust testing were removed; canonical public planning and fail-before-effects behavior remain intact.
- Release verdict remains **HALT** because the replacement provenance design still has architectural blockers:
  - It requires impossible/self-referential mutable engine self-authentication before the trusted engine code needed to authenticate it can execute.
  - Its random evidence tag is not authenticated and cannot remain independently verifiable for the evidence lifetime.
  - The proposed nine-key configuration lock is incompatible with the canonical five-key provenance validator.
  - Git blob capture is unbounded and can consume attacker-controlled committed content before admission.
  - The positive proof does not exercise the real outer dispatch boundary.
- imPACT classification: **upstream architecture defect plus scope mismatch**, not an isolated coder defect.
- Recovery requires a fresh Architect pass with a corrected trust boundary: the installed Host and installed engine are the local trusted computing base; admission authenticates the user project, committed configuration/dataset, provider selection, and resulting provider effects rather than asking mutable project state to authenticate the executing engine itself.
- Admission evidence must remain verifiable for its full lifetime, the canonical five-key provenance schema must be preserved, and every committed-blob read must be explicitly bounded before allocation/decoding.
- The renewed architecture must include a real positive outer-dispatch proof and retain the already-closed canonical-plan and zero-effect admission properties.
- Replace the prior Architect for this redo because the current approach has looped into an overconstrained/self-referential design. No user decision is required at this stage.
- No remediation, release, commit, staging, provider call, database/publication effect, network access, credential use, paid job, or model execution is authorized until the replacement architecture is accepted.
- The current Host candidate remains owned but paused; Slice 1C remains blocked.
- Durable memory remains unchanged; no cross-session memory candidate is promoted from this imPACT recovery checkpoint.

### 2026-08-31 Host Docker Provenance imPACT Architecture Redo Accepted

- The installed Host and installed engine are the trusted local computing base. Provenance admission authenticates user-controlled project state, committed configuration/dataset bytes, Docker descriptors, and resulting provider effects; it does not require mutable project state to self-authenticate the executing engine.
- Preserve the valid candidate core: canonical public `TrainingPlan` compilation, exact project/engine/gitlink/upstream inspection, committed-blob inputs, strict final destination, closed capability results, and fail-before-effects behavior.
- `SourceLock.configuration` remains the canonical five-key structure. Docker provider, destination, ingress, dataset, and related descriptors belong in the existing generic provenance/input sections rather than widening that closed configuration schema.
- Each admission creates a live, process-local, one-shot HMAC session. The public compiler receives evidence tied to that session, and Host verifies the returned evidence again after compilation before accepting the plan; the session is then consumed and cannot be replayed.
- Repository/source inspection and clean/pushed/gitlink/upstream validation occur before committed provider, destination, ingress, or dataset descriptors are loaded.
- Committed Git blobs are read through a bounded `Popen`-based reader with an exact **64 MiB** maximum, closed subprocess status handling, and fail-before-decode behavior for overflow or read failure.
- Required positive proof enters through the real outer `synaptic_host.__main__` dispatch using temporary clean superproject/engine repositories, local bare remotes, exact pushed gitlink, and committed descriptors; it may not bypass CLI/bootstrap composition.
- The current stale/dirty Host worktree must continue to return `RESOLUTION_UNAVAILABLE` and is not normalized into an eligible source.
- A successful, fully authenticated admission still returns `CAPABILITY_UNSUPPORTED` because the current Docker profile supports no training method, and it must produce zero Docker, SQLite, spool/publication, timestamp, or other durable effects.
- Corrections remain bounded to the existing nine-file Host candidate: remove self-referential engine authentication and the unauthenticated random tag, restore the five-key lock, add the bounded blob reader and post-compiler live-session verification, and replace the bypassing positive test with the outer-dispatch proof.
- Release gates: focused hostile provenance/session/blob tests, real outer-dispatch positive and negative cases, full Host regression, independent provenance/security re-audit, exact cumulative engine gitlink inclusion, then commit/push/parity. Slice 1C remains blocked until PASS.
- Durable memory remains unchanged; no cross-session memory candidate is promoted from this replacement architecture checkpoint.

### 2026-08-31 Host Docker Provenance Corrected Candidate

- Source/repository proof completes before committed descriptors are loaded, and the exact bound configuration is revalidated after reads and before compilation/admission succeeds.
- `SourceLock.configuration` uses the canonical five keys; Docker provider, destination, ingress, dataset, and related identities remain in the generic provenance/input descriptors.
- Admission uses a live process-local one-use HMAC session. The returned compiler evidence is checked post-compiler through the released validator, the session is consumed exactly once, and secret/session material is wiped on success and failure paths.
- Committed blobs use bounded `Popen` readers with exact per-blob and aggregate caps, closed exit-status/error handling, and fail-before-decode overflow behavior.
- The current profile always resolves honest `CAPABILITY_UNSUPPORTED`; no code path claims Docker SFT readiness.
- A real positive proof enters through outer `synaptic_host.__main__` using only project/engine roots and local-remote transport, with committed descriptors discovered through the trusted composition rather than injected test objects.
- The dirty/stale outer-dispatch case returns `RESOLUTION_UNAVAILABLE`.
- Both successful unsupported admission and failed resolution produce zero Docker, SQLite, spool/publication, timestamp, or other durable effects.
- Candidate evidence: full Host **1720 passed, 20 skipped**; `git diff --check` passed.
- No files were staged or committed, the cumulative engine gitlink remains unstaged, and no provider call, credential use, network access, paid job, publication effect, or model execution occurred.
- The corrected nine-file Host candidate remains provisional pending fresh independent provenance/security audit. Slice 1C remains blocked.
- Durable memory remains unchanged; no cross-session memory candidate is promoted from this corrected candidate handoff.

### 2026-08-31 Host Docker Provenance Final Audit — Fixture Blocker

- Static/runtime audit returns **PASS** with no new product or runtime finding.
- Focused verification produced **195 passed, 1 skipped, 5 setup errors**.
- The setup defect is confined to the test fixture: it attempts to clone the engine into `base/project/synaptic-tuner` before creating the parent `base/project` directory.
- Consequently, five real clean-superproject/provenance-boundary tests did not execute, so their intended evidence cannot be credited yet.
- The single authorized fix is to create the parent project directory before the clone; no runtime or production change is required.
- After that fixture correction, rerun all five blocked boundary tests, the focused provenance selection, and the full Host suite before final release assessment.
- Release and Slice 1C remain blocked only on corrected fixture execution and completed independent verification; there is currently no unresolved runtime audit finding.
- Durable memory remains unchanged; no cross-session memory candidate is promoted from this test-fixture checkpoint.

### 2026-08-31 Host Docker Provenance Fixture Remediation Candidate

- The test fixture now creates the parent project directory before cloning the engine into it; no production or runtime file changed for this correction.
- All **5 previously blocked tests passed**.
- Focused provenance selection: **200 passed, 1 skipped**.
- Full Host regression: **1720 passed, 20 skipped**.
- `git diff --check` passed.
- The corrected Host candidate remains provisional pending final independent re-audit; no commit, staging, provider call, database/publication effect, network access, credential use, paid job, or model execution occurred.
- Durable memory remains unchanged; no cross-session memory candidate is promoted from this fixture-remediation handoff.

### 2026-08-31 Host Docker Admission Slice 1B Final Independent PASS

- Final independent audit/verifier verdict is **PASS** with no remaining finding.
- The fixture parent-order defect is fixed, and all **5 clean-superproject/provenance-boundary tests passed**.
- Final focused evidence: **200 passed, 1 skipped**. Accepted full Host evidence: **1720 passed, 20 skipped**.
- Real outer clean dispatch returns honest `CAPABILITY_UNSUPPORTED`; dirty/stale outer dispatch returns `RESOLUTION_UNAVAILABLE`.
- Provenance uses the canonical five-key configuration, exact committed descriptors, post-compiler live one-use HMAC verification, consumed/wiped session authority, and zero Docker, SQLite, spool/publication, timestamp, or other durable effects.
- The release checkpoint must include engine gitlink `d203ea71` plus exactly these nine Host files:
  - `synaptic_host/docker_provider.py`
  - `synaptic_host/docker_training.py`
  - `training/providers/docker.json`
  - `synaptic_host/artifact_destinations.py`
  - `synaptic_host/cli.py`
  - `synaptic_host/__main__.py`
  - `tests/synaptic_host/test_docker_training.py`
  - `tests/synaptic_host/test_cli.py`
  - `tests/synaptic_host/test_cold_bootstrap.py`
- Slice 1B is release-ready. The only noted environmental constraint is long Windows temporary-path handling for nested Git fixture repositories; it is not a product or security blocker.
- No commit, staging, provider call, database/publication effect, network access, credential use, paid job, or model execution occurred during the final read-only gate.
- Durable memory remains unchanged; no cross-session memory candidate is promoted from this final Slice 1B checkpoint.

### 2026-08-31 Host Docker Admission Slice 1B Released

- Host Slice 1B was committed as `af0b6efa17e0b32d19551af591eb213dd1d031a7` with message `Add canonical Docker training admission`.
- The release contains exactly ten paths: engine gitlink `synaptic-tuner` at `d203ea71` plus nine Host files:
  - `synaptic_host/docker_provider.py`
  - `synaptic_host/docker_training.py`
  - `training/providers/docker.json`
  - `synaptic_host/artifact_destinations.py`
  - `synaptic_host/cli.py`
  - `synaptic_host/__main__.py`
  - `tests/synaptic_host/test_docker_training.py`
  - `tests/synaptic_host/test_cli.py`
  - `tests/synaptic_host/test_cold_bootstrap.py`
- Commit `af0b6efa17e0b32d19551af591eb213dd1d031a7` was pushed to the Host feature branch on origin; local/origin parity is **0 ahead / 0 behind**.
- Engine tracked state is clean at released compiler commit `d203ea71`; existing engine test residue remains preserved and uncommitted.
- Existing `.codex/pact` modifications, Host test residue, and the two unrelated WSL manifest changes remain preserved outside this checkpoint.
- Tests were not rerun during release. Accepted final gates remain **200 passed, 1 skipped** focused and **1720 passed, 20 skipped** full Host.
- Slice 1B release is complete. The next phase is Slice 2 architecture/implementation for durable Docker GPU execution and a canonical public SFT smoke; no GPU/model/provider execution is authorized by this release record alone.
- Durable memory remains unchanged; no cross-session memory candidate is promoted from this routine release checkpoint.

### 2026-08-31 Docker GPU Execution Slice 2 PREPARE Accepted

- The fastest honest Slice 2 path is a single cached proof using the exact locally cached Unsloth image and the exact cached SmolLM2-1.7B model revision/inventory; those immutable identifiers and inventories must be frozen before CODE.
- Runtime layout uses exactly two host binds: `/source` is read-only and contains the trusted installed engine plus cached model/dataset inputs; `/artifacts` is the only writable output root.
- The worker receives a sealed file-backed `WorkerInvocationV1`; no caller argv, shell command, mutable plan, or ambient workload transport becomes execution authority.
- Host owns durable preparation and project-level SQLite lifecycle state before Docker mutation. The engine and container own no lifecycle database.
- Docker capability must expose typed GPU device-0 create and inspect evidence, including exact device request and post-create verification, before the profile can advertise SFT readiness.
- Container identity, command, mounts, image, GPU request, and preparation identity must be deterministic and durably bound so restart recovery is lookup/reconcile only rather than a second create.
- Slice 2 must add concrete read/Runs lifecycle surfaces, authenticated artifact verification, and publication through the already released Host destination composition.
- Reuse the proven low-level Docker facade, sealed bundle/runtime mechanics, Host SQLite lifecycle, artifact spool, and publication pipeline. Do not rebuild those layers.
- Retire the legacy same-process Docker planning/execution path after canonical callers migrate; do not preserve it through adapters or aliases.
- A general model downloader, dynamic image acquisition system, multi-model registry, cloud/provider execution, or broad GPU scheduler is outside this minimal proof.
- Eight minimal implementation slices for Architect to freeze:
  1. Exact cached-image/model/profile capability and immutable inventory contract.
  2. Two-bind source/artifact layout plus sealed file-backed invocation staging.
  3. Typed Docker GPU device-0 create/inspect and deterministic identity contract.
  4. Durable Host preparation/SQLite command binding and one-create admission.
  5. Submit, observe, restart lookup, and deterministic reconciliation lifecycle.
  6. Concrete public Runs/read/log/status surfaces over persisted state.
  7. Exact artifact verification, lineage, spool handoff, and configured publication.
  8. Cached offline one-step public SFT smoke, independent security/test gates, release, and legacy-path removal.
- Current blockers for Architect: freeze the exact cached image identity and SmolLM2 revision/inventory; prove the cached runtime can consume the two-bind contract without network; bind GPU create/inspect semantics to lifecycle recovery; define exact preparation/store/read composition and final smoke acceptance inventory.
- No Docker mutation, GPU/model execution, provider/network call, credential use, paid job, publication effect, CODE, or test mutation is authorized by this PREPARE checkpoint.
- Durable memory remains unchanged; no cross-session memory candidate is promoted from this preparation handoff.

### 2026-08-31 Docker GPU Execution Slice 2 ARCHITECT Accepted

- Slice 2 is frozen into three sequential implementation/release slices; each requires its own independent barrier before the next consumes it.
- **Slice 2A — engine worker:** define the engine-owned durable worker bundle, authenticated local model/dataset snapshot descriptors, sealed `WorkerInvocationV1` file transport, and a fully offline canonical SFT worker path under the provider-neutral runtime contract.
- **Slice 2B — Host Docker lifecycle:** add typed GPU create/inspect evidence, SQLite schema v2 provider-preparation/control records, exact two-bind staging (`/source` read-only and `/artifacts` writable), deterministic create/lookup/observe/reconcile, concrete Runs/read/inventory surfaces, semantic verification, and configured Host publication.
- **Slice 2C — capability and smoke:** freeze the exact Docker profile and cached image/model/tokenizer/dataset inventory, prove every immutable cache identity, enable the method only after all offline/security/recovery gates pass, and run one bounded canonical public SFT smoke.
- Canonical data flow is one-way: public request -> canonical plan -> durable Host preparation/command -> sealed worker bundle and local snapshot -> one admitted Docker create -> observe/reconcile -> authenticated artifact inventory -> semantic `VERIFIED` -> Host spool and configured publication -> public outcome.
- The required terminal SFT artifact inventory is exactly one each of `workload_record`, `lineage`, `metrics`, `final_adapter`, and `tokenizer`; missing, duplicate, unknown, aliased, unbounded, or unauthenticated entries fail verification.
- SQLite evolution is a one-way provider-preparations migration to schema v2. It must refuse partial/newer/unknown schema states and cannot silently downgrade, rewrite history, or recreate live authority from persisted data.
- Restart/crash cuts are explicit: before durable prepare means no run/effect; after prepare but before admitted create means closed not-submitted/recoverable preparation; after admitted create begins means lookup-only reconciliation; unknown create outcome never retries; provider completion enters verification rather than success; publication failure cannot rewrite training success but remains a closed publication outcome.
- Profile/method enablement is prohibited until typed GPU inspection, cache identities, offline worker execution, SQLite/reconciliation, artifact verification, redaction/bounds, publication, full regressions, and independent security/release gates all pass.
- Publication occurs only after semantic `VERIFIED`; Docker terminal/completed state alone never authorizes publication or `SUCCEEDED`.
- Deferred beyond this slice: general model downloading, online dependency resolution, multiple models/methods/GPUs, scheduling, cloud providers, distributed training, arbitrary mounts, public provider staging, legacy adapters, and paid execution.
- Current hard blocker for Slice 2C is missing authoritative evidence for the cache root and seven required cached-file hashes. These exact roots/hashes must be discovered and frozen read-only before capability enablement or smoke authorization; no values may be guessed or derived from mutable tags alone.
- Next dispatch is Slice 2A engine CODE. Slice 2B and 2C remain blocked on earlier slice acceptance; no Docker/GPU/model/provider effect is authorized by this architecture checkpoint.
- Durable memory remains unchanged; no cross-session memory candidate is promoted from this accepted Slice 2 architecture.

### 2026-08-31 Docker GPU Execution Slice 2A Engine Candidate

- Slice 2A is a provisional 15-file engine candidate pending independent audit:
  - `synaptic-tuner/tuner/runtime/dispatch.py`
  - `synaptic-tuner/tuner/runtime/__init__.py`
  - `synaptic-tuner/tuner/runtime/verification.py`
  - `synaptic-tuner/tuner/training/methods/sft.py`
  - `synaptic-tuner/Trainers/sft/runtime_v1.py`
  - `synaptic-tuner/Trainers/sft/train_sft.py`
  - `synaptic-tuner/Trainers/sft/src/model_loader.py`
  - `synaptic-tuner/schemas/synaptic-sft-workload-v1.schema.json`
  - `synaptic-tuner/tuner/execution/providers/modal/modal-runtime-v1.lock.json`
  - `synaptic-tuner/tests/runtime/test_dispatch.py`
  - `synaptic-tuner/tests/runtime/test_artifact_verification.py`
  - `synaptic-tuner/tests/trainers/sft/test_runtime_v1.py`
  - `synaptic-tuner/tests/trainers/sft/test_model_revision.py`
  - `synaptic-tuner/tests/trainers/sft/test_train_sft_source.py`
  - `synaptic-tuner/tests/training/test_sft_compilation.py`
- The candidate introduces `WorkerBundleMaterialization` as the closed output of worker-bundle staging and binds its sealed invocation, source layout, snapshot inventory, and artifact destination contract.
- Model/tokenizer/dataset inputs are derived from the authenticated local snapshot; there is no network, mutable-revision, ambient-cache, or legacy loader fallback when the snapshot contract is selected.
- The SFT worker runs under a closed offline environment and the verifier/schema enforce the exact runtime, snapshot, workload, lineage, and five-artifact bindings before semantic success.
- The exact provider-neutral runtime lock hash is `da1f0f0717a970486fa19ab2df44826c93aae5db86797cc052890c30ac2ace83`.
- Candidate evidence: focused/direct selection **190 passed, 15 skipped**; Modal-adjacent selection **21 passed**; real Linux selection **9 passed, 94 deselected**.
- Compile, Black, and `git diff --check` passed for the candidate scope.
- An unrelated pre-existing lock-baseline mismatch remains outside Slice 2A and was not changed or claimed as fixed.
- No Host files, commits, staging, Docker/GPU/model execution, provider/network calls, credentials, paid jobs, database mutations, or publication effects occurred.
- The coder retains ownership of these 15 files for possible remediation. Slice 2A is not release-ready until fresh independent contract/security audit; Slice 2B remains blocked.
- Durable memory remains unchanged; no cross-session memory candidate is promoted from this provisional Slice 2A handoff.

### 2026-09-01 Docker GPU Execution Slice 2A Independent Audit PASS

- Accepted independent audit verdict is **PASS** with no findings for the exact 15-file Slice 2A candidate.
- `WorkerBundleMaterialization` is factory-only and Host-path-free; no caller-constructed bundle or Host filesystem identity becomes engine execution authority.
- Canonical workload bytes are bound consistently for both byte-backed and file-backed transports.
- Local snapshot materialization derives only from the locked cache/model/revision inventory and enforces containment, link/reparse refusal, regular-file identity, and no fallback to ambient cache, network, or legacy loaders.
- Offline environment controls, runtime verifier, and SFT schema are aligned with the same snapshot/workload/runtime/artifact contract.
- The exact Modal runtime-lock hash is `da1f0f0717a970486fa19ab2df44826c93aae5db86797cc052890c30ac2ace83`.
- Accepted checks: focused/direct **190 passed, 15 skipped**; Modal-adjacent **21 passed**; Python 3.10 grammar checks for **13 changed files passed**; compile and `git diff --check` passed.
- Boundary evidence confirms exactly **15 tracked files**, with **633 insertions and 9 deletions**.
- Audit limitations are explicit: native Python 3.10 execution and the Linux **9 passed, 94 deselected** selection were not independently rerun by this auditor; the previously supplied evidence remains recorded but is not misrepresented as an independent rerun.
- Release decision is **PASS**. The exact 15-file engine candidate is release-ready, and Slice 2B may begin only after its engine commit/push/parity checkpoint.
- Durable memory remains unchanged; no cross-session memory candidate is promoted from this accepted audit checkpoint.

### 2026-09-01 Docker GPU Execution Slice 2A Released

- Slice 2A was committed in the engine as `c272b8340ebf5edcb61c45a789c81632bf0be262` with message `Add offline SFT worker bundle`.
- The release contains exactly the 15 approved engine files:
  - `synaptic-tuner/tuner/runtime/dispatch.py`
  - `synaptic-tuner/tuner/runtime/__init__.py`
  - `synaptic-tuner/tuner/runtime/verification.py`
  - `synaptic-tuner/tuner/training/methods/sft.py`
  - `synaptic-tuner/Trainers/sft/runtime_v1.py`
  - `synaptic-tuner/Trainers/sft/train_sft.py`
  - `synaptic-tuner/Trainers/sft/src/model_loader.py`
  - `synaptic-tuner/schemas/synaptic-sft-workload-v1.schema.json`
  - `synaptic-tuner/tuner/execution/providers/modal/modal-runtime-v1.lock.json`
  - `synaptic-tuner/tests/runtime/test_dispatch.py`
  - `synaptic-tuner/tests/runtime/test_artifact_verification.py`
  - `synaptic-tuner/tests/trainers/sft/test_runtime_v1.py`
  - `synaptic-tuner/tests/trainers/sft/test_model_revision.py`
  - `synaptic-tuner/tests/trainers/sft/test_train_sft_source.py`
  - `synaptic-tuner/tests/training/test_sft_compilation.py`
- Commit statistics are **633 insertions and 9 deletions**.
- Commit `c272b8340ebf5edcb61c45a789c81632bf0be262` was pushed normally to `origin/feat/submodule-cloud-api-v1`; local/origin parity is **0 ahead / 0 behind**.
- Engine tracked state is clean. Existing untracked engine test/residue directories remain preserved outside the release.
- Host `HEAD` remains `af0b6efa17e0b32d19551af591eb213dd1d031a7`, the Host index remains empty, and the engine gitlink movement to `c272b834` remains intentionally unstaged for the later Host Slice 2B checkpoint.
- Existing `.codex/pact` modifications and all unrelated Host/WSL/test residue remain preserved.
- Tests were not rerun during release; the accepted independent Slice 2A PASS evidence remains authoritative.
- Slice 2A release is complete. The next dispatch is the user-approved smoke-first narrowed Slice 2B Host durable GPU vertical path; no Docker/GPU/model/provider effect is authorized by this release record alone.
- Durable memory remains unchanged; no cross-session memory candidate is promoted from this routine release checkpoint.

### 2026-09-01 Smoke-First Docker GPU Slice 2B ARCHITECT Accepted

- The smoke-first durable design introduces exactly two new durable record/table types: `ProviderPreparationRecordV1` and `DockerRunMutationRecordV1`; no general provider-state model is authorized.
- Host SQLite evolves additively from v1 to v2, preserving all existing publication and Modal/provider rows and refusing partial, newer, or incompatible schema states.
- Runtime staging uses exactly two mounts: `/source` read-only and `/artifacts` writable. A new Host source-staging boundary prepares the sealed worker bundle and authenticated snapshot without exposing arbitrary mounts.
- Device intent is a typed provider-neutral request. The Docker boundary translates it to an NVIDIA request for device 0 and must inspect the created container to prove that exact device assignment.
- Execution is synchronous and deterministic for this vertical slice: one durable preparation, one admitted container create/start, bounded observation, and lookup-only reconciliation on restart or ambiguous mutation outcome.
- Terminal verification requires exactly one each of `workload_record`, `lineage`, `metrics`, `final_adapter`, and `tokenizer`; Docker completion alone is not success.
- Publication uses a narrow one-run adapter and occurs only after semantic `VERIFIED`; an identical replay must converge on the same durable run/publication without a second container or duplicate publication.
- Implementation is bounded to at most two CODE slices plus smoke configuration:
  1. Typed GPU request/inspection in the engine-facing and low-level Host Docker boundaries.
  2. Host durable preparation/mutation executor, source staging, reconciliation, exact verification, and one-run publication composition.
  3. Configuration-only cached profile/inventory and the real smoke gate.
- Explicitly deferred: general public Runs/supervisor services, model downloader, multi-GPU scheduling, cloud providers, broad lifecycle abstraction, arbitrary mounts, and legacy same-process path deletion.
- The first blocking action is mechanical: commit and push the Host gitlink update to released engine `c272b834` and verify Host parity before either CODE slice begins.
- Real acceptance requires a clean canonical WSL checkout, exact cached image/model/dataset inventory, offline GPU device-0 execution, exact five-artifact verification/publication, and an identical rerun proving no duplicate create or publication.
- Architect is complete/read-only; no writer is active. After the gitlink checkpoint, dispatch CODE Slice 1, independently gate it, then CODE Slice 2 and smoke configuration.
- No Docker/GPU/model/provider mutation, CODE, test change, commit, staging, credential use, network call, paid job, or publication effect is authorized by this architecture checkpoint itself.
- Durable memory remains unchanged; no cross-session memory candidate is promoted from this accepted Slice 2B architecture.

### 2026-09-01 Host Gitlink Checkpoint for Slice 2B Released

- Host advanced from `af0b6efa17e0b32d19551af591eb213dd1d031a7` to `e992106e` in an exact one-path release commit.
- The only committed path is `synaptic-tuner`, recorded as Git mode `160000`.
- The engine gitlink moved from `d203ea71` to released Slice 2A engine `c272b834`.
- The Host commit was pushed normally to its origin feature branch; local/origin parity is **0 ahead / 0 behind**.
- The Host index is empty after release.
- Existing `.codex/pact` modifications, test residue, engine residue, and unrelated WSL manifest state remain preserved outside the commit.
- No source, test, configuration, provider, Docker, database, publication, credential, network, paid-job, or model-execution change was included; this checkpoint contains no path other than the gitlink.
- The mechanical Slice 2B prerequisite is complete. CODE Slice 1 for typed GPU request/inspection may now begin under the accepted architecture.
- Durable memory remains unchanged; no cross-session memory candidate is promoted from this routine gitlink checkpoint.

### 2026-09-01 Docker GPU Slice 2B.1A Engine Independent Audit PASS

- Independent audit verdict is **PASS** for exactly seven engine files:
  - `synaptic-tuner/tuner/execution/providers/docker_provider_v1/model.py`
  - `synaptic-tuner/synaptic_tuner/api/v1/training.py`
  - `synaptic-tuner/synaptic_tuner/api/v1/__init__.py`
  - `synaptic-tuner/tests/execution/providers/docker_provider_v1/conftest.py`
  - `synaptic-tuner/tests/execution/providers/docker_provider_v1/test_model.py`
  - `synaptic-tuner/tests/contract/test_public_training_api_v1.py`
  - `synaptic-tuner/tests/contract/fixtures/api_v1_formal_exports_pre_b1.json`
- The candidate adds typed immutable `AcceleratorDeviceRequestV1` with closed `kind`, ordered device indices, ordered capabilities, and a computed canonical digest binding every field.
- Docker accelerator policy is explicit and closed: CPU, or exact NVIDIA device index `0` with capability `gpu`; every other kind/index/capability combination fails admission.
- Legacy `gpu_enabled` is removed without an alias, adapter, fallback, or compatibility shim.
- Hostile mutation, reconstructed/subclass values, bool/int confusion, noncanonical ordering, duplicates, and digest substitution fail closed.
- The stale public compiler export fixture was repaired to match the accepted public surface.
- Independent exact verification result: **592 passed**. `git diff --check` is clean.
- The exact seven-file Slice 2B.1A engine candidate is release-ready; no Host, Docker/GPU/provider, database, publication, credential, network, paid-job, or model-execution effect occurred during the audit.
- Durable memory remains unchanged; no cross-session memory candidate is promoted from this accepted Slice 2B.1A audit.

### 2026-09-01 Docker GPU Slice 2B.1A Engine and Host Releases

- Engine advanced from `c272b834` to `3198867f` in commit `Add typed Docker accelerator request`.
- The engine release contains exactly the seven audited paths:
  - `synaptic-tuner/tuner/execution/providers/docker_provider_v1/model.py`
  - `synaptic-tuner/synaptic_tuner/api/v1/training.py`
  - `synaptic-tuner/synaptic_tuner/api/v1/__init__.py`
  - `synaptic-tuner/tests/execution/providers/docker_provider_v1/conftest.py`
  - `synaptic-tuner/tests/execution/providers/docker_provider_v1/test_model.py`
  - `synaptic-tuner/tests/contract/test_public_training_api_v1.py`
  - `synaptic-tuner/tests/contract/fixtures/api_v1_formal_exports_pre_b1.json`
- The engine commit was pushed normally to its origin feature branch; local/origin parity is **0 ahead / 0 behind** and the engine index is clean.
- Host advanced from `e992106e` to `59b8d72d` in commit `Advance engine for typed Docker accelerator`.
- The Host release contains exactly one path, `synaptic-tuner`, mode `160000`; its gitlink moved from `c272b834` to released engine `3198867f`.
- The Host commit was pushed normally to its origin feature branch; local/origin parity is **0 ahead / 0 behind** and the Host index is clean.
- Existing `.codex/pact` modifications, engine/Host test residue, and unrelated WSL state remain preserved outside both commits.
- No other path, Docker/GPU/provider action, database/publication effect, credential use, network call, paid job, or model execution was included in these release operations.
- Slice 2B.1A release is complete. Slice 2B.1B Host low-level typed GPU translation/inspection mechanics are ready for CODE.
- Durable memory remains unchanged; no cross-session memory candidate is promoted from this routine paired-release checkpoint.

### 2026-09-01 Docker GPU Slice 2B.1B Audit PASS and Controlled Diagnostic

- The initial GPU-inspection audit **HALT** is closed. Docker creation now uses explicit `--gpus driver=nvidia,device=0`, and product inspection requires the exact accepted five-field device-request shape with `Count=0` rather than treating the count field as an allocation quantity.
- The named-context audit **HALT** was traced to a deliberately stripped Docker configuration. It is closed through an exact authenticated Docker endpoint descriptor/resolver and explicit `--host`; runtime behavior does not consult ambient Docker configuration or context selection.
- Durable SQLite provider-preparation/mutation persistence is intentionally deferred to Slice 2B.2 and is not claimed by this low-level mechanics slice.
- Independent audit verdict is **PASS** for the full exact **24-file** Slice 2B.1B candidate with no remaining finding.
- Verification evidence: **992 non-real tests passed**; compile, Python 3.10 compatibility, and `git diff --check` are green.
- A controlled `desktop-linux` Docker diagnostic passed with descriptor digest prefix `3484caac…`, policy digest prefix `a1497970…`, and GPU digest prefix `97aeacfb…`.
- The diagnostic used the exact pinned image, performed exactly one stopped-container create, and verified the product inventory and exact GPU inspection contract through the accepted descriptor/resolver path.
- The exact diagnostic container/resource was cleaned afterward; no retained Docker mutation remains from the probe.
- The diagnostic did **not** start the container, execute training or a model, access cloud/provider services beyond the local Docker endpoint, use credentials, perform publication, submit a paid job, or authorize the later smoke.
- Slice 2B.1B low-level typed GPU translation/inspection mechanics are accepted. Slice 2B.2 durable Host preparation/executor/staging/reconciliation/publication remains the next gated implementation slice.
- Durable memory remains unchanged; no cross-session memory candidate is promoted from this accepted diagnostic checkpoint.

### 2026-09-01 Docker GPU Slice 2B.1B Host Released

- Host advanced from `59b8d72d` to `0e948689d8ecdfbf3196f91b08141538b00bae66` in commit `Bind Docker GPU execution to local endpoint`.
- The release contains exactly 24 paths: 22 modified and two new endpoint files:
  - `synaptic_host/docker_v1/cli.py`
  - `synaptic_host/docker_v1/composition.py`
  - `synaptic_host/docker_v1/control.py`
  - `synaptic_host/docker_v1/control_contract.py`
  - `synaptic_host/docker_v1/control_model.py`
  - `synaptic_host/docker_v1/control_private.py`
  - `synaptic_host/docker_v1/create.py`
  - `synaptic_host/docker_v1/endpoint.py` (new)
  - `synaptic_host/docker_v1/model.py`
  - `synaptic_host/docker_v1/mounts.py`
  - `synaptic_host/docker_v1/start.py`
  - `synaptic_host/docker_v1/verification.py`
  - `tests/synaptic_host/docker_v1/conftest.py`
  - `tests/synaptic_host/docker_v1/test_authority.py`
  - `tests/synaptic_host/docker_v1/test_cli.py`
  - `tests/synaptic_host/docker_v1/test_composition.py`
  - `tests/synaptic_host/docker_v1/test_control.py`
  - `tests/synaptic_host/docker_v1/test_control_contract.py`
  - `tests/synaptic_host/docker_v1/test_create.py`
  - `tests/synaptic_host/docker_v1/test_endpoint.py` (new)
  - `tests/synaptic_host/docker_v1/test_interop.py`
  - `tests/synaptic_host/docker_v1/test_mounts.py`
  - `tests/synaptic_host/docker_v1/test_real_docker_wsl.py`
  - `tests/synaptic_host/docker_v1/test_start.py`
- Commit statistics are **896 insertions and 92 deletions**.
- The Host commit was pushed normally to its origin feature branch; local/origin parity is **0 ahead / 0 behind** and the Host index is empty.
- Engine remains unchanged at released commit `3198867f`.
- Existing `.codex/pact` modifications, engine/Host test residue, and unrelated WSL state remain preserved outside the release.
- No other path, Docker start/training action, GPU/model execution, database/publication effect, credential use, network call, cloud action, or paid job was included in the release operation.
- Slice 2B.1 is complete. Slice 2B.2 Host durable vertical executor, source staging, reconciliation, verification, and publication is the next implementation slice.
- Durable memory remains unchanged; no cross-session memory candidate is promoted from this routine Slice 2B.1B release.

### 2026-09-01 Docker GPU Slice 2B.2 Final Architecture GO

- Implementation status is **GO** under this final narrow boundary; no broader lifecycle or provider framework is authorized.
- Durable persistence adds exactly two records/tables: `ProviderPreparationRecordV1` for the immutable, single-consumption prepared command/source binding and `DockerRunMutationRecordV1` for claim-before-effect Docker create/start identity, attempt, observation, and reconciliation state.
- Final phase/state semantics are closed: preparation is durably created before authority can be consumed; mutation is durably claimed and marked attempted before Docker mutation; an admitted create returns public `SUBMITTED`; provider completion remains non-success until exact verification; ambiguous outcomes are lookup-only and never retry create; terminal publication is recorded separately from training outcome.
- Public `SUBMITTED` is a receipt that the exact durable Docker mutation was admitted/attempted. It does not mean the container is running, training completed, artifacts verified, publication succeeded, or the run reached `SUCCEEDED`.
- Host construction uses `manifest.create_context` and the source lock's committed `storage.json`; callers do not inject alternate state, cache, staging, or publication paths after provenance admission.
- Container layout has exactly two roots: `/source` read-only and `/artifacts` writable. Cache/model/tokenizer/dataset inputs are materialized into a run-owned source snapshot beneath the authorized storage capability, authenticated before use, and never borrowed directly from ambient shared cache paths.
- SQLite migration is additive and one-way from v1 to v2, preserves existing publication and provider/Modal rows, fingerprints the exact schema, and refuses partial, unknown, newer, or downgrade states.
- **Slice A ownership:** Host SQLite v2 schema/store plus the two record codecs, atomic prepare/consume and mutation claim/attempt/observation/reconcile operations, migrations, and persistence/concurrency/restart tests. Slice A does not own Docker calls, staging, verification, publication, CLI, or smoke configuration.
- **Slice A gates:** v1 preservation and exact v2 refusal tests; atomic single-consumer/single-attempt concurrency; crash cuts before claim, after claim, and after attempted; lookup-only ambiguity; stale-token/revision rejection; bounded canonical values; no provider call in store tests; full Host regression and independent database/security audit.
- **Slice B ownership:** Host run-owned source/cache materialization, exact two-bind worker staging, synchronous durable executor, typed Docker create/start/inspect/observe adapter, exact five-role verification, one-run public receipt/readback, and configured publication composition with focused integration tests. Slice B consumes Slice A contracts and does not alter their schema.
- **Slice B gates:** zero Docker effects before durable admission; exact command/mount/GPU identity; one create on concurrent/replayed requests; restart reconciliation without retry; exact five artifacts and semantic `VERIFIED` before publication; public `SUBMITTED` semantics; identical replay with no duplicate container/publication; failure cleanup and bounded/redacted errors; full Host regression and independent security/test audit.
- **Slice 2C cache gate:** method enablement and real smoke remain blocked until the exact pinned image, cache root, SmolLM2 model/tokenizer revision, dataset bytes, and every required cached-file hash are frozen and independently verified from the clean WSL checkout.
- Explicitly deferred: general Runs/supervisor services, downloader or cache population, multiple models/methods/GPUs, scheduling, cloud providers, distributed training, arbitrary mounts, legacy same-process deletion, and paid execution.
- Next dispatch is Slice A CODE. Slice B waits for Slice A release; Slice 2C waits for both releases and the cache gate. No Docker/GPU/model/provider effect is authorized by this architecture checkpoint.
- Durable memory remains unchanged; no cross-session memory candidate is promoted from this final Slice 2B.2 architecture.

### 2026-09-01 Docker Slice 2C Activation Release and Agent Handoff Checkpoint

- Host branch `feat/submodule-cloud-api-v1-host` is released and pushed at `5503c5286b99f6b5905efa4b81a562666f0cfdbc`; its parent is `4aede291`, the prepared Docker activation/trust-hardening release. Host local/origin parity is **0 ahead / 0 behind**.
- Engine submodule gitlink, checkout, and engine origin all agree at `aec998ee8d6a2e58d86e19e8132bc59aa21ebd53`; engine local/origin parity is **0 ahead / 0 behind**.
- Released Host commit `4aede291` provides the prepared Docker activation path and trust hardening. Released Host commit `5503c528` adds the native-Windows Host boundary and config-first model inventory.
- Final independent audit verdict is **PASS**. Accepted evidence includes **61 passed / 3 skipped** before remediation, final native-staging verification at **25 passed / 1 skipped**, prepared composition at **11 passed**, and integrated inventory/provider/platform/training verification at **40 passed / 2 skipped**.
- No real Docker container or training run was executed for this release checkpoint.
- Read-only live preflight passed for the explicit Docker Desktop named-pipe endpoint, locally present production and Alpine images, NVIDIA RTX 3090 with 24 GB VRAM, approximately 170 GB free disk, configuration and dataset checks, and absence of a stale target container.
- The exact SmolLM2 snapshot `12fd25f77366fa6b3b4b768ec3050bf629380bac` is not present, so the model-materialization gate is not satisfied.
- Native execution architecture is now explicit: Host Python invokes an absolute `docker.exe` against the explicit named-pipe endpoint; WSL is used only to translate mount paths, not to own the Docker command channel.
- Model inputs resolve through the read-only, project-scoped `project://.synaptic/model-inventory` abstraction. There is no downloader or hidden network fallback. A fresh project-level SQLite database is normal and remains Host-owned.
- Provider-neutral publication remains the mechanism for arbitrary artifact destinations. The inventory source is configurable local storage today; a future Hugging Face or object-store adapter should materialize the same typed inventory rather than changing training semantics.
- The remaining ordered roadmap is:
  1. Create a clean full Host worktree at `5503c528` with the submodule pinned and checked out exactly at `aec998ee`.
  2. Close native-Windows artifact publication; the current public activation has `publication=None`, while the existing local publication backend is POSIX-only.
  3. Add and independently audit a prepared-path isolated Alpine CPU diagnostic gate; do not reuse the legacy Docker test path.
  4. Release that diagnostic gate.
  5. Materialize the exact SmolLM2 snapshot into the clean worktree's `.synaptic/model-inventory`.
  6. Run the prepared Alpine CPU diagnostic.
  7. Run one one-step NVIDIA SFT smoke only after publication closure and the exact model bytes are present.
  8. Prioritize a Modal smoke next, then HF Jobs and RunPod.
- Current blockers: the GPU smoke must not start until native-Windows publication closure, exact SmolLM2 bytes, and a clean checkout are all proven. No engine redesign is indicated.
- All specialists for this checkpoint are complete. No active worker should be assumed on resume.
- Existing PACT history and unrelated Host, engine, WSL, and test residue remain preserved; do not clean, reset, or rewrite them during handoff setup.
