# Planted-signal validation (G_val) v3 + construction-validity + prediction bands

SYNTHETIC DATA ONLY. Correlated-redundant flat-Rashomon generator (lib.synthetic_redundant_features); conditions = compact (r=1), r-ladder {r2,r4,r8} at rho=0.7, diffuse (calibrated per scale). R_SIM=30 replicates per (scale, condition), calibrated per scale to that scale's committed full-PCA dial AUROC ({'1.7b': 0.8152, '8b': 0.8621, '14b': 0.8399}). E1 averaged over R_SH=15 independent split-half draws (v3 fix i). v3 RETIRES v2's criterion (a) (decodability-insufficiency, unsatisfiable by any mean-shift construction) and designates E1 PRIMARY; E2/E3_k1/E4 are descriptive companions.

## Diffuse calibration (lead ruling 21.1)

| scale | r | rho | achieved E1 full-n (target 0.174) | achieved E3-k1 margin (target 0.04) |
|---|---|---|---|---|
| 1.7b | 8 | 0.7 | 0.1738 | 0.2976 |
| 8b | 8 | 0.95 | 0.1799 | 0.3515 |
| 14b | 16 | 0.5 | 0.1654 | 0.2582 |

## Construction-validity gate v3 (section 22.3; HARD BLOCKING STOP if fail): overall_pass = **True** (a=True, b_powered_8b_14b=True, b_1.7b_branch=full_pass, c=True); R_max=0.2357 (Delta_min=0.5, z=1.5)

### (a-new) monotone E1 full-n degradation, r-ladder {compact,r2,r4,r8}

| scale | compact | r2 | r4 | r8 | tolerance | pass |
|---|---|---|---|---|---|---|
| 1.7b | 0.5903 | 0.4507 | 0.3013 | 0.1849 | 0.0556 | True |
| 8b | 0.6860 | 0.5570 | 0.3939 | 0.2578 | 0.0479 | True |
| 14b | 0.6784 | 0.5530 | 0.3925 | 0.2320 | 0.0410 | True |

### (b-new) derived index-resolution ceiling: sigma_c(s) <= R_max (R_max = Delta_min/(z*sqrt(2)) = 0.2357); HARD at ('8b', '14b'), 1.7B recorded as a branch (pre-stated 1.7B disposition)

| scale | compact mean | diffuse mean | gap | diffuse half-width | sigma_c | pass |
|---|---|---|---|---|---|---|
| 1.7b | 0.5903 | 0.1845 | 0.4058 | 0.0739 | 0.1108 | True |
| 8b | 0.6860 | 0.1769 | 0.5092 | 0.1110 | 0.1326 | True |
| 14b | 0.6784 | 0.2013 | 0.4771 | 0.0846 | 0.1078 | True |

### (c) compact-vs-diffuse separation on the primary estimator (E1 full-n); E2/E3-k1 reported alongside for transparency

- **1.7b** (pass=True, primary_estimator=e1_full_n): e1_full_n: diff=0.4058 vs half-width=0.0532 sep=True, e2_ratio: diff=0.1186 vs half-width=0.0892 sep=True, e3_k1_margin: diff=0.0061 vs half-width=0.0328 sep=False
- **8b** (pass=True, primary_estimator=e1_full_n): e1_full_n: diff=0.5092 vs half-width=0.0706 sep=True, e2_ratio: diff=0.0289 vs half-width=0.0693 sep=False, e3_k1_margin: diff=0.0076 vs half-width=0.0370 sep=False
- **14b** (pass=True, primary_estimator=e1_full_n): e1_full_n: diff=0.4771 vs half-width=0.0517 sep=True, e2_ratio: diff=0.2691 vs half-width=0.0958 sep=True, e3_k1_margin: diff=0.0026 vs half-width=0.0330 sep=False

## G_val v2-band-based pass/fail (ACTIONABLE per estimator: E1 uses the powered-pair carve-out per the pre-stated 1.7B disposition; E2/E3_k1/E4 keep the unchanged all-three-scales rule and remain descriptive companions)

| estimator | pass |
|---|---|
| E1 | True |
| E2 | False |
| E3_k1 | False |
| E4 | True |

### E1 per-scale detail

- **1.7b**: compact=0.5903 diffuse=0.1845 diff=0.4058 pooled_hw=0.0532 sep=True mono=True reach=True pass=True r_ladder={ compact:0.5903, r2:0.4507, r4:0.3013, r8:0.1849 }
- **8b**: compact=0.6860 diffuse=0.1769 diff=0.5092 pooled_hw=0.0706 sep=True mono=True reach=True pass=True r_ladder={ compact:0.6860, r2:0.5570, r4:0.3939, r8:0.2578 }
- **14b**: compact=0.6784 diffuse=0.2013 diff=0.4771 pooled_hw=0.0517 sep=True mono=True reach=True pass=True r_ladder={ compact:0.6784, r2:0.5530, r4:0.3925, r8:0.2320 }

### E2 per-scale detail

- **1.7b**: compact=1.2469 diffuse=1.1282 diff=0.1186 pooled_hw=0.0892 sep=True mono=True reach=True pass=True r_ladder={ compact:1.2469, r2:1.1813, r4:1.1487, r8:1.1113 }
- **8b**: compact=1.2167 diffuse=1.1877 diff=0.0289 pooled_hw=0.0693 sep=False mono=True reach=True pass=False r_ladder={ compact:1.2167, r2:1.1472, r4:1.1174, r8:1.0892 }
- **14b**: compact=1.2383 diffuse=0.9692 diff=0.2691 pooled_hw=0.0958 sep=True mono=True reach=True pass=True r_ladder={ compact:1.2383, r2:1.1788, r4:1.1441, r8:1.1070 }

### E3_k1 per-scale detail

- **1.7b**: compact=0.2840 diffuse=0.2778 diff=0.0061 pooled_hw=0.0328 sep=False mono=True reach=True pass=False r_ladder={ compact:0.2840, r2:0.2869, r4:0.2860, r8:0.2833 }
- **8b**: compact=0.3280 diffuse=0.3204 diff=0.0076 pooled_hw=0.0370 sep=False mono=True reach=True pass=False r_ladder={ compact:0.3280, r2:0.3275, r4:0.3245, r8:0.3295 }
- **14b**: compact=0.3034 diffuse=0.3008 diff=0.0026 pooled_hw=0.0330 sep=False mono=True reach=True pass=False r_ladder={ compact:0.3034, r2:0.2936, r4:0.2990, r8:0.2983 }

### E4 per-scale detail

- **1.7b**: compact=11.9166 diffuse=14.5889 diff=2.6723 pooled_hw=2.6449 sep=True mono=True reach=True pass=True r_ladder={ compact:11.9166, r2:10.6659, r4:11.1604, r8:14.5719 }
- **8b**: compact=10.2094 diffuse=13.0523 diff=2.8430 pooled_hw=1.9125 sep=True mono=True reach=True pass=True r_ladder={ compact:10.2094, r2:9.6129, r4:10.5068, r8:13.9052 }
- **14b**: compact=10.7198 diffuse=22.0690 diff=11.3492 pooled_hw=2.2141 sep=True mono=True reach=True pass=True r_ladder={ compact:10.7198, r2:10.2397, r4:10.9899, r8:13.9936 }

## Primary designation (section 21.5): {'primary': 'E1', 'fallback_order': ('E3_k1', 'E1', 'E2'), 'm4_prime': False}

## Aggregate estimator values by scale x condition (mean [p5,p95], n reps)

### 1.7b

| condition | E1 full-n | E1 matched-n | E2 ratio | E3 k=1 margin | E4 PR |
|---|---|---|---|---|---|
| compact | 0.5903 [0.5613,0.6263] | 0.3710 [0.3160,0.4302] | 1.2469 [1.1553,1.3302] | 0.2840 [0.2595,0.3130] | 11.9166 [8.9925,16.0926] |
| r2 | 0.4507 [0.3997,0.5067] | 0.2559 [0.1933,0.3163] | 1.1813 [1.1062,1.2658] | 0.2869 [0.2600,0.3089] | 10.6659 [8.3420,13.4359] |
| r4 | 0.3013 [0.2501,0.3728] | 0.1541 [0.0842,0.2337] | 1.1487 [1.0134,1.3062] | 0.2860 [0.2511,0.3166] | 11.1604 [9.2953,12.9206] |
| r8 | 0.1849 [0.1234,0.2736] | 0.1117 [0.0577,0.1680] | 1.1113 [0.9960,1.2150] | 0.2833 [0.2346,0.3270] | 14.5719 [13.1543,16.0294] |
| diffuse | 0.1845 [0.1026,0.2505] | 0.0870 [0.0467,0.1432] | 1.1282 [1.0356,1.2177] | 0.2778 [0.2373,0.3148] | 14.5889 [12.8345,16.3139] |

### 8b

| condition | E1 full-n | E1 matched-n | E2 ratio | E3 k=1 margin | E4 PR |
|---|---|---|---|---|---|
| compact | 0.6860 [0.6508,0.7113] | 0.3955 [0.3279,0.4427] | 1.2167 [1.1472,1.2898] | 0.3280 [0.3000,0.3575] | 10.2094 [7.7512,12.6497] |
| r2 | 0.5570 [0.5256,0.5919] | 0.2736 [0.2058,0.3325] | 1.1472 [1.0708,1.2582] | 0.3275 [0.2906,0.3554] | 9.6129 [7.2305,12.5558] |
| r4 | 0.3939 [0.3459,0.4347] | 0.1636 [0.0853,0.2220] | 1.1174 [1.0432,1.1935] | 0.3245 [0.2878,0.3630] | 10.5068 [8.3627,12.1841] |
| r8 | 0.2578 [0.1621,0.3298] | 0.1203 [0.0645,0.1875] | 1.0892 [1.0095,1.1671] | 0.3295 [0.3001,0.3684] | 13.9052 [12.5370,15.4551] |
| diffuse | 0.1769 [0.0743,0.2963] | 0.1506 [0.1019,0.2259] | 1.1877 [1.1262,1.2609] | 0.3204 [0.2673,0.3576] | 13.0523 [11.8342,14.5857] |

### 14b

| condition | E1 full-n | E1 matched-n | E2 ratio | E3 k=1 margin | E4 PR |
|---|---|---|---|---|---|
| compact | 0.6784 [0.6580,0.6957] | 0.3782 [0.3142,0.4255] | 1.2383 [1.1754,1.3525] | 0.3034 [0.2774,0.3274] | 10.7198 [7.7405,13.1567] |
| r2 | 0.5530 [0.5264,0.5894] | 0.2588 [0.2086,0.3175] | 1.1788 [1.0919,1.2609] | 0.2936 [0.2629,0.3205] | 10.2397 [8.2006,12.7741] |
| r4 | 0.3925 [0.3357,0.4348] | 0.1631 [0.0822,0.2150] | 1.1441 [1.0621,1.2376] | 0.2990 [0.2715,0.3267] | 10.9899 [9.7411,12.5811] |
| r8 | 0.2320 [0.1717,0.2999] | 0.0928 [0.0525,0.1362] | 1.1070 [1.0435,1.2013] | 0.2983 [0.2721,0.3323] | 13.9936 [12.7429,15.3728] |
| diffuse | 0.2013 [0.1092,0.2785] | 0.0937 [0.0500,0.1497] | 0.9692 [0.8778,1.0839] | 0.3008 [0.2579,0.3401] | 22.0690 [20.2631,23.7032] |

## Two-anchor prediction bands (compact + diffuse, per scale per estimator)

### 1.7b

- **e1_full_n**: compact mean=0.5903 hw=0.0325; diffuse mean=0.1845 hw=0.0739
- **e1_matched_n**: compact mean=0.3710 hw=0.0571; diffuse mean=0.0870 hw=0.0483
- **e2_ratio**: compact mean=1.2469 hw=0.0874; diffuse mean=1.1282 hw=0.0911
- **e3_k1_margin**: compact mean=0.2840 hw=0.0267; diffuse mean=0.2778 hw=0.0388
- **e4_pr**: compact mean=11.9166 hw=3.5501; diffuse mean=14.5889 hw=1.7397

### 8b

- **e1_full_n**: compact mean=0.6860 hw=0.0302; diffuse mean=0.1769 hw=0.1110
- **e1_matched_n**: compact mean=0.3955 hw=0.0574; diffuse mean=0.1506 hw=0.0620
- **e2_ratio**: compact mean=1.2167 hw=0.0713; diffuse mean=1.1877 hw=0.0673
- **e3_k1_margin**: compact mean=0.3280 hw=0.0287; diffuse mean=0.3204 hw=0.0452
- **e4_pr**: compact mean=10.2094 hw=2.4493; diffuse mean=13.0523 hw=1.3758

### 14b

- **e1_full_n**: compact mean=0.6784 hw=0.0188; diffuse mean=0.2013 hw=0.0846
- **e1_matched_n**: compact mean=0.3782 hw=0.0557; diffuse mean=0.0937 hw=0.0499
- **e2_ratio**: compact mean=1.2383 hw=0.0885; diffuse mean=0.9692 hw=0.1031
- **e3_k1_margin**: compact mean=0.3034 hw=0.0250; diffuse mean=0.3008 hw=0.0411
- **e4_pr**: compact mean=10.7198 hw=2.7081; diffuse mean=22.0690 hw=1.7201

Crystallization index c = (observed - diffuse_mean) / (compact_mean - diffuse_mean), NOT clipped to [0,1] (v3 section 22.6.1 -- out-of-range values are informative), and the pre-registered trend test (monotonicity + endpoint contrast Delta_c vs propagated sigma_c, section 22.6.3) are both implemented (`crystallization_index`, `trend_test`) but NOT evaluated here -- this module never reads a real observed value. Per-scale sigma_c (the trend test's propagated-error input) is already computed above under the (b-new) construction-validity detail.
