# Sycophancy Answer Behavior-Axis Config Archive

This directory archives legacy Phase 3 answer-sycophancy behavior-axis scan and direction-export configs formerly stored under `experiment/phase1/probe/config/`.

Migration batch: `C026` from `docs/migration/phase1-probe-config-terrain.md`.

Owner decision: archive-only historical provenance for the June 20 Phase 3 answer-sycophancy behavior-axis work. No migrated `experiments/<slug>` owner was present, and these configs are not reusable shared defaults.

The component group contains the answer-sycophancy behavior-axis scan config and the derived direction-export config.

Keep these files as provenance for historical answer-sycophancy axis scans and direction candidates. Do not use this directory as the home for new experiment instruments; new evidence-producing cells belong under `experiments/<slug>/` or `experiments/common/` when promoted for shared reuse.

Non-goal: legacy scan and direction output roots under `experiment/phase1/probe/qwen3-4b-instruct-sycophancy-answer/` are preserved as historical run provenance. Downstream answer-sycophancy candidate, logit, and replay configs consume generated manifests and remain separate terrain components for later review.