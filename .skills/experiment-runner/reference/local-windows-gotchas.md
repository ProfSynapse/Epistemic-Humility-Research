# Local Windows/Desktop Gotchas

Use this as a router for local Windows, Docker, staging, eval, and bounded local
evidence issues. Load the narrow file first; do not preload the full local
history.

| Task | Load |
|------|------|
| Docker Desktop, local trainer, GPU, cache/env, detached launch, or monitor behavior | [local-runtime.md](local-runtime.md) |
| Dataset identity, leakage checks, recipe materialization, or staged tuner scratch paths | [data-and-staging-gotchas.md](data-and-staging-gotchas.md) |
| Live eval, Qwen thinking tags, output contracts, scorer drift, or post-eval sanity checks | [eval-and-scoring-gotchas.md](eval-and-scoring-gotchas.md) |
| Interpreting bounded local diagnostic/evidence runs | [bounded-local-evidence.md](bounded-local-evidence.md) |
| Phase 3 causal-pilot or logit-diagnostic local execution | [phase3-local-gotchas.md](phase3-local-gotchas.md) |

Bounded local diagnostics, Amendment A/B runs, and smoke tests are not headline
or protocol evidence unless a governed run record explicitly says so.
