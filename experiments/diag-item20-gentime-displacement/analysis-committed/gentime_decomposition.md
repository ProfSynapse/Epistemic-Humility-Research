# Item 20 - generation-time doubt/caution-plane decomposition (L35)

Checkpoint: clean-SFT -> GRPO-v2 (seed1). Axes from `experiment/phase1/probe/analysis/current_clean_grpo_v2_caution_residual_direction`.
Axis geometry: cos(doubt, caution) = -0.8296, cos(doubt, caution_perp) = 0.0000 (orthogonal by construction), cos(caution_perp, caution) = 0.5583.

Rows: 41 answered (with states) of 600 pool; 559 refused (no states). r2 pool is 100% unknown-label; all answered rows are confabulations and refused rows have no captured states -> single-group analysis (unknown-label confabulations); answered-vs-refused split not possible.

## 1. Absolute projection per position (mean [95% CI])

| position | proj doubt | proj caution | proj caution_perp | disp norm from anchor |
|---|---|---|---|---|
| anchor | -249.94 [-253.18, -246.34] | 295.20 [291.24, 298.68] | 157.34 [155.42, 159.04] | 0.00 [0.00, 0.00] |
| first_vis | -301.55 [-302.08, -300.98] | 349.46 [348.85, 350.00] | 177.83 [177.50, 178.16] | 373.51 [370.17, 377.05] |
| mid25 | -266.96 [-276.80, -255.77] | 288.69 [277.53, 298.39] | 120.39 [115.74, 124.68] | 487.56 [472.97, 504.01] |
| mid50 | -201.89 [-207.74, -196.36] | 230.32 [224.45, 236.10] | 112.52 [109.74, 114.86] | 412.30 [405.80, 420.54] |
| mid75 | -315.25 [-324.23, -302.40] | 363.15 [348.58, 373.26] | 181.99 [174.76, 187.05] | 555.78 [546.32, 565.38] |
| answer_end | -189.39 [-191.83, -187.21] | 221.74 [219.37, 224.34] | 115.73 [114.73, 116.80] | 475.25 [471.33, 478.95] |

Residual fraction of the displacement (fraction of the position-minus-anchor movement OUTSIDE the doubt/caution_perp plane):

| position | in-plane frac | residual frac |
|---|---|---|
| first_vis | 0.148 [0.141, 0.157] | 0.989 [0.987, 0.990] |
| mid25 | 0.102 [0.093, 0.111] | 0.994 [0.993, 0.995] |
| mid50 | 0.163 [0.152, 0.172] | 0.986 [0.985, 0.988] |
| mid75 | 0.145 [0.139, 0.151] | 0.989 [0.988, 0.990] |
| answer_end | 0.155 [0.145, 0.163] | 0.988 [0.986, 0.989] |

## 2. Delta profile: displacement from anchor along each axis (mean [95% CI])

| position | delta doubt | delta caution | delta caution_perp |
|---|---|---|---|
| first_vis | -51.61 [-54.96, -48.59] | 54.25 [51.04, 57.82] | 20.49 [18.88, 22.25] |
| mid25 | -17.02 [-25.93, -6.91] | -6.51 [-17.14, 2.55] | -36.95 [-41.62, -32.83] |
| mid50 | 48.05 [41.92, 53.47] | -64.89 [-70.79, -58.39] | -44.82 [-47.40, -42.23] |
| mid75 | -65.31 [-74.69, -52.34] | 67.95 [53.67, 78.46] | 24.65 [17.48, 29.93] |
| answer_end | 60.55 [56.10, 64.77] | -73.46 [-77.81, -68.73] | -41.61 [-43.63, -39.37] |

Per-row variance fraction of the displacement carried by each axis (mean [95% CI]):

| position | var-frac doubt | var-frac caution | var-frac caution_perp |
|---|---|---|---|
| first_vis | 0.0195 [0.0174, 0.0218] | 0.0216 [0.0193, 0.0243] | 0.0032 [0.0027, 0.0037] |
| mid25 | 0.0050 [0.0038, 0.0063] | 0.0031 [0.0011, 0.0056] | 0.0062 [0.0052, 0.0073] |
| mid50 | 0.0154 [0.0134, 0.0175] | 0.0268 [0.0235, 0.0298] | 0.0121 [0.0111, 0.0131] |
| mid75 | 0.0181 [0.0168, 0.0195] | 0.0204 [0.0187, 0.0221] | 0.0032 [0.0027, 0.0038] |
| answer_end | 0.0169 [0.0149, 0.0189] | 0.0246 [0.0220, 0.0272] | 0.0078 [0.0071, 0.0085] |

## 3. Cosine of the MEAN displacement vector with each axis

| position | cos doubt | cos caution | cos caution_perp | mean disp norm |
|---|---|---|---|---|
| first_vis | -0.1408 | 0.1481 | 0.0559 | 366.45 |
| mid25 | -0.0433 | -0.0166 | -0.0939 | 393.38 |
| mid50 | 0.1263 | -0.1705 | -0.1178 | 380.49 |
| mid75 | -0.1240 | 0.1290 | 0.0468 | 526.73 |
| answer_end | 0.1297 | -0.1573 | -0.0891 | 466.91 |

