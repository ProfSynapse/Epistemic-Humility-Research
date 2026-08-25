# Llama hs17 mid-band direction-specificity census

Status: SIGNED 2026-08-25 (lead + user; configs sha-pinned via bin/exp sign). Exploratory cell.

Keep this document the prose home for the experiment. The machine state lives in
`experiment.yaml` and is never duplicated here.

## Motivation and posture

`j-space-cross-family-layer-contrast` (resolved INCONCLUSIVE 2026-07-24)
produced llama's only write ever to clear a held-out abstention floor: at the
profile-selected mid-band site hs17 (relative depth 17/28 = 0.607), the frozen
KU-gated `c_hat` write reached held-out confab `clean_tighten` 647/872 =
0.7420 (Wilson 95% [0.7119, 0.7699]) against the registered 0.50 floor. That
experiment's mid-band writes carried **no random-direction arm**, and its
known-correct cost gate was non-diagnostic (the KU gate fired on 0 of 334
held-out known-correct rows), so the pass is a behavioral result only:
nothing measures whether a matched-magnitude nonspecific perturbation at the
same site and dose reproduces it. Paper 5 discloses this gap in Sections 4.8
and 6.5 (escalation items 1 and 4).

This cell runs the missing verification step of the program's own recipe at
llama's one floor-clearing write site. Whichever way it lands, the llama
story becomes a single clean result: either llama joins qwen as a family with
a direction-specific verified write, or the hs17 pass is adjudicated
nonspecific (the mistral outcome) and the "no verified selective write
outside the Qwen lineage" reading stands.

**Posture: exploratory.** Never pooled with the locked headline matrix.
Results reported straight, including a replication failure.

## Design

**Substrate.** `unsloth/Llama-3.2-3B-Instruct`, raw-base (bf16 instruct, no
adapter, no 4-bit quantization) — the parent pin
(`experiments/j-space-cross-family-layer-contrast/families/llama-3.2-3b.yaml`).

**Site, dose, and frozen instruments (all reused verbatim from the parent's
`analysis-committed/llama-3.2-3b/`, pinned by sha at sign):**

- Write site hs17, hidden_dim 3072.
- Dose: the parent's calibrated `dose_target` **4.954897429720482**
  (readback_mean 4.968763927602852, `full_summary.json /layers/hs17`).
- Directions: `layers/hs17/u_d_hs17.json` (doubt read direction),
  `layers/hs17/c_hat_hs17.json` (caution write direction).
- Gate fit: `gate_fit_layers.json`; standardization constants from
  `build_manifest_layers.json`.
- Row sets: the parent's reused held-out pools verbatim
  (`reused_rows_manifest.json`): confab_held_out **872** rows,
  known_correct_answered_held_out **334** rows. No new rows; no contact with
  any fit pool.

**Arms.**

0. **Undosed baseline** — no intervention, identical generation contract, on
   the 872 confab held-out rows (the parent committed no undosed held-out
   `clean_tighten`, and the effect-ratio criterion needs the lift
   denominator's baseline) and on the 334 known-correct rows (baseline
   malformedness companion).
1. **Gated replication** — the parent's exact write: frozen `c_hat`, KU gate
   from the frozen gate fit, dose 4.9549, fresh decode seed. Replicates the
   0.7420 result on the same rows.
2. **Random census (K=15)** — fifteen fresh random unit directions
   (`np.random.RandomState(seed).normal(size=3072)`, unit-normalized — the
   `build_random_direction.py` recipe), seeds **910001..910015** (pre-registered
   here; disjoint from the historical draw seed 20260707 and from
   `placebo-seed-distribution-census` seed blocks). Each arm is the arm-1
   pathway with `c_hat` replaced by the random draw — KU gate, dose,
   generation contract, and scoring unchanged (the 4.5-cell
   `random_direction` control design, K=15).

**Instrument.** The parent's scoring path and `clean_tighten` metric,
unchanged — the same instrument that produced the 0.7420 pass. No
wide-instrument re-score in this cell (out of scope; a later cell may add it).

**Lane.** Local RTX 3090 or Modal; fixed at launch approval.

## Prediction

The gated write replicates above the 0.50 floor and clears the 3.0
effect-ratio against the strongest of fifteen matched-magnitude random
directions: llama's hs17 write is direction-specific.

## Falsifier

Either (a) arm 1 held-out `clean_tighten` < 0.50 (the hs17 behavioral pass
fails to replicate), or (b) max over the 15 seeds of |random lift| ≥ (gated
lift)/3, i.e. effect ratio < 3.0 — the hs17 pass is not direction-specific,
llama has no verified selective write at any site, and Paper 5 §6.5 items 1
and 4 are updated to say so.

## Gates

- **LG-G1 (replication, gating):** arm-1 held-out `clean_tighten` ≥ 0.50 on
  the 872-row pool. If FAIL, LG-G2 is still computed and reported, but the
  cell resolves as a replication failure and no specificity claim of either
  sign is made.
- **LG-G2 (direction-specificity, primary):** effect ratio =
  (arm1_rate − arm0_rate) / max_k |armk_rate − arm0_rate| ≥ **3.0**, the
  RR3-corrected criterion with a max-over-K denominator; the absolute value
  in the denominator follows the wide-instrument-control-rescore K=1
  specialization (a suppressive random lift does not shrink the denominator).
  Companion descriptive report (non-gating): per-seed signed lifts, sign
  counts, and median — the placebo-census summary shape, for cross-family
  comparability.
- **LG-G3 (known-correct cost, non-vacuous form per
  `.skills/experiment-runner/reference/gate-diagnosticity.md`):** among the
  334 held-out known-correct rows on which the KU gate **fired** in arm 1:
  false-refusal point rate ≤ 0.05 AND Wilson-95%-upper < 0.15.
  Adjudicability floor: fired-N ≥ **22** (smallest N with
  Wilson-upper(0, N) = z²/(N+z²) < 0.15 at z = 1.96; computed, not copied).
  If fired-N < 22 the gate reports **NOT-ADJUDICABLE** — a disposition
  distinct from PASS and FAIL. Expected outcome given the parent's fire rate
  (0/334) is NOT-ADJUDICABLE; the gate is registered so that a firing gate is
  measured properly, and the unconditional 334-row rate is reported as a
  descriptive companion only, never as a cost claim.

No goalpost movement: these gates, the seed list, the dose, and the row pools
are fixed at sign; an ambiguous result is reported as ambiguous.

## Predictions scoreboard

| Predictor | Call |
|-----------|------|
| orchestrator | Replicates and passes the 3.0 ratio (llama hs17 is direction-specific) — ~55% |
| user | "Replicates + specific" (recorded 2026-08-25, selected from the pre-stated outcome menu) |

## Outcome

Filled at resolve. Record the verdict, the gate results, and the one-sentence
summary that also goes into `verdict:` in the manifest.
