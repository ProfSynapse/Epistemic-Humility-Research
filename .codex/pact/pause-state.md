# PACT Pause State

## Status

- Paused intentionally on 2026-09-01 for transfer to a new agent after the Slice 2C activation release checkpoint.
- Current phase: submodule-first Docker local-smoke activation, after prepared activation and native-Windows/model-inventory release, before any prepared-path CPU or GPU execution.
- All specialists from the completed slice are closed; no active worker should be assumed.

## Exact Released Revisions

- Host worktree: `F:\Code\Toolset-Training\_worktrees\ehr-submodule-cloud-api-v1-host`
- Host branch: `feat/submodule-cloud-api-v1-host`
- Host HEAD and origin: `5503c5286b99f6b5905efa4b81a562666f0cfdbc` (**0 ahead / 0 behind**)
- Host parent/prepared-activation release: `4aede291`
- Engine gitlink, checkout, and origin: `aec998ee8d6a2e58d86e19e8132bc59aa21ebd53` (**0 ahead / 0 behind**)

## Completed and Proven

- `4aede291`: prepared Docker activation and trust hardening released.
- `5503c528`: Windows Host execution and config-first model inventory released.
- Independent final audit: **PASS**.
- Accepted verification evidence: **61 passed / 3 skipped** pre-remediation; **25 passed / 1 skipped** final native staging; **11 passed** prepared composition; **40 passed / 2 skipped** integrated inventory/provider/platform/training.
- Read-only preflight passed for the explicit Docker Desktop named-pipe endpoint, locally present production and Alpine images, NVIDIA RTX 3090 24 GB, approximately 170 GB free disk, configuration/dataset validity, and no stale target container.
- No real Docker container, CPU diagnostic, GPU training, publication, cloud job, or paid execution occurred in this checkpoint.

## Accepted Architecture

- Host Python uses absolute `docker.exe` plus the explicit named-pipe endpoint. WSL translates mount paths only.
- The project-scoped read-only model inventory defaults to `project://.synaptic/model-inventory`; it performs no download and has no network fallback.
- A fresh project-level SQLite database is expected and Host-owned.
- Arbitrary output destinations remain supported through the provider-neutral publication registry. Future remote model inventory adapters should materialize the same typed local inventory contract.
- No engine redesign, new lifecycle framework, downloader, or hidden compatibility layer is needed for the remaining local-smoke work.

## Blockers

- Exact SmolLM2 snapshot `12fd25f77366fa6b3b4b768ec3050bf629380bac` is absent.
- Native-Windows publication is incomplete: current public activation sets `publication=None`, and the existing local backend is POSIX-only.
- A clean exact Host worktree with the exact engine submodule has not yet been created for acceptance execution.
- Therefore the GPU smoke remains halted even though Docker, the image, and the GPU passed read-only preflight.

## Exact Next Action

1. Create a clean full Host worktree at `5503c5286b99f6b5905efa4b81a562666f0cfdbc` and initialize/check out `synaptic-tuner` exactly at `aec998ee8d6a2e58d86e19e8132bc59aa21ebd53`.
2. In that clean worktree, design and implement only the native-Windows publication closure needed by the prepared Docker activation path. Preserve provider-neutral destination selection; do not add a Docker-specific destination model.
3. Add a separate prepared-path isolated Alpine CPU diagnostic test/gate, audit it independently, and release it. Do not run or extend the legacy real-Docker test as the acceptance path.
4. Materialize and authenticate the exact SmolLM2 snapshot in `.synaptic/model-inventory`.
5. Run the prepared CPU diagnostic, then one one-step NVIDIA SFT smoke after every blocker is closed.
6. Continue provider proof with Modal as the priority, followed by HF Jobs and RunPod.

## Resume Guardrails

- Start by verifying the exact Host HEAD/origin and engine gitlink/checkout/origin before editing or running anything.
- Preserve existing `.codex/pact` history and all unrelated Host, engine, WSL, and test residue. Do not clean, reset, stash, or rewrite history.
- Reuse released public preparation and Host persistence/publication abstractions. Do not route through legacy `synaptic_host/docker_v1/composition.py` for the new diagnostic.
- Do not pull images or start containers during initial orientation. Repeat the bounded read-only preflight first.
- No secrets should enter the prepared command, staged source, logs, or model inventory.

## Memory Consolidation

- Stable Host/engine boundary, Windows Docker command-channel, project inventory, provider-neutral publication, and smoke-gating lessons were promoted to `.codex/pact/memory.md`.
- Routine test counts and release sequencing remain in `.codex/pact/session.md` and this pause state rather than durable memory.
