# PACT Memory

Durable repo-focused context for PACT sessions in this workspace.

## Stable Context

- Phase 1 experiment pipeline was merged to `main` in PR #1 on 2026-06-11. Merge does not equal verification; manual/local verification is still pending.
- PROTOCOL v0.3 is locked and signed off. Changes to hypotheses, falsifiers, or headline matrix require a new signed revision with changelog.
- Training is authorized once protocol prerequisites land. Known prerequisite area includes cloud-lane dataset publication for Qwen3 datasets.
- Local GPU lane and HF Jobs cloud lane are both part of the Phase 1 operating model.
- Use the `experiment-runner` skill for launching, dry-running, or gating the Phase 1 matrix. That skill uses checked-in runner scripts and must not modify the `synaptic-tuner` submodule.
- Phase 3 full SelfAware delta logit diagnostics completed locally on 2026-06-19 for SFT->DPO delta L24 and SFT->KTO delta L25. Source-layer and nearby-layer panels were `status=ok`, `generation_executed=false`, and `logit_diagnostic_executed=true`; source-layer used 18 arms x 16 rows per candidate, and nearby offsets `-2`, `-1`, `+1`, `+2` used coefficients `2/5/10/20` over 16 rows per candidate. Treat as Tier 2 exploratory local diagnostics, not generation evidence or pre-registered headline evidence.
- Submodule-first Docker execution keeps durable orchestration, SQLite state, publication, endpoint selection, and project inventory in the Host. The engine receives an exact prepared plan/bundle and should not own Host persistence or destination policy.
- On native Windows, Host Python invokes an absolute `docker.exe` against an explicit Docker Desktop named-pipe endpoint. WSL is a mount-path translator only; it is not the Docker command channel.
- Model inventory is a configurable, read-only project capability rooted by default at `project://.synaptic/model-inventory`. It has no downloader or implicit network fallback. Future Hugging Face or object-store sources should materialize the same typed inventory contract.
- Artifact destinations remain provider-neutral through the publication registry; local-machine, Hugging Face, or other destinations belong behind publication adapters rather than in Docker training semantics.

## Gotchas

- `rtk`-proxied `pytest tests/` directory globs can falsely report "No tests collected" with exit 0. Re-run with explicit test file paths or bypass `rtk` before concluding collection is broken.
- `correctness_safe` KTO data is intentionally the same four rows as congruence with weights-only 2.0/1.0 ablation; do not gate false rows behind `mapping == "congruence"`.
- `experiment/phase1/data/.gitignore` hard-excludes `bridge_llama2_7b_chat/` for do-not-redistribute containment.
- Phase 3 SelfAware logit-diagnostic interpretation guardrail: KTO L25 showed a cleaner refusal-opener sign pattern than DPO L24 and the nearby-layer smaller grid preserved sign behavior, but do not make source-layer-local claims because nearby wrong-layer arms often matched or exceeded source-layer refusal-opener deltas.
- Pinned `uv 0.12.0` official output may include the exact Linux target triple: `uv 0.12.0 (x86_64-unknown-linux-gnu)`.
- Cold-ingress release requires the real WSL runtime gate to pass before release; hermetic host tests alone are insufficient.
- Authenticate `SourceLock.configuration` provenance exactly once through mandatory `SourceLockBindingV1` inside source evidence; never duplicate those provenance values into `resolved_config` or `execution_context`.
- For durable cloud submission, load and structurally classify the host-owned lifecycle/preparation pair before clock, source inspection, SDK loading, credentials, or provider reads. Only exact absence or a fully revalidated `FOUND` state may cross the provider-session boundary; provider preflight collisions converge through one read-only durable reclassification and never retry spawn.
- Do not treat image/GPU/Docker endpoint readiness as permission to run a GPU smoke. The prepared Docker path also requires native-platform publication closure, exact pinned model bytes in the authenticated inventory, and a clean exact Host/engine checkout.
- The existing local artifact publication backend is POSIX-only. Native-Windows activation must not silently set `publication=None` for a real GPU acceptance smoke; close that boundary first.
