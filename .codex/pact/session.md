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
