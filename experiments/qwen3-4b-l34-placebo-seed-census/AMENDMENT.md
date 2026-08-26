# Raw-base Qwen3-4B L34 random-direction seed census

Status: SIGNED 2026-08-25 (lead + user; configs sha-pinned via bin/exp sign). Exploratory cell.

Keep this document the prose home for the experiment. The machine state lives in
`experiment.yaml` and is never duplicated here.

## Motivation and posture

`wide-instrument-control-rescore` (resolved 2026-08-20) established
direction-specificity at the raw-base Qwen3-4B late write site (hs34, layer
index 33): under the wide instrument, gated confab tightening 137/185 =
0.7405 vs undosed baseline 21/185 = 0.1135 (lift +62.7 points), while the
matched-magnitude random direction moved the same quantity to 13/185 = 0.0703
(signed lift −4.3 points), effect ratio **14.5** against the 3.0 floor
(WG-G1 PASS). Its own report flags the limitation this cell closes: "single
random_direction arm (not RR3's K>=3 fresh-seed max); ratio = gated_lift /
|random_lift|, RR3's formula specialized to K=1." One committed draw (seed
20260707) is not a null distribution; `placebo-seed-distribution-census` set
the program's standard at fifteen fresh seeds per operating point, and Paper 5
§4.8 and §7 explicitly disclose the late site's missing seed distribution as
the residual on the qwen sign-opposition claim.

This cell supplies that distribution: fifteen fresh random directions at the
same site, dose, rows, and instrument, so the late-site specificity claim
either survives a max-over-15 denominator or is weakened to its single-draw
form in the paper.

**Posture: exploratory.** Never pooled with the locked headline matrix.
Results reported straight.

## Design

**Substrate.** `unsloth/Qwen3-4B`, raw-base (no adapter; bf16, no 4-bit
quantization) — the 4.5-cell pin (`doubt-gated-caution-tighten`).

**Site, dose, and frozen instruments (pinned by sha at sign):**

- Write site hs34 (layer index 33), hidden_dim 2560; dose_target **200.0**
  (the 4.5 cell's registered late-site dose, `cell.yaml`).
- Directions and gate: `doubt-gated-caution-tighten/analysis-committed/`
  `u_d_L34.json`, `c_hat_L34.json`, `gate_fit.json`, `build_manifest.json`.
- Historical reference draw: `random_direction_L34.json` (seed 20260707) —
  reported alongside as the historical point, **not** counted among the 15
  fresh seeds.
- Rows and instrument: the SAME 185-row confab population and wide
  two-instrument stack (widened detector + blinded context-free LLM-grading
  lane) that `wide-instrument-control-rescore` scored its arms on, with
  fresh id salt and decoy-audited shards via the census
  `apply_adjudication.py` tooling. Rates are unpaired per-arm wide rates,
  identical to WG-G1's construction; no paired bootstrap is claimed.

**Reused, not re-run:** the gated arm (137/185) and undosed baseline
(21/185) are frozen from the wicr committed report
(`analysis-committed/results/wide_gates_report.json`). This cell generates
only the fifteen random arms.

**New arms.** K=15 fresh random unit directions
(`np.random.RandomState(seed).normal(size=2560)`, unit-normalized — the
recorded recipe of the committed draw), seeds **920001..920015**
(pre-registered here; disjoint from 20260707 and from
`placebo-seed-distribution-census` seed blocks). Each is the wicr
random_direction arm's pathway with the direction swapped: same gate
behavior, dose 200.0, generation contract, and scoring as the wicr arms.

**Lane.** Local RTX 3090 or Modal; fixed at launch approval.

## Prediction

All fifteen random lifts stay small and the suppressive sign is
distribution-consistent: effect ratio ≥ 3.0 against the max-over-15
denominator and at least 12 of 15 seeds negative.

## Falsifier

Any seed's |lift over the frozen 0.1135 baseline| ≥ 62.7/3 = **20.9 points**
(effect ratio < 3.0): the late-site specificity claim does not survive a
distributional denominator, and the §4.8/§7 sign-opposition text is weakened
to the single-draw form or retracted.

## Gates

- **QG-G1 (distributional specificity, primary):** effect ratio =
  0.6270 (frozen wicr gated lift) / max_k |random_lift_k| ≥ **3.0**, k =
  1..15. Equivalent form: every |random lift| < 20.9 points.
- **QG-G2 (sign-consistency, secondary; census convention):** ≥ **12/15**
  seeds with negative (suppressive) signed lift confirms the family-signed
  suppressive placebo response at this operating point. Fewer than 12/15
  means the sign is not confirmed at the late site; QG-G2 is adjudicated
  independently of QG-G1 and reported straight either way (the mid-band
  census's 12/15 boundary convention).
- No cost gate: the random arms run on confab rows only; known-correct cost
  is not a target of this cell and no cost claim is made from it.

No goalpost movement: gates, seed list, dose, rows, and the frozen
gated/baseline values are fixed at sign; an ambiguous result is reported as
ambiguous.

## Predictions scoreboard

| Predictor | Call |
|-----------|------|
| orchestrator | Both gates pass (suppressive sign holds; ratio survives max-over-15) — ~75% |
| user | "Both gates pass" (recorded 2026-08-25, selected from the pre-stated outcome menu) |

## Outcome

**Resolved 2026-08-26 — MIXED, reported straight. Specificity survives the
distributional denominator (QG-G1 PASS); the suppressive sign does not
(QG-G2 FAIL).**

Full run on the approved local RTX 3090 lane: 15 fresh random arms generated
(15 x 185 rows, dose 200.0, hs34), scored under the frozen wicr wide
two-instrument stack — pinned detector_v2 plus the blinded context-free
adjudication lane (3 shards, 2392 core rows, 179+179 decoys, fresh salt).
CG1: all three shards PASS at attempt 1 with clear-negative and
clear-positive agreement 1.0, pooled clear-positive 179/179; no voids.
Unblinding-order guarantee held (per-shard graded-file sha256 committed
before any id map read; lead verified every graded file line-positionally
before committing its hash). Evidence: `analysis-committed/`
(pool/graded/applied manifests) and `analysis/wide_gates_report.json`
arithmetic, independently re-derived by the lead from raw rows + applied
adjudications (exact match, all 15 seeds).

| Gate | Registered criterion | Result | Disposition |
|------|----------------------|--------|-------------|
| QG-G1 (distributional specificity, primary) | 0.6270 / max_k abs(lift_k) >= 3.0 | max abs lift 0.1297 (seed 920006) -> ratio **4.83** | **PASS** |
| QG-G2 (sign-consistency, secondary) | >= 12/15 seeds negative | **6/15** negative (9 positive) | **FAIL** |

Per-seed signed lifts over the frozen 0.1135 baseline: range -7.0pp
(920011) to +13.0pp (920006); median +0.5pp; 6 negative / 9 positive. The
falsifier line (any abs lift >= 20.9pp) was not approached.

Reading, per the pre-stated gate meanings: the wicr gated write's +62.7pp
lift at hs34 is direction-specific against a fifteen-draw matched-dose
distribution, not just against one historical draw — the single-draw caveat
in Paper 5 sections 4.8/7 is retired in favor of the distributional form.
But the historical seed-20260707 draw's negative lift (-4.3pp) is a
draw-level accident, not a family-signed suppressive placebo response: the
fresh-draw distribution straddles zero with a slight positive lean. The
sign-opposition phrasing is not confirmed at this operating point and must
be dropped from the manuscript claims, exactly as the gate's pre-stated
FAIL meaning requires.

Scoreboard: both predictors called "Both gates pass" (orchestrator ~75%) —
both WRONG on QG-G2. Recorded straight.

One-sentence summary (manifest `verdict:`): qwen3-4b hs34 gated-write
specificity survives a 15-seed matched-dose random census (max abs lift
13.0pp, effect ratio 4.83 >= 3.0, QG-G1 PASS) but the historical draw's
suppressive sign is not distribution-consistent (6/15 negative vs >=12
required, QG-G2 FAIL): specificity claim upgraded to distributional form,
sign-opposition claim retired.
