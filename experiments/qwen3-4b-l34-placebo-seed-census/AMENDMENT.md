# Raw-base Qwen3-4B L34 random-direction seed census

Status: draft (not signed; do not launch as confirmatory evidence).

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
| user | |

## Outcome

Filled at resolve. Record the verdict, the gate results, and the one-sentence
summary that also goes into `verdict:` in the manifest.
