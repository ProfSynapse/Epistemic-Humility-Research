# PACT Memory

Durable repo-focused context for PACT sessions in this workspace.

## Stable Context

- Phase 1 experiment pipeline was merged to `main` in PR #1 on 2026-06-11. Merge does not equal verification; manual/local verification is still pending.
- PROTOCOL v0.3 is locked and signed off. Changes to hypotheses, falsifiers, or headline matrix require a new signed revision with changelog.
- Training is authorized once protocol prerequisites land. Known prerequisite area includes cloud-lane dataset publication for Qwen3 datasets.
- Local GPU lane and HF Jobs cloud lane are both part of the Phase 1 operating model.
- Use the `experiment-runner` skill for launching, dry-running, or gating the Phase 1 matrix. That skill uses checked-in runner scripts and must not modify the `synaptic-tuner` submodule.
- Phase 3 full SelfAware delta logit diagnostics completed locally on 2026-06-19 for SFT->DPO delta L24 and SFT->KTO delta L25. Source-layer and nearby-layer panels were `status=ok`, `generation_executed=false`, and `logit_diagnostic_executed=true`; source-layer used 18 arms x 16 rows per candidate, and nearby offsets `-2`, `-1`, `+1`, `+2` used coefficients `2/5/10/20` over 16 rows per candidate. Treat as Tier 2 exploratory local diagnostics, not generation evidence or pre-registered headline evidence.

## Gotchas

- `rtk`-proxied `pytest tests/` directory globs can falsely report "No tests collected" with exit 0. Re-run with explicit test file paths or bypass `rtk` before concluding collection is broken.
- `correctness_safe` KTO data is intentionally the same four rows as congruence with weights-only 2.0/1.0 ablation; do not gate false rows behind `mapping == "congruence"`.
- `experiment/phase1/data/.gitignore` hard-excludes `bridge_llama2_7b_chat/` for do-not-redistribute containment.
- Phase 3 SelfAware logit-diagnostic interpretation guardrail: KTO L25 showed a cleaner refusal-opener sign pattern than DPO L24 and the nearby-layer smaller grid preserved sign behavior, but do not make source-layer-local claims because nearby wrong-layer arms often matched or exceeded source-layer refusal-opener deltas.
