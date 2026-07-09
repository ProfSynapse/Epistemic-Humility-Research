# Amendment AK Stage 1 - gate verdicts (committed record)

Analysis: `archive/experiment/phase1/probe/amendments/amendment_ak_stage1_analyze.py`
(seed 20260705, deterministic). Full machine-readable output and per-position
CIs are in
`experiments/commitment-point/artifacts/stage1/ak_stage1_gate_report.json`.
Pilot floor: `experiments/commitment-point/artifacts/stage1/ak_stage1_pilot_floor.json`
(COMMITTED_FLOOR = 5.291963, locked BEFORE this analysis, commit b6f560b8).

Data: raw-base config_sha `0dcb65d0062db64a`, grpo-v2 config_sha
`6394415378c83c96`; 1,338 rows/arm (309 confab / 1,029 refuse); 50 pilot rows
excluded from the AK-G2 test set (non-pilot: 1,288 = 295 confab / 993 refuse
after the min-3-position slope filter).

## AK-G1 crystallization -- gated on grpo-v2 -- MISS

Pre-registered (doc §4): veto AUROC at answer-end minus veto AUROC at
first-visible >= +0.10. Veto axis refit per position out-of-fold (PCA-128 +
saga), label = confab; AJ equal-rank random-direction guard read ~0.49-0.53.

| arm | first-visible veto AUROC | answer-end veto AUROC | delta (end - first) |
|---|---|---|---|
| grpo-v2 (GATED) | 0.9424 [0.9299, 0.9534] | 0.9248 [0.9084, 0.9390] | **-0.0175** |
| raw-base (descriptive) | 0.9624 [0.9524, 0.9715] | 0.9966 [0.9938, 0.9987] | +0.0341 |

Verdict: **MISS** (need >= +0.10; observed -0.0175, i.e. the veto does not
rise across the answer window on grpo-v2). The veto is already near-saturated
at the first visible token (0.94) and drifts slightly DOWN by answer-end.
Descriptively raw-base rises (+0.034) toward a ~0.997 ceiling but still far
below the +0.10 bar. Interpretation is left to the orchestrator; the number is
that on the gated arm the veto does not crystallize across the answer window at
this granularity -- it is essentially already assembled at the first visible
token.

## AK-G2 doubt-trajectory discriminability -- gated -- MISS (floor not cleared)

Pre-registered (doc §4): PASS requires (a) |slope contrast| >= COMMITTED_FLOOR
(5.291963) AND (b) permutation p < 0.01. Statistic = confab-vs-refuse contrast
of the per-row least-squares slope of the frozen doubt-trunk (AH answerability
probe L24) projection vs normalized answer-window position [0,1].

| arm | slope contrast | CI95 | perm p | clears floor? | p < 0.01? |
|---|---|---|---|---|---|
| grpo-v2 (GATED) | -4.6234 | [-5.382, -3.884] | 1.0e-04 | **No** (< 5.292) | Yes |
| raw-base (descriptive) | -9.3199 | [-10.320, -8.315] | 1.0e-04 | Yes | Yes |

Verdict: **MISS** on the gated arm: (b) holds (p < 0.01) but (a) fails
(|contrast| 4.62 < floor 5.29), and the doc requires BOTH. Because it is a
MISS, no doubt-trajectory path is claimed on the gated arm and the scoreboard
fork is not adjudicated here.

Descriptive path context (NOT a claim; reported per doc §4 that "which path
wins is the finding"):
- grpo-v2: confab rows mean slope **+11.78** (doubt RISES during confab
  generation), refuse rows **+16.41** (doubt rises MORE). Both strata rise; the
  confab-minus-refuse contrast is negative because refuse rises faster. On the
  gated arm the raw direction is consistent with the user's H-rise on confab
  rows, but the discriminability floor is not cleared.
- raw-base: confab rows mean slope **-3.50** (doubt DROPS), refuse rows **+5.82**
  -> an H-drop-on-confab pattern with a contrast that clears the floor. This is
  the descriptive arm only and is NOT the gate surface.

The gated and descriptive arms point in DIFFERENT directions on the confab
stratum (grpo-v2 rise vs raw-base drop). This divergence is a finding for the
orchestrator/scoreboard, not something this analysis adjudicates.

## Falsifier status

The full AK falsifier (doc §4) is "flat crystallization curve (G1 miss) AND no
steering asymmetry (G3 miss)". G3 is Stage 2 (not run). Stage 1 delivers a G1
MISS (one of the two falsifier legs) and a G2 MISS-on-floor. Whether the
falsifier fires depends on the Stage 2 G3 result and is the orchestrator's
adjudication.
