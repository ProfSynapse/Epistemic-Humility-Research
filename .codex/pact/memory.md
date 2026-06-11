# PACT Memory

Durable repo-focused context for PACT sessions in this workspace.

## Stable Context

- Phase 1 experiment pipeline was merged to `main` in PR #1 on 2026-06-11. Merge does not equal verification; manual/local verification is still pending.
- PROTOCOL v0.3 is locked and signed off. Changes to hypotheses, falsifiers, or headline matrix require a new signed revision with changelog.
- Training is authorized once protocol prerequisites land. Known prerequisite area includes cloud-lane dataset publication for Qwen3 datasets.
- Local GPU lane and HF Jobs cloud lane are both part of the Phase 1 operating model.
- Use the `experiment-runner` skill for launching, dry-running, or gating the Phase 1 matrix. That skill uses checked-in runner scripts and must not modify the `synaptic-tuner` submodule.

## Gotchas

- `rtk`-proxied `pytest tests/` directory globs can falsely report "No tests collected" with exit 0. Re-run with explicit test file paths or bypass `rtk` before concluding collection is broken.
- `correctness_safe` KTO data is intentionally the same four rows as congruence with weights-only 2.0/1.0 ablation; do not gate false rows behind `mapping == "congruence"`.
- `experiment/phase1/data/.gitignore` hard-excludes `bridge_llama2_7b_chat/` for do-not-redistribute containment.
