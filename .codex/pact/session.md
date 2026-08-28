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
