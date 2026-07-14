# Phase 1 outputs migration (2026-07-12)

Dry-run manifest for `bin/migrate_phase1_outputs.py`, classifying the
untracked `experiment/` output tree (~100GB, entirely untracked; confirmed
via `git ls-files experiment/` returning zero) so each amendment's data
lives with its owning `experiments/<slug>/`, shared Phase 1 infrastructure
moves to a gitignored archive location, and disposable build junk is
removed. This document and the sibling
`phase1-outputs-migration-20260712.manifest.json` are the phase 1 (plan)
deliverables; no files have been moved or deleted yet.

## Provenance

- Repo HEAD at plan time: `7bd170efac678eb79e04db232850be03a2366785`
- `experiments/registry.json` blob sha: `7c2e576173c18fa83850e778fab723992eb0b6cb`
- Letter -> slug mapping size: 40 (matches TODO.md's
  generated amendment-status-index total of 40 amendment docs)
- Classifier: `bin/migrate_phase1_outputs.py` (deterministic; letter -> slug
  map built at run time from `experiments/registry.json`'s `legacy.label`
  field, never hand-maintained)

## Totals

| Class | Entries | Size |
|---|---|---|
| Per-amendment | 124 | 43.91 GB |
| Shared infrastructure | 157 | 54.99 GB |
| Junk (deleted) | 38 | 0.01 GB |
| **Total** | **319** | **98.91 GB** |

Collisions: 0. Already-migrated (source missing, skipped): 0.

## Letter -> slug mapping used

Built from `experiments/registry.json`, field `experiments[*].legacy.label`
-> `experiments[*].slug`. Cross-checked against TODO.md's generated
amendment-status index (`<!-- BEGIN GENERATED: amendment-index -->`), which
reports the same total of 40 migrated amendment docs.

| Letter | Slug |
|---|---|
| B | `stated-confidence-grpo` |
| C | `crossover-preference-stacking` |
| D | `schema-response-confidence` |
| E | `probe-scaled-response-confidence` |
| F | `grpo-centered-stacking` |
| G | `best-stack-replication-scale-gate` |
| H | `thinking-enabled-parallel-arm` |
| I | `8b-scale-and-hyperparameter-gates` |
| J | `grpo-v3-proper-scoring-confidence` |
| K | `contrastive-sft-behavior-conditional-confidence` |
| L | `answer-subspan-masked-contrastive-sft` |
| M | `quantile-balanced-probe-distilled-sft` |
| N | `grpo-v3-on-contrastive-sft-base` |
| O | `probe-as-oracle-readout-ceiling` |
| P | `xdataset-probe-transfer` |
| Q | `aux-head-trainable-readout` |
| R | `aux-head-cotraining-native-behavior` |
| S | `correctness-confidence-probe` |
| T | `correctness-readout-deployment-port` |
| U | `unified-two-signal-dial-veto` |
| V | `natural-answer-generalization` |
| W | `base-model-training-free-mechanism` |
| X | `cross-model-size-sweep` |
| Y | `pretrain-only-base-readout` |
| Z | `cross-family-confirmatory` |
| AA | `causal-confidence-steering` |
| AB | `first-person-injection` |
| AC | `doubt-regulated-caution` |
| AD | `inverted-injection-trained-checkpoints` |
| AE | `base-model-doubt-coupled-caution` |
| AF | `second-person-doubt-prime` |
| AG | `oracle-dissociation-prime` |
| AH | `divergent-pool-own-readout` |
| AI | `probe-as-reward` |
| AJ | `knowledge-subspace-erasure` |
| AK | `commitment-point` |
| AL | `radial-anti-propensity-steering` |
| AM | `residual-catch-veto-coverage` |
| AN | `selected-setpoint-regulator` |
| SR | `sampled-decode-seed-robustness` |

Verified against the four name-shape claims in the migration brief:

- `eval/results_amendment_<letter>_*` -> confirmed (e.g.
  `results_amendment_ai_response_confidence_..._4b` -> letter `ai` -> AI ->
  `probe-as-reward`).
- `analysis/amendment_<letters>_*` -> confirmed (`amendment_ai`,
  `amendment_aj_subspace_erasure`, `amendment_al_prep`,
  `amendment_an_prep`).
- `analysis/af_*`, `ag_*` -> confirmed, and the same shape generalizes to
  `ac_*` (AC), `ae_*` (AE), `ah_*` (AH), `ak_*` (AK), `am_*` (AM) -- all
  handled by the same rule, not hardcoded per letter.
- `sr_*` (Amendment SR = `sampled-decode-seed-robustness`) and `z_*`
  (Amendment Z = `cross-family-confirmatory`) -> confirmed, both as direct
  children of `probe/` rather than `probe/analysis/`.

Notably, `results_amendment_a_*` (bare letter `A`, six eval directories) does
**not** resolve: there is no amendment `A` in the registry (the sequence
runs B..Z, AA..AN, plus SR). These six directories are classified `shared`
with `candidate_letter: A` rather than guessed onto any experiment -- they
read as the locked Phase 1 headline-matrix eval results, not an amendment's
output. See the unmapped section below.

## Per-amendment breakdown

Destination pattern: `experiments/<slug>/analysis/phase1-migrated/<path-under-experiment/phase1/>`.
All 23 destination slugs already have their `analysis/` directory covered
by the root `.gitignore` rule `experiments/*/analysis/` (verified with
`git check-ignore` for every slug below) -- no per-experiment `.gitignore`
edits were made or are needed.

| Slug | Entries | Size |
|---|---|---|
| `answer-subspan-masked-contrastive-sft` | 1 | 0.00 GB |
| `aux-head-cotraining-native-behavior` | 3 | 0.01 GB |
| `base-model-doubt-coupled-caution` | 3 | 0.00 GB |
| `commitment-point` | 1 | 0.00 GB |
| `contrastive-sft-behavior-conditional-confidence` | 1 | 0.00 GB |
| `cross-family-confirmatory` | 9 | 8.47 GB |
| `divergent-pool-own-readout` | 4 | 6.60 GB |
| `doubt-regulated-caution` | 4 | 0.00 GB |
| `grpo-centered-stacking` | 7 | 0.01 GB |
| `grpo-v3-on-contrastive-sft-base` | 3 | 0.01 GB |
| `grpo-v3-proper-scoring-confidence` | 1 | 0.00 GB |
| `knowledge-subspace-erasure` | 1 | 0.00 GB |
| `oracle-dissociation-prime` | 5 | 0.64 GB |
| `probe-as-reward` | 3 | 1.12 GB |
| `probe-scaled-response-confidence` | 13 | 0.01 GB |
| `quantile-balanced-probe-distilled-sft` | 1 | 0.00 GB |
| `radial-anti-propensity-steering` | 1 | 1.72 GB |
| `residual-catch-veto-coverage` | 1 | 0.00 GB |
| `sampled-decode-seed-robustness` | 21 | 24.97 GB |
| `schema-response-confidence` | 7 | 0.01 GB |
| `second-person-doubt-prime` | 2 | 0.21 GB |
| `selected-setpoint-regulator` | 1 | 0.00 GB |
| `stated-confidence-grpo` | 31 | 0.11 GB |

<details><summary>Full per-amendment entry list (src -> dest, size)</summary>

| Src | Dest | Size |
|---|---|---|
| `experiment/phase1/eval/results_amendment_l_response_confidence_selfaware_contrastive_masked_sft_seed1_merged_full_4b` | `experiments/answer-subspan-masked-contrastive-sft/analysis/phase1-migrated/eval/results_amendment_l_response_confidence_selfaware_contrastive_masked_sft_seed1_merged_full_4b` | 0.003 GB |
| `experiment/phase1/eval/results_amendment_r_response_confidence_selfaware_a0_full_4b` | `experiments/aux-head-cotraining-native-behavior/analysis/phase1-migrated/eval/results_amendment_r_response_confidence_selfaware_a0_full_4b` | 0.002 GB |
| `experiment/phase1/eval/results_amendment_r_response_confidence_selfaware_a1_full_4b` | `experiments/aux-head-cotraining-native-behavior/analysis/phase1-migrated/eval/results_amendment_r_response_confidence_selfaware_a1_full_4b` | 0.002 GB |
| `experiment/phase1/eval/results_amendment_r_response_confidence_selfaware_a2_full_4b` | `experiments/aux-head-cotraining-native-behavior/analysis/phase1-migrated/eval/results_amendment_r_response_confidence_selfaware_a2_full_4b` | 0.002 GB |
| `experiment/phase1/probe/analysis/ae_base_baseline_collection` | `experiments/base-model-doubt-coupled-caution/analysis/phase1-migrated/probe/analysis/ae_base_baseline_collection` | 0.000 GB |
| `experiment/phase1/probe/analysis/ae_base_behavior_rows` | `experiments/base-model-doubt-coupled-caution/analysis/phase1-migrated/probe/analysis/ae_base_behavior_rows` | 0.000 GB |
| `experiment/phase1/probe/analysis/ae_base_pool` | `experiments/base-model-doubt-coupled-caution/analysis/phase1-migrated/probe/analysis/ae_base_pool` | 0.000 GB |
| `experiment/phase1/probe/analysis/ak_stage1` | `experiments/commitment-point/analysis/phase1-migrated/probe/analysis/ak_stage1` | 0.000 GB |
| `experiment/phase1/eval/results_amendment_k_response_confidence_selfaware_contrastive_sft_seed1_merged_full_4b` | `experiments/contrastive-sft-behavior-conditional-confidence/analysis/phase1-migrated/eval/results_amendment_k_response_confidence_selfaware_contrastive_sft_seed1_merged_full_4b` | 0.003 GB |
| `experiment/phase1/probe/z_gemma-4-e4b` | `experiments/cross-family-confirmatory/analysis/phase1-migrated/probe/z_gemma-4-e4b` | 2.477 GB |
| `experiment/phase1/probe/z_llama-3.2-3b` | `experiments/cross-family-confirmatory/analysis/phase1-migrated/probe/z_llama-3.2-3b` | 2.003 GB |
| `experiment/phase1/probe/z_logs` | `experiments/cross-family-confirmatory/analysis/phase1-migrated/probe/z_logs` | 0.002 GB |
| `experiment/phase1/probe/z_ministral-3-3b` | `experiments/cross-family-confirmatory/analysis/phase1-migrated/probe/z_ministral-3-3b` | 1.865 GB |
| `experiment/phase1/probe/z_qwen3.5-4b` | `experiments/cross-family-confirmatory/analysis/phase1-migrated/probe/z_qwen3.5-4b` | 1.901 GB |
| `experiment/phase1/probe/z_smoke_gemma-4-e4b` | `experiments/cross-family-confirmatory/analysis/phase1-migrated/probe/z_smoke_gemma-4-e4b` | 0.066 GB |
| `experiment/phase1/probe/z_smoke_llama-3.2-3b` | `experiments/cross-family-confirmatory/analysis/phase1-migrated/probe/z_smoke_llama-3.2-3b` | 0.053 GB |
| `experiment/phase1/probe/z_smoke_ministral-3-3b` | `experiments/cross-family-confirmatory/analysis/phase1-migrated/probe/z_smoke_ministral-3-3b` | 0.050 GB |
| `experiment/phase1/probe/z_smoke_qwen3.5-4b` | `experiments/cross-family-confirmatory/analysis/phase1-migrated/probe/z_smoke_qwen3.5-4b` | 0.051 GB |
| `experiment/phase1/probe/analysis/ah_addendum_a1` | `experiments/divergent-pool-own-readout/analysis/phase1-migrated/probe/analysis/ah_addendum_a1` | 0.000 GB |
| `experiment/phase1/probe/analysis/ah_main` | `experiments/divergent-pool-own-readout/analysis/phase1-migrated/probe/analysis/ah_main` | 0.005 GB |
| `experiment/phase1/probe/analysis/ah_scout` | `experiments/divergent-pool-own-readout/analysis/phase1-migrated/probe/analysis/ah_scout` | 0.000 GB |
| `experiment/phase1/probe/analysis/ah_stage0` | `experiments/divergent-pool-own-readout/analysis/phase1-migrated/probe/analysis/ah_stage0` | 6.595 GB |
| `experiment/phase1/probe/analysis/ac_doubt_coupled_intervention` | `experiments/doubt-regulated-caution/analysis/phase1-migrated/probe/analysis/ac_doubt_coupled_intervention` | 0.002 GB |
| `experiment/phase1/probe/analysis/ac_doubt_coupled_intervention_smoke` | `experiments/doubt-regulated-caution/analysis/phase1-migrated/probe/analysis/ac_doubt_coupled_intervention_smoke` | 0.000 GB |
| `experiment/phase1/probe/analysis/ac_doubt_coupled_intervention_smoke_batched_check` | `experiments/doubt-regulated-caution/analysis/phase1-migrated/probe/analysis/ac_doubt_coupled_intervention_smoke_batched_check` | 0.000 GB |
| `experiment/phase1/probe/analysis/ac_doubt_gain_map` | `experiments/doubt-regulated-caution/analysis/phase1-migrated/probe/analysis/ac_doubt_gain_map` | 0.000 GB |
| `experiment/phase1/eval/results_amendment_f_response_confidence_selfaware_clean_sft_dpo_grpo_seed1_full_4b` | `experiments/grpo-centered-stacking/analysis/phase1-migrated/eval/results_amendment_f_response_confidence_selfaware_clean_sft_dpo_grpo_seed1_full_4b` | 0.002 GB |
| `experiment/phase1/eval/results_amendment_f_response_confidence_selfaware_clean_sft_dpo_merged_seed1_sanity_4b` | `experiments/grpo-centered-stacking/analysis/phase1-migrated/eval/results_amendment_f_response_confidence_selfaware_clean_sft_dpo_merged_seed1_sanity_4b` | 0.000 GB |
| `experiment/phase1/eval/results_amendment_f_response_confidence_selfaware_clean_sft_grpo_dpo_seed1_full_4b` | `experiments/grpo-centered-stacking/analysis/phase1-migrated/eval/results_amendment_f_response_confidence_selfaware_clean_sft_grpo_dpo_seed1_full_4b` | 0.003 GB |
| `experiment/phase1/eval/results_amendment_f_response_confidence_selfaware_clean_sft_grpo_kto_seed1_full_4b` | `experiments/grpo-centered-stacking/analysis/phase1-migrated/eval/results_amendment_f_response_confidence_selfaware_clean_sft_grpo_kto_seed1_full_4b` | 0.002 GB |
| `experiment/phase1/eval/results_amendment_f_response_confidence_selfaware_clean_sft_grpo_v2_merged_seed1_sanity_4b` | `experiments/grpo-centered-stacking/analysis/phase1-migrated/eval/results_amendment_f_response_confidence_selfaware_clean_sft_grpo_v2_merged_seed1_sanity_4b` | 0.000 GB |
| `experiment/phase1/eval/results_amendment_f_response_confidence_selfaware_clean_sft_kto_grpo_seed1_full_4b` | `experiments/grpo-centered-stacking/analysis/phase1-migrated/eval/results_amendment_f_response_confidence_selfaware_clean_sft_kto_grpo_seed1_full_4b` | 0.002 GB |
| `experiment/phase1/eval/results_amendment_f_response_confidence_selfaware_clean_sft_kto_merged_seed1_sanity_4b` | `experiments/grpo-centered-stacking/analysis/phase1-migrated/eval/results_amendment_f_response_confidence_selfaware_clean_sft_kto_merged_seed1_sanity_4b` | 0.000 GB |
| `experiment/phase1/eval/results_amendment_n_beta005_selfaware_grpo_on_contrastive_sft_seed1_full_4b` | `experiments/grpo-v3-on-contrastive-sft-base/analysis/phase1-migrated/eval/results_amendment_n_beta005_selfaware_grpo_on_contrastive_sft_seed1_full_4b` | 0.003 GB |
| `experiment/phase1/eval/results_amendment_n_diag_temp135_selfaware_grpo_on_contrastive_sft_seed1_full_4b` | `experiments/grpo-v3-on-contrastive-sft-base/analysis/phase1-migrated/eval/results_amendment_n_diag_temp135_selfaware_grpo_on_contrastive_sft_seed1_full_4b` | 0.003 GB |
| `experiment/phase1/eval/results_amendment_n_response_confidence_selfaware_grpo_on_contrastive_sft_seed1_full_4b` | `experiments/grpo-v3-on-contrastive-sft-base/analysis/phase1-migrated/eval/results_amendment_n_response_confidence_selfaware_grpo_on_contrastive_sft_seed1_full_4b` | 0.003 GB |
| `experiment/phase1/eval/results_amendment_j_response_confidence_selfaware_clean_sft_grpo_v3_seed1_full_4b` | `experiments/grpo-v3-proper-scoring-confidence/analysis/phase1-migrated/eval/results_amendment_j_response_confidence_selfaware_clean_sft_grpo_v3_seed1_full_4b` | 0.003 GB |
| `experiment/phase1/probe/analysis/amendment_aj_subspace_erasure` | `experiments/knowledge-subspace-erasure/analysis/phase1-migrated/probe/analysis/amendment_aj_subspace_erasure` | 0.000 GB |
| `experiment/phase1/probe/analysis/ag_generation` | `experiments/oracle-dissociation-prime/analysis/phase1-migrated/probe/analysis/ag_generation` | 0.000 GB |
| `experiment/phase1/probe/analysis/ag_neutral_pregen` | `experiments/oracle-dissociation-prime/analysis/phase1-migrated/probe/analysis/ag_neutral_pregen` | 0.213 GB |
| `experiment/phase1/probe/analysis/ag_primed_pregen` | `experiments/oracle-dissociation-prime/analysis/phase1-migrated/probe/analysis/ag_primed_pregen` | 0.427 GB |
| `experiment/phase1/probe/analysis/ag_score` | `experiments/oracle-dissociation-prime/analysis/phase1-migrated/probe/analysis/ag_score` | 0.000 GB |
| `experiment/phase1/probe/analysis/ag_state` | `experiments/oracle-dissociation-prime/analysis/phase1-migrated/probe/analysis/ag_state` | 0.000 GB |
| `experiment/phase1/eval/results_amendment_ai_response_confidence_selfaware_par_permuted_seed1_corrected_base_full_4b` | `experiments/probe-as-reward/analysis/phase1-migrated/eval/results_amendment_ai_response_confidence_selfaware_par_permuted_seed1_corrected_base_full_4b` | 0.003 GB |
| `experiment/phase1/eval/results_amendment_ai_response_confidence_selfaware_par_true_seed1_corrected_base_full_4b` | `experiments/probe-as-reward/analysis/phase1-migrated/eval/results_amendment_ai_response_confidence_selfaware_par_true_seed1_corrected_base_full_4b` | 0.003 GB |
| `experiment/phase1/probe/analysis/amendment_ai` | `experiments/probe-as-reward/analysis/phase1-migrated/probe/analysis/amendment_ai` | 1.118 GB |
| `experiment/phase1/eval/results_amendment_e_response_confidence_selfaware_clean_sft_dpo_seed1_corrected_base_full_4b` | `experiments/probe-scaled-response-confidence/analysis/phase1-migrated/eval/results_amendment_e_response_confidence_selfaware_clean_sft_dpo_seed1_corrected_base_full_4b` | 0.003 GB |
| `experiment/phase1/eval/results_amendment_e_response_confidence_selfaware_clean_sft_dpo_seed1_corrected_base_smoke_4b` | `experiments/probe-scaled-response-confidence/analysis/phase1-migrated/eval/results_amendment_e_response_confidence_selfaware_clean_sft_dpo_seed1_corrected_base_smoke_4b` | 0.000 GB |
| `experiment/phase1/eval/results_amendment_e_response_confidence_selfaware_clean_sft_dpo_seed1_smoke_4b` | `experiments/probe-scaled-response-confidence/analysis/phase1-migrated/eval/results_amendment_e_response_confidence_selfaware_clean_sft_dpo_seed1_smoke_4b` | 0.000 GB |
| `experiment/phase1/eval/results_amendment_e_response_confidence_selfaware_clean_sft_grpo_seed1_corrected_base_full_4b` | `experiments/probe-scaled-response-confidence/analysis/phase1-migrated/eval/results_amendment_e_response_confidence_selfaware_clean_sft_grpo_seed1_corrected_base_full_4b` | 0.003 GB |
| `experiment/phase1/eval/results_amendment_e_response_confidence_selfaware_clean_sft_grpo_seed1_corrected_base_smoke_4b` | `experiments/probe-scaled-response-confidence/analysis/phase1-migrated/eval/results_amendment_e_response_confidence_selfaware_clean_sft_grpo_seed1_corrected_base_smoke_4b` | 0.000 GB |
| `experiment/phase1/eval/results_amendment_e_response_confidence_selfaware_clean_sft_grpo_v2_seed1_corrected_base_full_4b` | `experiments/probe-scaled-response-confidence/analysis/phase1-migrated/eval/results_amendment_e_response_confidence_selfaware_clean_sft_grpo_v2_seed1_corrected_base_full_4b` | 0.003 GB |
| `experiment/phase1/eval/results_amendment_e_response_confidence_selfaware_clean_sft_kto_seed1_corrected_base_full_4b` | `experiments/probe-scaled-response-confidence/analysis/phase1-migrated/eval/results_amendment_e_response_confidence_selfaware_clean_sft_kto_seed1_corrected_base_full_4b` | 0.003 GB |
| `experiment/phase1/eval/results_amendment_e_response_confidence_selfaware_clean_sft_kto_seed1_corrected_base_smoke_4b` | `experiments/probe-scaled-response-confidence/analysis/phase1-migrated/eval/results_amendment_e_response_confidence_selfaware_clean_sft_kto_seed1_corrected_base_smoke_4b` | 0.000 GB |
| `experiment/phase1/eval/results_amendment_e_response_confidence_selfaware_clean_sft_seed1_merged_full_4b` | `experiments/probe-scaled-response-confidence/analysis/phase1-migrated/eval/results_amendment_e_response_confidence_selfaware_clean_sft_seed1_merged_full_4b` | 0.003 GB |
| `experiment/phase1/eval/results_amendment_e_response_confidence_selfaware_clean_sft_seed1_merged_smoke_4b` | `experiments/probe-scaled-response-confidence/analysis/phase1-migrated/eval/results_amendment_e_response_confidence_selfaware_clean_sft_seed1_merged_smoke_4b` | 0.000 GB |
| `experiment/phase1/eval/results_amendment_e_response_confidence_selfaware_clean_sft_seed1_smoke_4b` | `experiments/probe-scaled-response-confidence/analysis/phase1-migrated/eval/results_amendment_e_response_confidence_selfaware_clean_sft_seed1_smoke_4b` | 0.000 GB |
| `experiment/phase1/eval/results_amendment_e_response_confidence_selfaware_contrastive_sft_seed1_checkpoint1500_smoke_4b` | `experiments/probe-scaled-response-confidence/analysis/phase1-migrated/eval/results_amendment_e_response_confidence_selfaware_contrastive_sft_seed1_checkpoint1500_smoke_4b` | 0.000 GB |
| `experiment/phase1/eval/results_amendment_e_response_confidence_selfaware_probe_scaled_sft_seed1_smoke_4b` | `experiments/probe-scaled-response-confidence/analysis/phase1-migrated/eval/results_amendment_e_response_confidence_selfaware_probe_scaled_sft_seed1_smoke_4b` | 0.000 GB |
| `experiment/phase1/eval/results_amendment_m_response_confidence_selfaware_probe_factual_sft_seed1_merged_full_4b` | `experiments/quantile-balanced-probe-distilled-sft/analysis/phase1-migrated/eval/results_amendment_m_response_confidence_selfaware_probe_factual_sft_seed1_merged_full_4b` | 0.003 GB |
| `experiment/phase1/probe/analysis/amendment_al_prep` | `experiments/radial-anti-propensity-steering/analysis/phase1-migrated/probe/analysis/amendment_al_prep` | 1.723 GB |
| `experiment/phase1/probe/analysis/am_residual_catch` | `experiments/residual-catch-veto-coverage/analysis/phase1-migrated/probe/analysis/am_residual_catch` | 0.000 GB |
| `experiment/phase1/probe/sr_gemma-4-e4b_seed20260701` | `experiments/sampled-decode-seed-robustness/analysis/phase1-migrated/probe/sr_gemma-4-e4b_seed20260701` | 0.000 GB |
| `experiment/phase1/probe/sr_gemma-4-e4b_seed20260702` | `experiments/sampled-decode-seed-robustness/analysis/phase1-migrated/probe/sr_gemma-4-e4b_seed20260702` | 0.000 GB |
| `experiment/phase1/probe/sr_gemma-4-e4b_seed20260703` | `experiments/sampled-decode-seed-robustness/analysis/phase1-migrated/probe/sr_gemma-4-e4b_seed20260703` | 0.000 GB |
| `experiment/phase1/probe/sr_llama-3.2-3b_seed20260701` | `experiments/sampled-decode-seed-robustness/analysis/phase1-migrated/probe/sr_llama-3.2-3b_seed20260701` | 2.003 GB |
| `experiment/phase1/probe/sr_llama-3.2-3b_seed20260702` | `experiments/sampled-decode-seed-robustness/analysis/phase1-migrated/probe/sr_llama-3.2-3b_seed20260702` | 2.003 GB |
| `experiment/phase1/probe/sr_llama-3.2-3b_seed20260703` | `experiments/sampled-decode-seed-robustness/analysis/phase1-migrated/probe/sr_llama-3.2-3b_seed20260703` | 2.003 GB |
| `experiment/phase1/probe/sr_logs` | `experiments/sampled-decode-seed-robustness/analysis/phase1-migrated/probe/sr_logs` | 0.007 GB |
| `experiment/phase1/probe/sr_ministral-3-3b_seed20260701` | `experiments/sampled-decode-seed-robustness/analysis/phase1-migrated/probe/sr_ministral-3-3b_seed20260701` | 1.865 GB |
| `experiment/phase1/probe/sr_ministral-3-3b_seed20260702` | `experiments/sampled-decode-seed-robustness/analysis/phase1-migrated/probe/sr_ministral-3-3b_seed20260702` | 1.865 GB |
| `experiment/phase1/probe/sr_ministral-3-3b_seed20260703` | `experiments/sampled-decode-seed-robustness/analysis/phase1-migrated/probe/sr_ministral-3-3b_seed20260703` | 1.865 GB |
| `experiment/phase1/probe/sr_qwen3.5-4b_seed20260701` | `experiments/sampled-decode-seed-robustness/analysis/phase1-migrated/probe/sr_qwen3.5-4b_seed20260701` | 1.901 GB |
| `experiment/phase1/probe/sr_qwen3.5-4b_seed20260702` | `experiments/sampled-decode-seed-robustness/analysis/phase1-migrated/probe/sr_qwen3.5-4b_seed20260702` | 1.901 GB |
| `experiment/phase1/probe/sr_qwen3.5-4b_seed20260703` | `experiments/sampled-decode-seed-robustness/analysis/phase1-migrated/probe/sr_qwen3.5-4b_seed20260703` | 1.901 GB |
| `experiment/phase1/probe/sr_rr_gemma-4-e4b_seed20260701` | `experiments/sampled-decode-seed-robustness/analysis/phase1-migrated/probe/sr_rr_gemma-4-e4b_seed20260701` | 2.478 GB |
| `experiment/phase1/probe/sr_rr_gemma-4-e4b_seed20260702` | `experiments/sampled-decode-seed-robustness/analysis/phase1-migrated/probe/sr_rr_gemma-4-e4b_seed20260702` | 2.476 GB |
| `experiment/phase1/probe/sr_rr_gemma-4-e4b_seed20260703` | `experiments/sampled-decode-seed-robustness/analysis/phase1-migrated/probe/sr_rr_gemma-4-e4b_seed20260703` | 2.477 GB |
| `experiment/phase1/probe/sr_rr_smoke_gemma-4-e4b` | `experiments/sampled-decode-seed-robustness/analysis/phase1-migrated/probe/sr_rr_smoke_gemma-4-e4b` | 0.066 GB |
| `experiment/phase1/probe/sr_smoke_gemma-4-e4b` | `experiments/sampled-decode-seed-robustness/analysis/phase1-migrated/probe/sr_smoke_gemma-4-e4b` | 0.000 GB |
| `experiment/phase1/probe/sr_smoke_llama-3.2-3b` | `experiments/sampled-decode-seed-robustness/analysis/phase1-migrated/probe/sr_smoke_llama-3.2-3b` | 0.053 GB |
| `experiment/phase1/probe/sr_smoke_ministral-3-3b` | `experiments/sampled-decode-seed-robustness/analysis/phase1-migrated/probe/sr_smoke_ministral-3-3b` | 0.050 GB |
| `experiment/phase1/probe/sr_smoke_qwen3.5-4b` | `experiments/sampled-decode-seed-robustness/analysis/phase1-migrated/probe/sr_smoke_qwen3.5-4b` | 0.051 GB |
| `experiment/phase1/eval/results_amendment_d_response_confidence_selfaware_schema_sft_dpo_seed1_smoke_4b` | `experiments/schema-response-confidence/analysis/phase1-migrated/eval/results_amendment_d_response_confidence_selfaware_schema_sft_dpo_seed1_smoke_4b` | 0.000 GB |
| `experiment/phase1/eval/results_amendment_d_response_confidence_selfaware_schema_sft_grpo_seed1_full_4b` | `experiments/schema-response-confidence/analysis/phase1-migrated/eval/results_amendment_d_response_confidence_selfaware_schema_sft_grpo_seed1_full_4b` | 0.003 GB |
| `experiment/phase1/eval/results_amendment_d_response_confidence_selfaware_schema_sft_grpo_seed1_smoke_4b` | `experiments/schema-response-confidence/analysis/phase1-migrated/eval/results_amendment_d_response_confidence_selfaware_schema_sft_grpo_seed1_smoke_4b` | 0.000 GB |
| `experiment/phase1/eval/results_amendment_d_response_confidence_selfaware_schema_sft_kto_seed1_smoke_4b` | `experiments/schema-response-confidence/analysis/phase1-migrated/eval/results_amendment_d_response_confidence_selfaware_schema_sft_kto_seed1_smoke_4b` | 0.000 GB |
| `experiment/phase1/eval/results_amendment_d_response_confidence_selfaware_schema_sft_seed1_merged_full_4b` | `experiments/schema-response-confidence/analysis/phase1-migrated/eval/results_amendment_d_response_confidence_selfaware_schema_sft_seed1_merged_full_4b` | 0.003 GB |
| `experiment/phase1/eval/results_amendment_d_response_confidence_selfaware_schema_sft_seed1_merged_smoke_4b` | `experiments/schema-response-confidence/analysis/phase1-migrated/eval/results_amendment_d_response_confidence_selfaware_schema_sft_seed1_merged_smoke_4b` | 0.000 GB |
| `experiment/phase1/eval/results_amendment_d_response_confidence_selfaware_schema_sft_seed1_smoke_4b` | `experiments/schema-response-confidence/analysis/phase1-migrated/eval/results_amendment_d_response_confidence_selfaware_schema_sft_seed1_smoke_4b` | 0.000 GB |
| `experiment/phase1/probe/analysis/af_base_pregen` | `experiments/second-person-doubt-prime/analysis/phase1-migrated/probe/analysis/af_base_pregen` | 0.213 GB |
| `experiment/phase1/probe/analysis/af_generation` | `experiments/second-person-doubt-prime/analysis/phase1-migrated/probe/analysis/af_generation` | 0.001 GB |
| `experiment/phase1/probe/analysis/amendment_an_prep` | `experiments/selected-setpoint-regulator/analysis/phase1-migrated/probe/analysis/amendment_an_prep` | 0.002 GB |
| `experiment/phase1/eval/results_amendment_b_response_confidence_selfaware_sft_bridge_grpo_seed1_full_4b` | `experiments/stated-confidence-grpo/analysis/phase1-migrated/eval/results_amendment_b_response_confidence_selfaware_sft_bridge_grpo_seed1_full_4b` | 0.005 GB |
| `experiment/phase1/eval/results_amendment_b_response_confidence_selfaware_sft_bridge_grpo_seed1_smoke_4b` | `experiments/stated-confidence-grpo/analysis/phase1-migrated/eval/results_amendment_b_response_confidence_selfaware_sft_bridge_grpo_seed1_smoke_4b` | 0.000 GB |
| `experiment/phase1/eval/results_amendment_b_response_confidence_selfaware_sft_bridge_grpo_seed1_unknown_smoke_4b` | `experiments/stated-confidence-grpo/analysis/phase1-migrated/eval/results_amendment_b_response_confidence_selfaware_sft_bridge_grpo_seed1_unknown_smoke_4b` | 0.000 GB |
| `experiment/phase1/eval/results_amendment_b_stated_confidence_neutral_concise_schema_answer_confidence_selfaware_seed1_all_arms_4b` | `experiments/stated-confidence-grpo/analysis/phase1-migrated/eval/results_amendment_b_stated_confidence_neutral_concise_schema_answer_confidence_selfaware_seed1_all_arms_4b` | 0.010 GB |
| `experiment/phase1/eval/results_amendment_b_stated_confidence_neutral_concise_schema_answer_confidence_selfaware_seed1_all_arms_4b_thinking_on` | `experiments/stated-confidence-grpo/analysis/phase1-migrated/eval/results_amendment_b_stated_confidence_neutral_concise_schema_answer_confidence_selfaware_seed1_all_arms_4b_thinking_on` | 0.011 GB |
| `experiment/phase1/eval/results_amendment_b_stated_confidence_neutral_concise_schema_answer_confidence_selfaware_seed1_base_smoke_4b` | `experiments/stated-confidence-grpo/analysis/phase1-migrated/eval/results_amendment_b_stated_confidence_neutral_concise_schema_answer_confidence_selfaware_seed1_base_smoke_4b` | 0.000 GB |
| `experiment/phase1/eval/results_amendment_b_stated_confidence_neutral_concise_schema_answer_confidence_selfaware_seed1_base_smoke_4b_thinking_on` | `experiments/stated-confidence-grpo/analysis/phase1-migrated/eval/results_amendment_b_stated_confidence_neutral_concise_schema_answer_confidence_selfaware_seed1_base_smoke_4b_thinking_on` | 0.000 GB |
| `experiment/phase1/eval/results_amendment_b_stated_confidence_neutral_concise_schema_answer_confidence_selfaware_seed2_all_arms_4b` | `experiments/stated-confidence-grpo/analysis/phase1-migrated/eval/results_amendment_b_stated_confidence_neutral_concise_schema_answer_confidence_selfaware_seed2_all_arms_4b` | 0.010 GB |
| `experiment/phase1/eval/results_amendment_b_stated_confidence_neutral_concise_schema_answer_confidence_selfaware_seed2_all_arms_4b_thinking_on` | `experiments/stated-confidence-grpo/analysis/phase1-migrated/eval/results_amendment_b_stated_confidence_neutral_concise_schema_answer_confidence_selfaware_seed2_all_arms_4b_thinking_on` | 0.011 GB |
| `experiment/phase1/eval/results_amendment_b_stated_confidence_neutral_concise_schema_answer_confidence_selfaware_seed3_all_arms_4b` | `experiments/stated-confidence-grpo/analysis/phase1-migrated/eval/results_amendment_b_stated_confidence_neutral_concise_schema_answer_confidence_selfaware_seed3_all_arms_4b` | 0.010 GB |
| `experiment/phase1/eval/results_amendment_b_stated_confidence_neutral_concise_schema_answer_confidence_selfaware_seed3_all_arms_4b_thinking_on` | `experiments/stated-confidence-grpo/analysis/phase1-migrated/eval/results_amendment_b_stated_confidence_neutral_concise_schema_answer_confidence_selfaware_seed3_all_arms_4b_thinking_on` | 0.011 GB |
| `experiment/phase1/eval/results_amendment_b_stated_confidence_neutral_concise_schema_answer_confidence_selfaware_seq_seed1_4b` | `experiments/stated-confidence-grpo/analysis/phase1-migrated/eval/results_amendment_b_stated_confidence_neutral_concise_schema_answer_confidence_selfaware_seq_seed1_4b` | 0.006 GB |
| `experiment/phase1/eval/results_amendment_b_stated_confidence_neutral_concise_schema_answer_confidence_selfaware_seq_seed1_4b_thinking_on` | `experiments/stated-confidence-grpo/analysis/phase1-migrated/eval/results_amendment_b_stated_confidence_neutral_concise_schema_answer_confidence_selfaware_seq_seed1_4b_thinking_on` | 0.007 GB |
| `experiment/phase1/eval/results_amendment_b_stated_confidence_neutral_concise_schema_answer_confidence_selfaware_seq_seed2_sft_dpo_4b` | `experiments/stated-confidence-grpo/analysis/phase1-migrated/eval/results_amendment_b_stated_confidence_neutral_concise_schema_answer_confidence_selfaware_seq_seed2_sft_dpo_4b` | 0.002 GB |
| `experiment/phase1/eval/results_amendment_b_stated_confidence_neutral_concise_schema_answer_confidence_selfaware_seq_seed2_sft_dpo_4b_thinking_on` | `experiments/stated-confidence-grpo/analysis/phase1-migrated/eval/results_amendment_b_stated_confidence_neutral_concise_schema_answer_confidence_selfaware_seq_seed2_sft_dpo_4b_thinking_on` | 0.002 GB |
| `experiment/phase1/eval/results_amendment_b_stated_confidence_neutral_concise_schema_answer_confidence_selfaware_seq_seed2_sft_kto_4b` | `experiments/stated-confidence-grpo/analysis/phase1-migrated/eval/results_amendment_b_stated_confidence_neutral_concise_schema_answer_confidence_selfaware_seq_seed2_sft_kto_4b` | 0.002 GB |
| `experiment/phase1/eval/results_amendment_b_stated_confidence_neutral_concise_schema_answer_confidence_selfaware_seq_seed2_sft_kto_4b_thinking_on` | `experiments/stated-confidence-grpo/analysis/phase1-migrated/eval/results_amendment_b_stated_confidence_neutral_concise_schema_answer_confidence_selfaware_seq_seed2_sft_kto_4b_thinking_on` | 0.002 GB |
| `experiment/phase1/eval/results_amendment_b_stated_confidence_neutral_concise_schema_answer_confidence_selfaware_seq_seed2_sft_merged_4b` | `experiments/stated-confidence-grpo/analysis/phase1-migrated/eval/results_amendment_b_stated_confidence_neutral_concise_schema_answer_confidence_selfaware_seq_seed2_sft_merged_4b` | 0.002 GB |
| `experiment/phase1/eval/results_amendment_b_stated_confidence_neutral_concise_schema_answer_confidence_selfaware_seq_seed2_sft_merged_4b_thinking_on` | `experiments/stated-confidence-grpo/analysis/phase1-migrated/eval/results_amendment_b_stated_confidence_neutral_concise_schema_answer_confidence_selfaware_seq_seed2_sft_merged_4b_thinking_on` | 0.002 GB |
| `experiment/phase1/eval/results_amendment_b_stated_confidence_neutral_concise_schema_answer_confidence_selfaware_seq_seed3_sft_dpo_4b` | `experiments/stated-confidence-grpo/analysis/phase1-migrated/eval/results_amendment_b_stated_confidence_neutral_concise_schema_answer_confidence_selfaware_seq_seed3_sft_dpo_4b` | 0.002 GB |
| `experiment/phase1/eval/results_amendment_b_stated_confidence_neutral_concise_schema_answer_confidence_selfaware_seq_seed3_sft_dpo_4b_thinking_on` | `experiments/stated-confidence-grpo/analysis/phase1-migrated/eval/results_amendment_b_stated_confidence_neutral_concise_schema_answer_confidence_selfaware_seq_seed3_sft_dpo_4b_thinking_on` | 0.002 GB |
| `experiment/phase1/eval/results_amendment_b_stated_confidence_neutral_concise_schema_answer_confidence_selfaware_seq_seed3_sft_kto_4b` | `experiments/stated-confidence-grpo/analysis/phase1-migrated/eval/results_amendment_b_stated_confidence_neutral_concise_schema_answer_confidence_selfaware_seq_seed3_sft_kto_4b` | 0.002 GB |
| `experiment/phase1/eval/results_amendment_b_stated_confidence_neutral_concise_schema_answer_confidence_selfaware_seq_seed3_sft_kto_4b_thinking_on` | `experiments/stated-confidence-grpo/analysis/phase1-migrated/eval/results_amendment_b_stated_confidence_neutral_concise_schema_answer_confidence_selfaware_seq_seed3_sft_kto_4b_thinking_on` | 0.002 GB |
| `experiment/phase1/eval/results_amendment_b_stated_confidence_neutral_concise_schema_answer_confidence_selfaware_seq_seed3_sft_merged_4b` | `experiments/stated-confidence-grpo/analysis/phase1-migrated/eval/results_amendment_b_stated_confidence_neutral_concise_schema_answer_confidence_selfaware_seq_seed3_sft_merged_4b` | 0.002 GB |
| `experiment/phase1/eval/results_amendment_b_stated_confidence_neutral_concise_schema_answer_confidence_selfaware_seq_seed3_sft_merged_4b_thinking_on` | `experiments/stated-confidence-grpo/analysis/phase1-migrated/eval/results_amendment_b_stated_confidence_neutral_concise_schema_answer_confidence_selfaware_seq_seed3_sft_merged_4b_thinking_on` | 0.002 GB |
| `experiment/phase1/eval/results_amendment_b_stated_confidence_neutral_concise_schema_selfaware_seed1_base_smoke_4b` | `experiments/stated-confidence-grpo/analysis/phase1-migrated/eval/results_amendment_b_stated_confidence_neutral_concise_schema_selfaware_seed1_base_smoke_4b` | 0.000 GB |
| `experiment/phase1/eval/results_amendment_b_stated_confidence_neutral_concise_selfaware_seed1_all_arms_4b` | `experiments/stated-confidence-grpo/analysis/phase1-migrated/eval/results_amendment_b_stated_confidence_neutral_concise_selfaware_seed1_all_arms_4b` | 0.003 GB |
| `experiment/phase1/eval/results_amendment_b_stated_confidence_neutral_concise_selfaware_seed1_base_smoke_4b` | `experiments/stated-confidence-grpo/analysis/phase1-migrated/eval/results_amendment_b_stated_confidence_neutral_concise_selfaware_seed1_base_smoke_4b` | 0.000 GB |
| `experiment/phase1/eval/results_amendment_b_stated_confidence_neutral_selfaware_seed1_base_smoke_4b` | `experiments/stated-confidence-grpo/analysis/phase1-migrated/eval/results_amendment_b_stated_confidence_neutral_selfaware_seed1_base_smoke_4b` | 0.000 GB |
| `experiment/phase1/eval/results_amendment_b_stated_confidence_selfaware_base_grpo_pilot_smoke_4b` | `experiments/stated-confidence-grpo/analysis/phase1-migrated/eval/results_amendment_b_stated_confidence_selfaware_base_grpo_pilot_smoke_4b` | 0.000 GB |
| `experiment/phase1/eval/results_amendment_b_stated_confidence_selfaware_seed1_all_arms_4b` | `experiments/stated-confidence-grpo/analysis/phase1-migrated/eval/results_amendment_b_stated_confidence_selfaware_seed1_all_arms_4b` | 0.002 GB |

</details>

## Shared infrastructure breakdown

Destination pattern: `archive/experiment/phase1-data/<path-under-experiment/phase1/>`
(root `.gitignore` now has a single blanket rule,
`archive/experiment/phase1-data/`, added by this change -- verified with
`git check-ignore`). A handful of entries outside `experiment/phase1/`
(none survived after the junk/empty-dir pass; see Junk below) would instead
land under `archive/experiment/<relpath>`.

Total: 157 entries, 54.99 GB.

<details><summary>Full shared entry list (src -> dest, size)</summary>

| Src | Dest | Size |
|---|---|---|
| `experiment/phase1/data/qwen3-4b-instruct` | `archive/experiment/phase1-data/data/qwen3-4b-instruct` | 0.036 GB |
| `experiment/phase1/data/tests` | `archive/experiment/phase1-data/data/tests` | 0.000 GB |
| `experiment/phase1/eval/.pytest_cache` | `archive/experiment/phase1-data/eval/.pytest_cache` | 0.000 GB |
| `experiment/phase1/eval/analysis` | `archive/experiment/phase1-data/eval/analysis` | 0.000 GB |
| `experiment/phase1/eval/logs` | `archive/experiment/phase1-data/eval/logs` | 0.045 GB |
| `experiment/phase1/eval/results_amendment_a_broader_ood_local_4b` | `archive/experiment/phase1-data/eval/results_amendment_a_broader_ood_local_4b` | 0.001 GB |
| `experiment/phase1/eval/results_amendment_a_selfaware_full_local_4b` | `archive/experiment/phase1-data/eval/results_amendment_a_selfaware_full_local_4b` | 0.004 GB |
| `experiment/phase1/eval/results_amendment_a_selfaware_full_seed2_sft_dpo_local_4b` | `archive/experiment/phase1-data/eval/results_amendment_a_selfaware_full_seed2_sft_dpo_local_4b` | 0.001 GB |
| `experiment/phase1/eval/results_amendment_a_selfaware_full_seed2_sft_dpo_lowmem_local_4b` | `archive/experiment/phase1-data/eval/results_amendment_a_selfaware_full_seed2_sft_dpo_lowmem_local_4b` | 0.001 GB |
| `experiment/phase1/eval/results_amendment_a_selfaware_full_seed2_sft_kto_lowmem_local_4b` | `archive/experiment/phase1-data/eval/results_amendment_a_selfaware_full_seed2_sft_kto_lowmem_local_4b` | 0.001 GB |
| `experiment/phase1/eval/results_amendment_a_selfaware_full_seed3_sft_dpo_local_4b` | `archive/experiment/phase1-data/eval/results_amendment_a_selfaware_full_seed3_sft_dpo_local_4b` | 0.001 GB |
| `experiment/phase1/eval/results_broader_ood_evidence_local_4b` | `archive/experiment/phase1-data/eval/results_broader_ood_evidence_local_4b` | 0.000 GB |
| `experiment/phase1/eval/results_kto_broader_ood_evidence_local_4b` | `archive/experiment/phase1-data/eval/results_kto_broader_ood_evidence_local_4b` | 0.000 GB |
| `experiment/phase1/eval/results_kto_selfaware_full_local_4b` | `archive/experiment/phase1-data/eval/results_kto_selfaware_full_local_4b` | 0.000 GB |
| `experiment/phase1/eval/results_ood_slice_local_4b` | `archive/experiment/phase1-data/eval/results_ood_slice_local_4b` | 0.000 GB |
| `experiment/phase1/eval/results_ood_slice_local_4b.failed_thinking_20260613_093939` | `archive/experiment/phase1-data/eval/results_ood_slice_local_4b.failed_thinking_20260613_093939` | 0.000 GB |
| `experiment/phase1/eval/results_parallel_selfaware_full_local_4b_20260615_2131` | `archive/experiment/phase1-data/eval/results_parallel_selfaware_full_local_4b_20260615_2131` | 0.005 GB |
| `experiment/phase1/eval/results_parallel_smoke_local_4b_20260615_2119` | `archive/experiment/phase1-data/eval/results_parallel_smoke_local_4b_20260615_2119` | 0.000 GB |
| `experiment/phase1/eval/results_selfaware_evidence_2240_192_local_4b` | `archive/experiment/phase1-data/eval/results_selfaware_evidence_2240_192_local_4b` | 0.000 GB |
| `experiment/phase1/eval/results_selfaware_full_local_4b` | `archive/experiment/phase1-data/eval/results_selfaware_full_local_4b` | 0.000 GB |
| `experiment/phase1/eval/results_selfaware_full_seed1_all_arms_4b_20260615_2148` | `archive/experiment/phase1-data/eval/results_selfaware_full_seed1_all_arms_4b_20260615_2148` | 0.005 GB |
| `experiment/phase1/eval/results_selfaware_full_seed2_all_arms_4b_20260615_2148` | `archive/experiment/phase1-data/eval/results_selfaware_full_seed2_all_arms_4b_20260615_2148` | 0.005 GB |
| `experiment/phase1/eval/results_selfaware_full_seed3_all_arms_4b_20260616_0615` | `archive/experiment/phase1-data/eval/results_selfaware_full_seed3_all_arms_4b_20260616_0615` | 0.005 GB |
| `experiment/phase1/eval/results_selfaware_mixed_slice_local_4b` | `archive/experiment/phase1-data/eval/results_selfaware_mixed_slice_local_4b` | 0.000 GB |
| `experiment/phase1/eval/results_sft_grouped_broader_ood_local_4b` | `archive/experiment/phase1-data/eval/results_sft_grouped_broader_ood_local_4b` | 0.000 GB |
| `experiment/phase1/eval/results_sft_grouped_selfaware_full_local_4b` | `archive/experiment/phase1-data/eval/results_sft_grouped_selfaware_full_local_4b` | 0.000 GB |
| `experiment/phase1/eval/results_sft_merged_seed2_lowmem_selfaware_192_sanity` | `archive/experiment/phase1-data/eval/results_sft_merged_seed2_lowmem_selfaware_192_sanity` | 0.000 GB |
| `experiment/phase1/eval/results_sft_merged_seed2_selfaware_192_sanity` | `archive/experiment/phase1-data/eval/results_sft_merged_seed2_selfaware_192_sanity` | 0.000 GB |
| `experiment/phase1/eval/results_smoke_local_4b` | `archive/experiment/phase1-data/eval/results_smoke_local_4b` | 0.000 GB |
| `experiment/phase1/eval/results_sycophancy_answer_seed1_all_arms_4b` | `archive/experiment/phase1-data/eval/results_sycophancy_answer_seed1_all_arms_4b` | 0.000 GB |
| `experiment/phase1/eval/results_sycophancy_answer_smoke_seed1_all_arms_4b` | `archive/experiment/phase1-data/eval/results_sycophancy_answer_smoke_seed1_all_arms_4b` | 0.000 GB |
| `experiment/phase1/eval/tests` | `archive/experiment/phase1-data/eval/tests` | 0.000 GB |
| `experiment/phase1/eval/tools` | `archive/experiment/phase1-data/eval/tools` | 0.000 GB |
| `experiment/phase1/grpo/.pytest_cache` | `archive/experiment/phase1-data/grpo/.pytest_cache` | 0.000 GB |
| `experiment/phase1/grpo/configs` | `archive/experiment/phase1-data/grpo/configs` | 0.000 GB |
| `experiment/phase1/grpo/tests` | `archive/experiment/phase1-data/grpo/tests` | 0.000 GB |
| `experiment/phase1/probe/.pytest_cache` | `archive/experiment/phase1-data/probe/.pytest_cache` | 0.000 GB |
| `experiment/phase1/probe/analysis/_dead_kbs_1782510040` | `archive/experiment/phase1-data/probe/analysis/_dead_kbs_1782510040` | 0.000 GB |
| `experiment/phase1/probe/analysis/_panels_knowledge_boundary` | `archive/experiment/phase1-data/probe/analysis/_panels_knowledge_boundary` | 0.001 GB |
| `experiment/phase1/probe/analysis/_xdataset_kuq_controls` | `archive/experiment/phase1-data/probe/analysis/_xdataset_kuq_controls` | 0.000 GB |
| `experiment/phase1/probe/analysis/current_clean_behavior_axis_directions` | `archive/experiment/phase1-data/probe/analysis/current_clean_behavior_axis_directions` | 0.000 GB |
| `experiment/phase1/probe/analysis/current_clean_behavior_axis_scan` | `archive/experiment/phase1-data/probe/analysis/current_clean_behavior_axis_scan` | 0.001 GB |
| `experiment/phase1/probe/analysis/current_clean_dpo_grpo_unknown_failure_prompt_matched_behavior_axis_scan` | `archive/experiment/phase1-data/probe/analysis/current_clean_dpo_grpo_unknown_failure_prompt_matched_behavior_axis_scan` | 0.000 GB |
| `experiment/phase1/probe/analysis/current_clean_dpo_grpo_unknown_failure_prompt_matched_multicell_readout` | `archive/experiment/phase1-data/probe/analysis/current_clean_dpo_grpo_unknown_failure_prompt_matched_multicell_readout` | 0.001 GB |
| `experiment/phase1/probe/analysis/current_clean_grpo_dpo_unknown_failure_prompt_matched_behavior_axis_scan` | `archive/experiment/phase1-data/probe/analysis/current_clean_grpo_dpo_unknown_failure_prompt_matched_behavior_axis_scan` | 0.000 GB |
| `experiment/phase1/probe/analysis/current_clean_grpo_dpo_unknown_failure_prompt_matched_multicell_readout` | `archive/experiment/phase1-data/probe/analysis/current_clean_grpo_dpo_unknown_failure_prompt_matched_multicell_readout` | 0.001 GB |
| `experiment/phase1/probe/analysis/current_clean_grpo_v2_caution_perp_residual_intervention` | `archive/experiment/phase1-data/probe/analysis/current_clean_grpo_v2_caution_perp_residual_intervention` | 0.001 GB |
| `experiment/phase1/probe/analysis/current_clean_grpo_v2_caution_residual_direction` | `archive/experiment/phase1-data/probe/analysis/current_clean_grpo_v2_caution_residual_direction` | 0.000 GB |
| `experiment/phase1/probe/analysis/current_clean_grpo_v2_caution_residual_intervention` | `archive/experiment/phase1-data/probe/analysis/current_clean_grpo_v2_caution_residual_intervention` | 0.001 GB |
| `experiment/phase1/probe/analysis/current_clean_grpo_v2_caution_residual_read_trajectory` | `archive/experiment/phase1-data/probe/analysis/current_clean_grpo_v2_caution_residual_read_trajectory` | 0.000 GB |
| `experiment/phase1/probe/analysis/current_clean_grpo_v2_knowledge_boundary_steer` | `archive/experiment/phase1-data/probe/analysis/current_clean_grpo_v2_knowledge_boundary_steer` | 0.000 GB |
| `experiment/phase1/probe/analysis/current_clean_grpo_v2_known_overrefusal_generation_replay_96` | `archive/experiment/phase1-data/probe/analysis/current_clean_grpo_v2_known_overrefusal_generation_replay_96` | 0.003 GB |
| `experiment/phase1/probe/analysis/current_clean_grpo_v2_known_overrefusal_generation_replay_96_coeff_sweep` | `archive/experiment/phase1-data/probe/analysis/current_clean_grpo_v2_known_overrefusal_generation_replay_96_coeff_sweep` | 0.006 GB |
| `experiment/phase1/probe/analysis/current_clean_grpo_v2_known_overrefusal_layer_window_normed_directions` | `archive/experiment/phase1-data/probe/analysis/current_clean_grpo_v2_known_overrefusal_layer_window_normed_directions` | 0.000 GB |
| `experiment/phase1/probe/analysis/current_clean_grpo_v2_known_overrefusal_multilayer_band_generation` | `archive/experiment/phase1-data/probe/analysis/current_clean_grpo_v2_known_overrefusal_multilayer_band_generation` | 0.008 GB |
| `experiment/phase1/probe/analysis/current_clean_grpo_v2_known_overrefusal_native_l26_coeff_sweep` | `archive/experiment/phase1-data/probe/analysis/current_clean_grpo_v2_known_overrefusal_native_l26_coeff_sweep` | 0.008 GB |
| `experiment/phase1/probe/analysis/current_clean_grpo_v2_known_overrefusal_native_l26_panel_b_coeff_sweep` | `archive/experiment/phase1-data/probe/analysis/current_clean_grpo_v2_known_overrefusal_native_l26_panel_b_coeff_sweep` | 0.008 GB |
| `experiment/phase1/probe/analysis/current_clean_grpo_v2_known_overrefusal_native_l26_panel_b_generation` | `archive/experiment/phase1-data/probe/analysis/current_clean_grpo_v2_known_overrefusal_native_l26_panel_b_generation` | 0.002 GB |
| `experiment/phase1/probe/analysis/current_clean_grpo_v2_known_overrefusal_native_layer_window_generation` | `archive/experiment/phase1-data/probe/analysis/current_clean_grpo_v2_known_overrefusal_native_layer_window_generation` | 0.010 GB |
| `experiment/phase1/probe/analysis/current_clean_grpo_v2_known_overrefusal_shifted_layer_generation_control` | `archive/experiment/phase1-data/probe/analysis/current_clean_grpo_v2_known_overrefusal_shifted_layer_generation_control` | 0.010 GB |
| `experiment/phase1/probe/analysis/current_clean_grpo_v2_l26_double_orthogonalized_panel_a_generation` | `archive/experiment/phase1-data/probe/analysis/current_clean_grpo_v2_l26_double_orthogonalized_panel_a_generation` | 0.006 GB |
| `experiment/phase1/probe/analysis/current_clean_grpo_v2_l26_double_orthogonalized_panel_b_generation` | `archive/experiment/phase1-data/probe/analysis/current_clean_grpo_v2_l26_double_orthogonalized_panel_b_generation` | 0.006 GB |
| `experiment/phase1/probe/analysis/current_clean_grpo_v2_l26_double_orthogonalized_panel_c_generation` | `archive/experiment/phase1-data/probe/analysis/current_clean_grpo_v2_l26_double_orthogonalized_panel_c_generation` | 0.002 GB |
| `experiment/phase1/probe/analysis/current_clean_grpo_v2_l26_double_orthogonalized_panel_d_coeff_placement_sweep` | `archive/experiment/phase1-data/probe/analysis/current_clean_grpo_v2_l26_double_orthogonalized_panel_d_coeff_placement_sweep` | 0.024 GB |
| `experiment/phase1/probe/analysis/current_clean_grpo_v2_l26_double_orthogonalized_panel_d_generation` | `archive/experiment/phase1-data/probe/analysis/current_clean_grpo_v2_l26_double_orthogonalized_panel_d_generation` | 0.004 GB |
| `experiment/phase1/probe/analysis/current_clean_grpo_v2_l26_double_orthogonalized_shifted_layer_panel_c_generation` | `archive/experiment/phase1-data/probe/analysis/current_clean_grpo_v2_l26_double_orthogonalized_shifted_layer_panel_c_generation` | 0.010 GB |
| `experiment/phase1/probe/analysis/current_clean_grpo_v2_l26_double_orthogonalized_shifted_layer_panel_d_generation` | `archive/experiment/phase1-data/probe/analysis/current_clean_grpo_v2_l26_double_orthogonalized_shifted_layer_panel_d_generation` | 0.008 GB |
| `experiment/phase1/probe/analysis/current_clean_grpo_v2_l26_orthogonalized_panel_a_generation` | `archive/experiment/phase1-data/probe/analysis/current_clean_grpo_v2_l26_orthogonalized_panel_a_generation` | 0.002 GB |
| `experiment/phase1/probe/analysis/current_clean_grpo_v2_l26_orthogonalized_panel_b_generation` | `archive/experiment/phase1-data/probe/analysis/current_clean_grpo_v2_l26_orthogonalized_panel_b_generation` | 0.008 GB |
| `experiment/phase1/probe/analysis/current_clean_grpo_v2_l26_repair_multi_protect_directions` | `archive/experiment/phase1-data/probe/analysis/current_clean_grpo_v2_l26_repair_multi_protect_directions` | 0.000 GB |
| `experiment/phase1/probe/analysis/current_clean_grpo_v2_l26_repair_multi_protect_scan` | `archive/experiment/phase1-data/probe/analysis/current_clean_grpo_v2_l26_repair_multi_protect_scan` | 0.000 GB |
| `experiment/phase1/probe/analysis/current_clean_grpo_v2_l26_repair_orthogonalized_to_unknown_refusal` | `archive/experiment/phase1-data/probe/analysis/current_clean_grpo_v2_l26_repair_orthogonalized_to_unknown_refusal` | 0.000 GB |
| `experiment/phase1/probe/analysis/current_clean_grpo_v2_l26_repair_orthogonalized_to_unknown_refusal_and_known_wrong` | `archive/experiment/phase1-data/probe/analysis/current_clean_grpo_v2_l26_repair_orthogonalized_to_unknown_refusal_and_known_wrong` | 0.000 GB |
| `experiment/phase1/probe/analysis/current_clean_grpo_v2_l26_repair_protect_directions` | `archive/experiment/phase1-data/probe/analysis/current_clean_grpo_v2_l26_repair_protect_directions` | 0.000 GB |
| `experiment/phase1/probe/analysis/current_clean_grpo_v2_latent_knowledge_probe` | `archive/experiment/phase1-data/probe/analysis/current_clean_grpo_v2_latent_knowledge_probe` | 0.000 GB |
| `experiment/phase1/probe/analysis/current_clean_grpo_v2_unknown_failure_behavior_axis_scan` | `archive/experiment/phase1-data/probe/analysis/current_clean_grpo_v2_unknown_failure_behavior_axis_scan` | 0.000 GB |
| `experiment/phase1/probe/analysis/current_clean_grpo_v2_unknown_failure_directions` | `archive/experiment/phase1-data/probe/analysis/current_clean_grpo_v2_unknown_failure_directions` | 0.000 GB |
| `experiment/phase1/probe/analysis/current_clean_grpo_v2_unknown_failure_l16_generation_replay` | `archive/experiment/phase1-data/probe/analysis/current_clean_grpo_v2_unknown_failure_l16_generation_replay` | 0.004 GB |
| `experiment/phase1/probe/analysis/current_clean_grpo_v2_unknown_failure_logit_diagnostic` | `archive/experiment/phase1-data/probe/analysis/current_clean_grpo_v2_unknown_failure_logit_diagnostic` | 0.197 GB |
| `experiment/phase1/probe/analysis/current_clean_grpo_v2_unknown_failure_prompt_matched_behavior_axis_scan` | `archive/experiment/phase1-data/probe/analysis/current_clean_grpo_v2_unknown_failure_prompt_matched_behavior_axis_scan` | 0.000 GB |
| `experiment/phase1/probe/analysis/current_clean_grpo_v2_unknown_failure_prompt_matched_directions` | `archive/experiment/phase1-data/probe/analysis/current_clean_grpo_v2_unknown_failure_prompt_matched_directions` | 0.000 GB |
| `experiment/phase1/probe/analysis/current_clean_grpo_v2_unknown_failure_prompt_matched_generation_replay` | `archive/experiment/phase1-data/probe/analysis/current_clean_grpo_v2_unknown_failure_prompt_matched_generation_replay` | 0.014 GB |
| `experiment/phase1/probe/analysis/current_clean_grpo_v2_unknown_failure_prompt_matched_head_axis_geometry` | `archive/experiment/phase1-data/probe/analysis/current_clean_grpo_v2_unknown_failure_prompt_matched_head_axis_geometry` | 0.000 GB |
| `experiment/phase1/probe/analysis/current_clean_grpo_v2_unknown_failure_prompt_matched_head_intervention_sweep` | `archive/experiment/phase1-data/probe/analysis/current_clean_grpo_v2_unknown_failure_prompt_matched_head_intervention_sweep` | 0.000 GB |
| `experiment/phase1/probe/analysis/current_clean_grpo_v2_unknown_failure_prompt_matched_head_intervention_sweep_randomctl` | `archive/experiment/phase1-data/probe/analysis/current_clean_grpo_v2_unknown_failure_prompt_matched_head_intervention_sweep_randomctl` | 0.000 GB |
| `experiment/phase1/probe/analysis/current_clean_grpo_v2_unknown_failure_prompt_matched_head_intervention_sweep_randomctl_normmatched` | `archive/experiment/phase1-data/probe/analysis/current_clean_grpo_v2_unknown_failure_prompt_matched_head_intervention_sweep_randomctl_normmatched` | 0.000 GB |
| `experiment/phase1/probe/analysis/current_clean_grpo_v2_unknown_failure_prompt_matched_head_localization_scan` | `archive/experiment/phase1-data/probe/analysis/current_clean_grpo_v2_unknown_failure_prompt_matched_head_localization_scan` | 0.008 GB |
| `experiment/phase1/probe/analysis/current_clean_grpo_v2_unknown_failure_prompt_matched_head_read_projection` | `archive/experiment/phase1-data/probe/analysis/current_clean_grpo_v2_unknown_failure_prompt_matched_head_read_projection` | 0.000 GB |
| `experiment/phase1/probe/analysis/current_clean_grpo_v2_unknown_failure_prompt_matched_head_read_trajectory` | `archive/experiment/phase1-data/probe/analysis/current_clean_grpo_v2_unknown_failure_prompt_matched_head_read_trajectory` | 0.000 GB |
| `experiment/phase1/probe/analysis/current_clean_grpo_v2_unknown_failure_prompt_matched_head_read_trajectory_sft_base` | `archive/experiment/phase1-data/probe/analysis/current_clean_grpo_v2_unknown_failure_prompt_matched_head_read_trajectory_sft_base` | 0.000 GB |
| `experiment/phase1/probe/analysis/current_clean_grpo_v2_unknown_failure_prompt_matched_head_steering_directions` | `archive/experiment/phase1-data/probe/analysis/current_clean_grpo_v2_unknown_failure_prompt_matched_head_steering_directions` | 0.000 GB |
| `experiment/phase1/probe/analysis/current_clean_grpo_v2_unknown_failure_prompt_matched_head_steering_directions_randomctl` | `archive/experiment/phase1-data/probe/analysis/current_clean_grpo_v2_unknown_failure_prompt_matched_head_steering_directions_randomctl` | 0.000 GB |
| `experiment/phase1/probe/analysis/current_clean_grpo_v2_unknown_failure_prompt_matched_head_steering_directions_randomctl_normmatched` | `archive/experiment/phase1-data/probe/analysis/current_clean_grpo_v2_unknown_failure_prompt_matched_head_steering_directions_randomctl_normmatched` | 0.000 GB |
| `experiment/phase1/probe/analysis/current_clean_grpo_v2_unknown_failure_prompt_matched_l26_constrained_generation_replay` | `archive/experiment/phase1-data/probe/analysis/current_clean_grpo_v2_unknown_failure_prompt_matched_l26_constrained_generation_replay` | 0.007 GB |
| `experiment/phase1/probe/analysis/current_clean_grpo_v2_unknown_failure_prompt_matched_l26_constrained_unknown_repair` | `archive/experiment/phase1-data/probe/analysis/current_clean_grpo_v2_unknown_failure_prompt_matched_l26_constrained_unknown_repair` | 0.000 GB |
| `experiment/phase1/probe/analysis/current_clean_grpo_v2_unknown_failure_prompt_matched_l26_multicell_directions` | `archive/experiment/phase1-data/probe/analysis/current_clean_grpo_v2_unknown_failure_prompt_matched_l26_multicell_directions` | 0.000 GB |
| `experiment/phase1/probe/analysis/current_clean_grpo_v2_unknown_failure_prompt_matched_logit_diagnostic` | `archive/experiment/phase1-data/probe/analysis/current_clean_grpo_v2_unknown_failure_prompt_matched_logit_diagnostic` | 0.148 GB |
| `experiment/phase1/probe/analysis/current_clean_grpo_v2_unknown_failure_prompt_matched_multicell_readout` | `archive/experiment/phase1-data/probe/analysis/current_clean_grpo_v2_unknown_failure_prompt_matched_multicell_readout` | 0.001 GB |
| `experiment/phase1/probe/analysis/current_clean_known_overrefusal_generation_replay` | `archive/experiment/phase1-data/probe/analysis/current_clean_known_overrefusal_generation_replay` | 0.002 GB |
| `experiment/phase1/probe/analysis/current_clean_known_overrefusal_logit_diagnostic` | `archive/experiment/phase1-data/probe/analysis/current_clean_known_overrefusal_logit_diagnostic` | 0.036 GB |
| `experiment/phase1/probe/analysis/current_clean_known_overrefusal_normed_directions` | `archive/experiment/phase1-data/probe/analysis/current_clean_known_overrefusal_normed_directions` | 0.000 GB |
| `experiment/phase1/probe/analysis/current_clean_kto_grpo_unknown_failure_prompt_matched_behavior_axis_scan` | `archive/experiment/phase1-data/probe/analysis/current_clean_kto_grpo_unknown_failure_prompt_matched_behavior_axis_scan` | 0.000 GB |
| `experiment/phase1/probe/analysis/current_clean_kto_grpo_unknown_failure_prompt_matched_multicell_readout` | `archive/experiment/phase1-data/probe/analysis/current_clean_kto_grpo_unknown_failure_prompt_matched_multicell_readout` | 0.001 GB |
| `experiment/phase1/probe/analysis/current_clean_kto_unknown_failure_prompt_matched_behavior_axis_scan` | `archive/experiment/phase1-data/probe/analysis/current_clean_kto_unknown_failure_prompt_matched_behavior_axis_scan` | 0.000 GB |
| `experiment/phase1/probe/analysis/current_clean_kto_unknown_failure_prompt_matched_directions` | `archive/experiment/phase1-data/probe/analysis/current_clean_kto_unknown_failure_prompt_matched_directions` | 0.000 GB |
| `experiment/phase1/probe/analysis/current_clean_kto_unknown_failure_prompt_matched_generation_replay` | `archive/experiment/phase1-data/probe/analysis/current_clean_kto_unknown_failure_prompt_matched_generation_replay` | 0.010 GB |
| `experiment/phase1/probe/analysis/current_clean_kto_unknown_failure_prompt_matched_multicell_readout` | `archive/experiment/phase1-data/probe/analysis/current_clean_kto_unknown_failure_prompt_matched_multicell_readout` | 0.001 GB |
| `experiment/phase1/probe/analysis/current_selfaware_behavior_rows` | `archive/experiment/phase1-data/probe/analysis/current_selfaware_behavior_rows` | 0.018 GB |
| `experiment/phase1/probe/analysis/dark_displacement_census` | `archive/experiment/phase1-data/probe/analysis/dark_displacement_census` | 0.001 GB |
| `experiment/phase1/probe/analysis/hydra_census_stage1` | `archive/experiment/phase1-data/probe/analysis/hydra_census_stage1` | 0.000 GB |
| `experiment/phase1/probe/analysis/mi_category_geometry_20260704` | `archive/experiment/phase1-data/probe/analysis/mi_category_geometry_20260704` | 2.118 GB |
| `experiment/phase1/probe/analysis/mi_confab_phenotypes_20260704` | `archive/experiment/phase1-data/probe/analysis/mi_confab_phenotypes_20260704` | 0.000 GB |
| `experiment/phase1/probe/analysis/mi_confab_signature_20260704` | `archive/experiment/phase1-data/probe/analysis/mi_confab_signature_20260704` | 0.000 GB |
| `experiment/phase1/probe/analysis/mi_controversial_flips_20260704` | `archive/experiment/phase1-data/probe/analysis/mi_controversial_flips_20260704` | 0.000 GB |
| `experiment/phase1/probe/analysis/mi_exploration_20260703` | `archive/experiment/phase1-data/probe/analysis/mi_exploration_20260703` | 0.000 GB |
| `experiment/phase1/probe/analysis/mi_familiarity_geometry_20260704` | `archive/experiment/phase1-data/probe/analysis/mi_familiarity_geometry_20260704` | 0.000 GB |
| `experiment/phase1/probe/analysis/mi_veto_transport_20260704` | `archive/experiment/phase1-data/probe/analysis/mi_veto_transport_20260704` | 0.000 GB |
| `experiment/phase1/probe/analysis/model_variation_inventory.csv` | `archive/experiment/phase1-data/probe/analysis/model_variation_inventory.csv` | 0.000 GB |
| `experiment/phase1/probe/analysis/p3_section5_provenance_20260704` | `archive/experiment/phase1-data/probe/analysis/p3_section5_provenance_20260704` | 0.000 GB |
| `experiment/phase1/probe/analysis/paper3_section5_geometry` | `archive/experiment/phase1-data/probe/analysis/paper3_section5_geometry` | 0.000 GB |
| `experiment/phase1/probe/analysis/par_design` | `archive/experiment/phase1-data/probe/analysis/par_design` | 0.004 GB |
| `experiment/phase1/probe/analysis/par_mining` | `archive/experiment/phase1-data/probe/analysis/par_mining` | 3.345 GB |
| `experiment/phase1/probe/analysis/par_recalibration` | `archive/experiment/phase1-data/probe/analysis/par_recalibration` | 3.040 GB |
| `experiment/phase1/probe/analysis/par_sensor_refit` | `archive/experiment/phase1-data/probe/analysis/par_sensor_refit` | 20.100 GB |
| `experiment/phase1/probe/analysis/radial_ceiling_sim_20260704` | `archive/experiment/phase1-data/probe/analysis/radial_ceiling_sim_20260704` | 0.000 GB |
| `experiment/phase1/probe/analysis/thinking_audit_128_1024` | `archive/experiment/phase1-data/probe/analysis/thinking_audit_128_1024` | 0.000 GB |
| `experiment/phase1/probe/analysis/veto_warning_policy_20260704` | `archive/experiment/phase1-data/probe/analysis/veto_warning_policy_20260704` | 0.000 GB |
| `experiment/phase1/probe/assets` | `archive/experiment/phase1-data/probe/assets` | 0.024 GB |
| `experiment/phase1/probe/config` | `archive/experiment/phase1-data/probe/config` | 0.002 GB |
| `experiment/phase1/probe/logs` | `archive/experiment/phase1-data/probe/logs` | 0.002 GB |
| `experiment/phase1/probe/manifests` | `archive/experiment/phase1-data/probe/manifests` | 0.002 GB |
| `experiment/phase1/probe/qwen3-1.7b-bnb-4bit` | `archive/experiment/phase1-data/probe/qwen3-1.7b-bnb-4bit` | 1.366 GB |
| `experiment/phase1/probe/qwen3-14b-bnb-4bit` | `archive/experiment/phase1-data/probe/qwen3-14b-bnb-4bit` | 4.709 GB |
| `experiment/phase1/probe/qwen3-4b-clean-sft-dpo-grpo-seed1-selfaware` | `archive/experiment/phase1-data/probe/qwen3-4b-clean-sft-dpo-grpo-seed1-selfaware` | 0.273 GB |
| `experiment/phase1/probe/qwen3-4b-clean-sft-grpo-dpo-seed1-selfaware` | `archive/experiment/phase1-data/probe/qwen3-4b-clean-sft-grpo-dpo-seed1-selfaware` | 1.593 GB |
| `experiment/phase1/probe/qwen3-4b-clean-sft-grpo-v2` | `archive/experiment/phase1-data/probe/qwen3-4b-clean-sft-grpo-v2` | 1.358 GB |
| `experiment/phase1/probe/qwen3-4b-clean-sft-grpo-v2-seed1-kuq` | `archive/experiment/phase1-data/probe/qwen3-4b-clean-sft-grpo-v2-seed1-kuq` | 1.067 GB |
| `experiment/phase1/probe/qwen3-4b-clean-sft-grpo-v2-seed1-selfaware` | `archive/experiment/phase1-data/probe/qwen3-4b-clean-sft-grpo-v2-seed1-selfaware` | 2.290 GB |
| `experiment/phase1/probe/qwen3-4b-clean-sft-kto-grpo-seed1-selfaware` | `archive/experiment/phase1-data/probe/qwen3-4b-clean-sft-kto-grpo-seed1-selfaware` | 0.273 GB |
| `experiment/phase1/probe/qwen3-4b-clean-sft-kto-seed1-selfaware` | `archive/experiment/phase1-data/probe/qwen3-4b-clean-sft-kto-seed1-selfaware` | 0.273 GB |
| `experiment/phase1/probe/qwen3-4b-clean-sft-seed1-selfaware` | `archive/experiment/phase1-data/probe/qwen3-4b-clean-sft-seed1-selfaware` | 1.320 GB |
| `experiment/phase1/probe/qwen3-4b-instruct` | `archive/experiment/phase1-data/probe/qwen3-4b-instruct` | 4.417 GB |
| `experiment/phase1/probe/qwen3-4b-instruct-sycophancy-answer` | `archive/experiment/phase1-data/probe/qwen3-4b-instruct-sycophancy-answer` | 0.026 GB |
| `experiment/phase1/probe/qwen3-4b-instruct-sycophancy-answer-kto-seed1` | `archive/experiment/phase1-data/probe/qwen3-4b-instruct-sycophancy-answer-kto-seed1` | 0.090 GB |
| `experiment/phase1/probe/qwen3-4b-instruct-sycophancy-answer-sft-seed1` | `archive/experiment/phase1-data/probe/qwen3-4b-instruct-sycophancy-answer-sft-seed1` | 0.090 GB |
| `experiment/phase1/probe/qwen3-4b-instruct-thinking-audit-128-1024` | `archive/experiment/phase1-data/probe/qwen3-4b-instruct-thinking-audit-128-1024` | 0.010 GB |
| `experiment/phase1/probe/qwen3-4b-instruct-thinking-audit-512` | `archive/experiment/phase1-data/probe/qwen3-4b-instruct-thinking-audit-512` | 0.000 GB |
| `experiment/phase1/probe/qwen3-4b-instruct_thinking_contaminated_20260611-1004` | `archive/experiment/phase1-data/probe/qwen3-4b-instruct_thinking_contaminated_20260611-1004` | 0.013 GB |
| `experiment/phase1/probe/qwen3-4b-instruct_uncapped_partial_20260611-0843` | `archive/experiment/phase1-data/probe/qwen3-4b-instruct_uncapped_partial_20260611-0843` | 0.004 GB |
| `experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware` | `archive/experiment/phase1-data/probe/qwen3-4b-sft-merged-seed1-selfaware` | 3.056 GB |
| `experiment/phase1/probe/qwen3-8b-bnb-4bit` | `archive/experiment/phase1-data/probe/qwen3-8b-bnb-4bit` | 3.403 GB |
| `experiment/phase1/probe/steering` | `archive/experiment/phase1-data/probe/steering` | 0.020 GB |
| `experiment/phase1/probe/tests` | `archive/experiment/phase1-data/probe/tests` | 0.002 GB |
| `experiment/phase1/probe/xdataset` | `archive/experiment/phase1-data/probe/xdataset` | 0.001 GB |
| `experiment/phase1/run_records/launch_logs` | `archive/experiment/phase1-data/run_records/launch_logs` | 0.000 GB |
| `experiment/phase1/run_records/logs` | `archive/experiment/phase1-data/run_records/logs` | 0.004 GB |
| `experiment/phase1/tools/tests` | `archive/experiment/phase1-data/tools/tests` | 0.000 GB |

</details>

### Unmapped-but-letter-shaped (flagged, not guessed)

Directories whose leading token is a bare 1-2 letter lowercase segment (the
only shape any real amendment letter can take) but which does not match a
key in the letter -> slug table above. Classified `shared`, not deleted or
reassigned -- worth a human look before or after the move:

| Src | candidate_letter | Note |
|---|---|---|
| `experiment/phase1/eval/results_amendment_a_broader_ood_local_4b` | A | no amendment A; reads as the locked headline-matrix eval output |
| `experiment/phase1/eval/results_amendment_a_selfaware_full_local_4b` | A | no amendment A; reads as the locked headline-matrix eval output |
| `experiment/phase1/eval/results_amendment_a_selfaware_full_seed2_sft_dpo_local_4b` | A | no amendment A; reads as the locked headline-matrix eval output |
| `experiment/phase1/eval/results_amendment_a_selfaware_full_seed2_sft_dpo_lowmem_local_4b` | A | no amendment A; reads as the locked headline-matrix eval output |
| `experiment/phase1/eval/results_amendment_a_selfaware_full_seed2_sft_kto_lowmem_local_4b` | A | no amendment A; reads as the locked headline-matrix eval output |
| `experiment/phase1/eval/results_amendment_a_selfaware_full_seed3_sft_dpo_local_4b` | A | no amendment A; reads as the locked headline-matrix eval output |
| `experiment/phase1/probe/analysis/mi_category_geometry_20260704` | MI | no amendment MI; reads as ad hoc mechanistic-interpretability exploration |
| `experiment/phase1/probe/analysis/mi_confab_phenotypes_20260704` | MI | no amendment MI; reads as ad hoc mechanistic-interpretability exploration |
| `experiment/phase1/probe/analysis/mi_confab_signature_20260704` | MI | no amendment MI; reads as ad hoc mechanistic-interpretability exploration |
| `experiment/phase1/probe/analysis/mi_controversial_flips_20260704` | MI | no amendment MI; reads as ad hoc mechanistic-interpretability exploration |
| `experiment/phase1/probe/analysis/mi_exploration_20260703` | MI | no amendment MI; reads as ad hoc mechanistic-interpretability exploration |
| `experiment/phase1/probe/analysis/mi_familiarity_geometry_20260704` | MI | no amendment MI; reads as ad hoc mechanistic-interpretability exploration |
| `experiment/phase1/probe/analysis/mi_veto_transport_20260704` | MI | no amendment MI; reads as ad hoc mechanistic-interpretability exploration |

## Junk (to be deleted in phase 2)

Listed here **before** any deletion, per instruction. Two categories:

1. Every `__pycache__` directory anywhere under `experiment/` (22 found).
2. Marimo-dashboard export + PWA boilerplate directly under
   `experiment/phase1/probe/` (14 files/dirs) -- the exact same category the
   project already treats as regenerable and gitignores for the frozen
   legacy copy at `archive/experiment/phase1/probe/` (see the existing
   `.gitignore` comment "marimo dashboard runtime cache + exported web
   bundle boilerplate (regenerable)"). `sae_dashboard.py`, `.nojekyll`,
   `CLAUDE.md`, and `manifest.json` are included on that same precedent
   even though the migration brief's prose only named
   `sae_dashboard.html/.py favicons/webmanifest/logo/android-chrome/apple-touch`
   explicitly -- flagged here for lead veto before `--execute`.
3. Three directories that become empty once (1) and (2) are removed:
   `experiment/experiment/` (0 files to begin with),
   `experiment/paper/` (only ever contained `scripts/__pycache__`), and
   `experiment/phase1/analysis/` (only ever contained one stray `.pyc`).

Total: 38 entries, 0.01 GB.

| Src | Note |
|---|---|
| `experiment/experiment` | empty after junk removal |
| `experiment/paper` | empty after junk removal |
| `experiment/paper/scripts/__pycache__` | __pycache__ |
| `experiment/phase1/analysis` | empty after junk removal |
| `experiment/phase1/analysis/__pycache__` | __pycache__ |
| `experiment/phase1/data/__pycache__` | __pycache__ |
| `experiment/phase1/data/tests/__pycache__` | __pycache__ |
| `experiment/phase1/eval/__pycache__` | __pycache__ |
| `experiment/phase1/eval/analysis/__pycache__` | __pycache__ |
| `experiment/phase1/eval/analysis/unknown_question_labels/__pycache__` | __pycache__ |
| `experiment/phase1/eval/tests/__pycache__` | __pycache__ |
| `experiment/phase1/eval/tools/__pycache__` | __pycache__ |
| `experiment/phase1/grpo/__pycache__` | __pycache__ |
| `experiment/phase1/grpo/configs/__pycache__` | __pycache__ |
| `experiment/phase1/grpo/tests/__pycache__` | __pycache__ |
| `experiment/phase1/probe/.nojekyll` | probe-root boilerplate |
| `experiment/phase1/probe/CLAUDE.md` | probe-root boilerplate |
| `experiment/phase1/probe/__marimo__` | probe-root boilerplate |
| `experiment/phase1/probe/__pycache__` | __pycache__ |
| `experiment/phase1/probe/analysis/__pycache__` | __pycache__ |
| `experiment/phase1/probe/analysis/mi_category_geometry_20260704/flavor_readout/__pycache__` | __pycache__ |
| `experiment/phase1/probe/analysis/mi_veto_transport_20260704/__pycache__` | __pycache__ |
| `experiment/phase1/probe/android-chrome-192x192.png` | probe-root boilerplate |
| `experiment/phase1/probe/android-chrome-512x512.png` | probe-root boilerplate |
| `experiment/phase1/probe/apple-touch-icon.png` | probe-root boilerplate |
| `experiment/phase1/probe/favicon-16x16.png` | probe-root boilerplate |
| `experiment/phase1/probe/favicon-32x32.png` | probe-root boilerplate |
| `experiment/phase1/probe/favicon.ico` | probe-root boilerplate |
| `experiment/phase1/probe/logo.png` | probe-root boilerplate |
| `experiment/phase1/probe/manifest.json` | probe-root boilerplate |
| `experiment/phase1/probe/sae_dashboard.html` | probe-root boilerplate |
| `experiment/phase1/probe/site.webmanifest` | probe-root boilerplate |
| `experiment/phase1/probe/steering/__pycache__` | __pycache__ |
| `experiment/phase1/probe/steering/tests/__pycache__` | __pycache__ |
| `experiment/phase1/probe/tests/__pycache__` | __pycache__ |
| `experiment/phase1/run_records/logs/__pycache__` | __pycache__ |
| `experiment/phase1/tools/__pycache__` | __pycache__ |
| `experiment/phase1/tools/tests/__pycache__` | __pycache__ |

### Conservative non-junk calls (flagged for the lead, not deleted)

Not deleted because the migration brief did not name them explicitly, even
though they resemble disposable build artifacts elsewhere in the repo's own
`.gitignore` precedent. Currently classified `shared` (archived, not
deleted):

- `experiment/phase1/probe/assets/` (27 MB) -- the marimo web-app JS/CSS/font
  bundle; the existing `.gitignore` calls the equivalent legacy-copy path
  "web-app bundle dump (log-viewer artifact; not experiment data)".
- Every `.pytest_cache/` directory under `experiment/` (not swept the way
  `__pycache__` was, since the brief named only the latter).

## Phase 2 command

Once the lead approves this plan:

```
python3 bin/migrate_phase1_outputs.py --execute
```

Idempotent: re-running (dry-run or `--execute`) after a partial or full
apply treats any entry whose source no longer exists as
`already-migrated` and skips it; any entry whose destination already
exists is left in place and reported as a `collision` rather than
overwritten.

## Execution record (2026-07-12, lead)

Executed by the lead after manifest review. Outcome:

- 317 of 319 entries completed: per-amendment renames into
  `experiments/<slug>/analysis/phase1-migrated/` (43.9 GB, largest:
  sampled-decode-seed-robustness 26 GB, cross-family-confirmatory 8.6 GB,
  divergent-pool-own-readout 6.7 GB), shared infrastructure into
  `archive/experiment/phase1-data/` (56 GB), junk deleted per the list
  above. `bin/exp validate` OK (63 experiments) post-move.
- 2 entries (the Amendment AI PAR eval dirs
  `results_amendment_ai_response_confidence_selfaware_par_{permuted,true}_seed1_corrected_base_full_4b`)
  contain 14 files owned by a foreign UID (Docker-era root writes), so the
  source dirs cannot be unlinked without sudo. Both were COPIED to their
  `experiments/probe-as-reward/analysis/phase1-migrated/eval/` destinations
  and verified (byte-compare clean; the destination copies are
  authoritative). The residue under `experiment/` awaits a one-time
  `sudo rm -rf experiment` by the operator; nothing else remains in that
  tree (8 files, 5.4 MB, all inside the two foreign-owned dirs).
- Gotcha recorded: `shutil.move` falls back to copy-then-rmtree when
  rename fails, and rmtree dies on foreign-owned entries; the pre-move
  ownership scan (`find ! -user $USER`) belongs in any future bulk-move
  script.
