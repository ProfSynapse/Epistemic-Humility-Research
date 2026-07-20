# Correctness discriminative-subspace overlap across training checkpoints

Smoke mode: True. Metric: Grassmann projection (mean squared cosine of
principal angles). Position: post-generation only. Seeds: PCA/fold 20260719, bootstrap/permutation/isotropic 20260720, robustness 20260721.

## Class balance (per stage)

| stage | rows | correct | wrong | floor (>=150/150) |
|---|---|---|---|---|
| raw | 1823 | 500 | 1323 | True |
| cleansft | 1250 | 750 | 500 | True |
| grpov2 | 1488 | 988 | 500 | True |
| partrue | 1217 | 500 | 717 | True |
| s | 1836 | 500 | 1336 | True |

## Core AUROC and retained variance by layer by stage (PCA-128)

| layer | raw | cleansft | grpov2 | partrue | s |
|---|---|---|---|---|---|
| L20 | 0.8402 | 0.8088 | 0.8144 | 0.8102 | 0.8403 |
| L21 | 0.8444 | 0.8060 | 0.8209 | 0.8152 | 0.8450 |

## S->T bracket overlap by k (gate layers, k_gate=4)

| layer | k=1 | k=4 |
|---|---|---|
| L20 | 0.0099 | 0.0075 |
| L21 | 0.0044 | 0.0040 |

## S->T label-permutation null, mean / p95 at k=4

| layer | null mean | null p95 | overlap | margin vs mean | passes SO-G1(i) |
|---|---|---|---|---|---|
| L20 | 0.0076 | 0.0101 | 0.0075 | -0.0001 | False |
| L21 | 0.0058 | 0.0096 | 0.0040 | -0.0018 | False |

## Within-stage full-n reliability at k=4 (S, T)

| layer | reliability (S) | R^2 (S) | fallback (S) | reliability (T) | R^2 (T) | fallback (T) |
|---|---|---|---|---|---|---|
| L20 | 0.0154 | 0.0255 | True | 0.0181 | 0.3556 | True |
| L21 | 0.0170 | 0.4334 | True | 0.0274 | 0.6682 | True |

## Recovery curve at k=4 (floor / ceiling / closed fraction)

| layer | recovery AUROC | floor | ceiling | closed fraction |
|---|---|---|---|---|
| L20 | 0.7243 | 0.6651 | 0.8827 | 0.2720 |
| L21 | 0.7445 | 0.6377 | 0.8875 | 0.4277 |

## k=1 pipeline sanity check (recovery vs documented 0.679 cold transfer)

- k=1 recovery AUROC at L20: 0.7071
- documented cold transfer: 0.679
- within 0.10: True

## Gate-relevant summary (L19-L24 means; reported straight, no goalpost moves)

- k_gate: 4
- so_g1_i_overlap_mean: 0.005761616449810919
- so_g1_i_perm_null_mean: 0.0066938850179631875
- so_g1_i_perm_null_p95: 0.009824792904825966
- so_g1_i_margin: -0.0009322685681522683
- so_g1_i_pass: False
- so_g1_ii_reliability_s: 0.016177814851414105
- so_g1_ii_reliability_t: 0.02273905237696927
- so_g1_ii_pass: False
- so_g1_iii_closed_fraction: 0.34982740146861263
- so_g1_iii_pass: False
- so_g1_conjunction_pass: False
- reading: middle_ground
- k1_sanity_recovery_auroc_L20: 0.7070708502024292
- k1_sanity_near_documented_0679: True
- two_seed_agree: True

## Two-seed headline robustness rerun (k=8 or k_max, S->T)

| seed | layer | overlap | margin vs perm-null mean | passes SO-G1(i) this seed |
|---|---|---|---|---|
| seed_primary | L20 | 0.0075 | -0.0001 | False |
| seed_primary | L21 | 0.0040 | -0.0018 | False |
| seed_robust | L20 | 0.0085 | 0.0026 | False |
| seed_robust | L21 | 0.0072 | -0.0005 | False |

Seeds agree on SO-G1(i): True

## Smoke schema assertions

- [OK] gate_relevant_summary.so_g1_i_overlap_mean present+finite
- [OK] gate_relevant_summary.so_g1_i_perm_null_mean present+finite
- [OK] gate_relevant_summary.so_g1_i_perm_null_p95 present+finite
- [OK] gate_relevant_summary.so_g1_ii_reliability_s present+finite
- [OK] gate_relevant_summary.so_g1_ii_reliability_t present+finite
- [OK] gate_relevant_summary.so_g1_iii_closed_fraction present+finite
- [OK] gate_relevant_summary.k1_sanity_recovery_auroc_L20 present+finite
- [OK] reading in {A,B,middle_ground}
- [OK] k=1 recovery within [0.5, 0.9] loose sanity
- [OK] recovery block non-empty
- [OK] reliability block non-empty for s and grpov2
- [OK] permutation null non-empty for S->T bracket
- [OK] isotropic null non-empty for S->T bracket
- [OK] confound_bounds.matched_population_st present
- [OK] confound_bounds.matched_class_balance_timeline present
- [OK] secondary_basis pooled overlap present
- [OK] robustness_two_seed both seeds present
- [OK] deflation block non-empty
- [OK] raw_span_overlap block non-empty
