# Correctness discriminative-subspace overlap across training checkpoints

Smoke mode: False. Metric: Grassmann projection (mean squared cosine of
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
| L0 | 0.5365 | 0.5811 | 0.6507 | 0.5812 | 0.5231 |
| L1 | 0.6717 | 0.6702 | 0.6770 | 0.5914 | 0.7320 |
| L2 | 0.6998 | 0.6917 | 0.6919 | 0.6051 | 0.7406 |
| L3 | 0.7513 | 0.6712 | 0.7019 | 0.6074 | 0.7516 |
| L4 | 0.7604 | 0.6921 | 0.6982 | 0.6100 | 0.7646 |
| L5 | 0.7555 | 0.6677 | 0.7057 | 0.5967 | 0.7686 |
| L6 | 0.7600 | 0.6563 | 0.7124 | 0.6300 | 0.7676 |
| L7 | 0.7718 | 0.6747 | 0.7187 | 0.6629 | 0.7692 |
| L8 | 0.7766 | 0.6837 | 0.7135 | 0.6701 | 0.7726 |
| L9 | 0.7773 | 0.7055 | 0.7184 | 0.6529 | 0.7772 |
| L10 | 0.7674 | 0.7025 | 0.7181 | 0.6783 | 0.7943 |
| L11 | 0.7744 | 0.7192 | 0.7213 | 0.6682 | 0.7890 |
| L12 | 0.7891 | 0.7226 | 0.7239 | 0.7036 | 0.7947 |
| L13 | 0.7950 | 0.7367 | 0.7211 | 0.7021 | 0.8048 |
| L14 | 0.7937 | 0.7479 | 0.7548 | 0.7466 | 0.7955 |
| L15 | 0.8034 | 0.7609 | 0.7569 | 0.7661 | 0.8130 |
| L16 | 0.8235 | 0.7739 | 0.7756 | 0.7708 | 0.8276 |
| L17 | 0.8284 | 0.7746 | 0.7809 | 0.7823 | 0.8307 |
| L18 | 0.8412 | 0.7952 | 0.7881 | 0.7867 | 0.8445 |
| L19 | 0.8373 | 0.7983 | 0.7996 | 0.7902 | 0.8402 |
| L20 | 0.8402 | 0.8088 | 0.8144 | 0.8102 | 0.8403 |
| L21 | 0.8444 | 0.8060 | 0.8209 | 0.8152 | 0.8450 |
| L22 | 0.8561 | 0.8106 | 0.8266 | 0.8008 | 0.8498 |
| L23 | 0.8458 | 0.8075 | 0.8219 | 0.8052 | 0.8557 |
| L24 | 0.8604 | 0.8082 | 0.8226 | 0.8122 | 0.8557 |
| L25 | 0.8531 | 0.7982 | 0.8113 | 0.8072 | 0.8467 |
| L26 | 0.8506 | 0.8051 | 0.8078 | 0.8057 | 0.8496 |
| L27 | 0.8510 | 0.8082 | 0.8101 | 0.8028 | 0.8468 |
| L28 | 0.8403 | 0.8044 | 0.8074 | 0.8077 | 0.8443 |
| L29 | 0.8315 | 0.8065 | 0.8043 | 0.8115 | 0.8315 |
| L30 | 0.8240 | 0.8161 | 0.8054 | 0.8057 | 0.8257 |
| L31 | 0.8228 | 0.8180 | 0.8023 | 0.7989 | 0.8258 |
| L32 | 0.8141 | 0.8184 | 0.7929 | 0.7923 | 0.8292 |
| L33 | 0.8186 | 0.8136 | 0.7956 | 0.7966 | 0.8396 |
| L34 | 0.8132 | 0.8132 | 0.8012 | 0.7935 | 0.8345 |
| L35 | 0.8246 | 0.8126 | 0.7983 | 0.7999 | 0.8288 |
| L36 | 0.8226 | 0.7966 | 0.8016 | 0.8103 | 0.8263 |

## S->T bracket overlap by k (gate layers, k_gate=8)

| layer | k=1 | k=2 | k=4 | k=8 | k=16 | k=32 |
|---|---|---|---|---|---|---|
| L19 | 0.0151 | 0.0100 | 0.0089 | 0.0111 | 0.0197 | 0.0451 |
| L20 | 0.0100 | 0.0073 | 0.0052 | 0.0128 | 0.0220 | 0.0449 |
| L21 | 0.0047 | 0.0044 | 0.0086 | 0.0131 | 0.0199 | 0.0437 |
| L22 | 0.0040 | 0.0054 | 0.0074 | 0.0132 | 0.0209 | 0.0410 |
| L23 | 0.0092 | 0.0070 | 0.0059 | 0.0098 | 0.0218 | 0.0438 |
| L24 | 0.0108 | 0.0065 | 0.0048 | 0.0094 | 0.0201 | 0.0370 |

## S->T label-permutation null, mean / p95 at k=8

| layer | null mean | null p95 | overlap | margin vs mean | passes SO-G1(i) |
|---|---|---|---|---|---|
| L19 | 0.0115 | 0.0152 | 0.0111 | -0.0005 | False |
| L20 | 0.0109 | 0.0150 | 0.0128 | 0.0019 | False |
| L21 | 0.0112 | 0.0141 | 0.0131 | 0.0019 | False |
| L22 | 0.0105 | 0.0135 | 0.0132 | 0.0027 | False |
| L23 | 0.0112 | 0.0142 | 0.0098 | -0.0013 | False |
| L24 | 0.0098 | 0.0131 | 0.0094 | -0.0004 | False |

## Within-stage full-n reliability at k=8 (S, T)

| layer | reliability (S) | R^2 (S) | fallback (S) | reliability (T) | R^2 (T) | fallback (T) |
|---|---|---|---|---|---|---|
| L19 | 0.0188 | 0.0246 | True | 0.0261 | 0.0218 | True |
| L20 | 0.0179 | 0.0081 | True | 0.0282 | 0.1223 | True |
| L21 | 0.0177 | 0.0070 | True | 0.0298 | 0.2262 | True |
| L22 | 0.0195 | 0.0630 | True | 0.0306 | 0.1758 | True |
| L23 | 0.0192 | 0.0607 | True | 0.0313 | 0.0351 | True |
| L24 | 0.0181 | 0.1170 | True | 0.0299 | 0.1307 | True |

## Recovery curve at k=8 (floor / ceiling / closed fraction)

| layer | recovery AUROC | floor | ceiling | closed fraction |
|---|---|---|---|---|
| L19 | 0.7415 | 0.6873 | 0.8692 | 0.2976 |
| L20 | 0.7420 | 0.7014 | 0.8805 | 0.2270 |
| L21 | 0.7190 | 0.6994 | 0.8862 | 0.1053 |
| L22 | 0.7597 | 0.6980 | 0.8915 | 0.3187 |
| L23 | 0.7147 | 0.7051 | 0.8849 | 0.0536 |
| L24 | 0.7089 | 0.6998 | 0.8887 | 0.0481 |

## k=1 pipeline sanity check (recovery vs documented 0.679 cold transfer)

- k=1 recovery AUROC at L20: 0.7009
- documented cold transfer: 0.679
- within 0.10: True

## Gate-relevant summary (L19-L24 means; reported straight, no goalpost moves)

- k_gate: 8
- so_g1_i_overlap_mean: 0.011567925851313082
- so_g1_i_perm_null_mean: 0.010850084800225963
- so_g1_i_perm_null_p95: 0.014192911760108886
- so_g1_i_margin: 0.0007178410510871192
- so_g1_i_pass: False
- so_g1_ii_reliability_s: 0.01852097724167835
- so_g1_ii_reliability_t: 0.0293049843056671
- so_g1_ii_pass: False
- so_g1_iii_closed_fraction: 0.17504521343798893
- so_g1_iii_pass: False
- so_g1_conjunction_pass: False
- reading: middle_ground
- k1_sanity_recovery_auroc_L20: 0.7009412955465587
- k1_sanity_near_documented_0679: True
- two_seed_agree: True

## Two-seed headline robustness rerun (k=8 or k_max, S->T)

| seed | layer | overlap | margin vs perm-null mean | passes SO-G1(i) this seed |
|---|---|---|---|---|
| seed_primary | L19 | 0.0111 | -0.0005 | False |
| seed_primary | L20 | 0.0128 | 0.0019 | False |
| seed_primary | L21 | 0.0131 | 0.0019 | False |
| seed_primary | L22 | 0.0132 | 0.0027 | False |
| seed_primary | L23 | 0.0098 | -0.0013 | False |
| seed_primary | L24 | 0.0094 | -0.0004 | False |
| seed_robust | L19 | 0.0113 | -0.0006 | False |
| seed_robust | L20 | 0.0093 | -0.0022 | False |
| seed_robust | L21 | 0.0096 | -0.0015 | False |
| seed_robust | L22 | 0.0110 | 0.0003 | False |
| seed_robust | L23 | 0.0150 | 0.0037 | False |
| seed_robust | L24 | 0.0095 | -0.0006 | False |

Seeds agree on SO-G1(i): True
