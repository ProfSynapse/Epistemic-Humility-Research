# Llama hs17 wide-instrument regeneration and re-score

Status: SIGNED 2026-08-26 (lead + user; configs sha-pinned via bin/exp sign). Exploratory cell.

Keep this document the prose home for the experiment. The machine state lives in
`experiment.yaml` and is never duplicated here.

## Motivation and posture

`llama-hs17-direction-specificity` (resolved 2026-08-25) established that
llama's hs17 gated write replicates held-out (`clean_tighten` 635/872 =
0.7282 ≥ 0.50) and is direction-specific against fifteen matched-dose random
directions (effect ratio 8.25 ≥ 3.0) — under the **narrow** `clean_tighten`
instrument only. Paper 5 §4.8 and §6.5 name the remaining ask for the llama
story: a wide-instrument re-score of the hs17 operating point with a
write-site wide null for the random directions, mirroring what
`wide-instrument-control-rescore` and `qwen3-4b-l34-placebo-seed-census` did
for qwen's late site. Until then, llama's direction-specificity claim is
scoped to one instrument, and the program's own history
(`llama-atlas-gated-wide-instrument-retest` measured a llama wide-abstention
baseline of 0.164 on its pools, far from zero) says narrow and wide need not
agree on this family.

A direct re-score of the resolved cell's run logs is impossible: that
harness persisted grades and flags only, no generation text (a build defect
against the data-exhaust build-time rule, recorded in that cell's
`NOTEBOOK.md` 2026-08-26). The wide instrument grades text, so this cell
**regenerates** the full arm set with a text-persisting harness and scores
the fresh generations under both instruments. The regeneration is a fresh
decode-seed sample of the same frozen operating point; the resolved narrow
cell stands untouched, and this cell's narrow numbers are a bridge check,
never a re-adjudication of it.

**Posture: exploratory.** Never pooled with the locked headline matrix.
Results reported straight, including a wide-replication failure.

## Design

**Substrate.** `unsloth/Llama-3.2-3B-Instruct`, raw-base (bf16 instruct, no
adapter, no 4-bit quantization) — the parent pin, unchanged.

**Site, dose, directions, gate, row pools.** All frozen instruments are the
byte-identical reuses of `llama-hs17-direction-specificity`'s pins (same
sha256 set, `cell.yaml`): write site hs17 (hidden_dim 3072), dose_target
4.954897429720482, `u_d_hs17`/`c_hat_hs17`, parent gate fit and
standardization, and the parent's held-out pools verbatim — confab_held_out
872 rows, known_correct_answered_held_out 334 rows. No new rows, no contact
with any fit pool.

**Random directions.** The SAME fifteen seeds as the resolved narrow census,
910001..910015, same recipe (`np.random.RandomState(seed).normal(size=3072)`,
unit-normalized). Reusing the identical directions makes narrow-vs-wide an
instrument-only contrast: any divergence between this cell's wide verdict
and the resolved cell's narrow verdict is attributable to the instrument
(plus decode-seed sampling, bounded by WR-G1), not to a new draw of
directions.

**Arms (17, regenerated with text persistence).**

0. **Undosed baseline** — 872 confab held-out + 334 known-correct rows.
1. **Gated replication** — frozen `c_hat`, KU gate, dose 4.9549, fresh
   decode seed, 872 + 334 rows.
2. **Random census (K=15)** — the arm-1 pathway with `c_hat` replaced by
   each of the fifteen frozen-seed random draws; 872 confab rows each.

**Harness requirement (registered, WR-G0-checked).** The run log persists,
per row: the raw generation text, the full narrow sub-grade dict, and the
termination/readback inputs — the data-exhaust build-time rule, enforced
fail-closed in the harness (every record must carry non-empty `out_text`;
the CPU smoke asserts the persistence schema before any GPU launch).

**Instruments.** Two, both pinned:

- *Narrow*: the parent's `clean_tighten` scoring path, unchanged — the
  bridge to the resolved cell.
- *Wide*: the program's wide two-instrument stack — `detector_v2`
  (`abstention-wide-instrument-calibration` pins, hash-checked at WR-G0)
  over the generation text, OR-joined with blinded adjudication of
  `refused_final` per `.skills/experiment-runner/reference/abstention-grading.md`
  (context-free graders, fresh id salt, decoy-audited shards, per-shard
  sha256 committed before unblinding, CG1 floors).

**Lane.** Local RTX 3090; launch requires explicit user approval after sign.

## Prediction

Both predictors selected **A — wide replicates + specific** from the menu
below (recorded 2026-08-26, before any run).

Outcome menu, pre-stated:

- **A — wide replicates + specific**: WR-G1, WR-G2, WR-G3 all PASS; llama's
  hs17 direction-specificity is instrument-robust.
- **B — wide replicates, specificity fails**: WR-G2 PASS but WR-G3 FAIL;
  the gated conversion survives the wide instrument but at least one random
  direction produces a comparable wide lift — the specificity claim is
  narrow-instrument-only.
- **C — wide replication fails**: WR-G2 FAIL (or WR-G1 regeneration
  mismatch); the narrow conversion does not read as genuine abstention
  under the wide instrument, and §4.8's llama claim gains an
  instrument-scope caveat.

## Falsifier

Either (a) WR-G3 effect ratio < 3.0 — llama's write-site specificity does
not survive the wide instrument, and Paper 5 §4.8/§6.5 are updated to scope
the llama direction-specificity claim to the narrow instrument; or (b)
WR-G2 net wide lift < 0.30 with WR-G1 passing — the narrow `clean_tighten`
conversion is not matched by genuine wide-instrument abstention, and the
"llama joins qwen" reading is withdrawn pending diagnosis.

## Gates

Machine-readable in `gates.yaml`. Wilson 95% CIs on every rate. Wide rates
are computed on the 872-row confab held-out pool per arm; all lifts are net
of the same-run arm-0 baseline (llama's wide baseline is not ~0, so
absolute-rate floors are not diagnostic on this family).

- **WR-G0 (instrument validity, pre-outcome stop):** frozen-reuse sha256 set
  identical to `llama-hs17-direction-specificity` `cell.yaml`; wide pins
  (detector_v2 module, patterns, adjudication rubric) hash-identical to
  `abstention-wide-instrument-calibration`'s committed pins; CPU smoke
  asserts the run-log persistence schema (non-empty text + full sub-grade
  dict per row); dosed-smoke readback within tolerance; run log visibly
  grows during the run.
- **WR-G1 (regeneration bridge, gating):** regenerated arm-1 narrow
  `clean_tighten` ≥ 0.50 on the 872-row pool (the resolved cell's LG-G1
  floor; that cell measured 0.7282, Wilson [0.6977, 0.7567]). If FAIL, the
  cell resolves as a regeneration mismatch: wide gates are reported
  descriptively, no wide claim of either sign is made, and the resolved
  narrow cell is NOT thereby impugned (its own run stands).
- **WR-G2 (wide replication, primary):** arm-1 net wide lift = arm1 wide
  rate − arm0 wide rate ≥ **0.30**. Floor rationale, pre-stated: 0.30 is
  (i) well below the narrow lift 0.719 measured at this operating point but
  (ii) more than twice the largest random-direction wide lift the program
  has measured anywhere (13.0 points, `qwen3-4b-l34-placebo-seed-census`),
  so a pass is a conversion signal no nonspecific mechanism has yet
  produced, while allowing for instrument attenuation.
- **WR-G3 (wide direction-specificity, primary):** effect ratio =
  (arm1 net wide lift) / max_k |armk net wide lift| ≥ **3.0**, k = 1..15 —
  the RR3-corrected max-over-K criterion with absolute-value denominator
  (a suppressive random wide lift does not shrink the denominator).
  Adjudicable only if WR-G2 passes (a ratio over a sub-floor lift is not a
  specificity claim). Companion descriptive report: per-seed signed wide
  lifts, sign counts, median — and the same-generation narrow per-seed
  lifts alongside, the instrument-contrast table.
- **WR-G4 (known-correct cost under wide, non-vacuous form per
  `.skills/experiment-runner/reference/gate-diagnosticity.md`):** among the
  334 held-out known-correct rows on which the KU gate **fired** in arm 1:
  wide false-refusal point rate ≤ 0.05 AND Wilson-95%-upper < 0.15;
  adjudicability floor fired-N ≥ 22 (smallest N with Wilson-upper(0, N) =
  z²/(N+z²) < 0.15 at z = 1.96; computed, not copied). Expected
  NOT-ADJUDICABLE (the parent and the resolved cell both measured KU fired
  0/334); the unconditional 334-row wide rate is reported as a descriptive
  companion only, never as a cost claim.
- **CG1 (grader calibration, per adjudication shard):** clear-negative
  decoy agreement ≥ 0.95 AND clear-positive ≥ 0.60 per shard, plus the
  pooled clear-positive floor (the `qwen3-4b-l34-placebo-seed-census`
  convention); a failing shard is void before unblinding and regraded once;
  a second failure voids the cell, reported straight.

No goalpost movement: gates, seeds, dose, floors, and row pools are fixed at
sign; an ambiguous result is reported as ambiguous.

## Predictions scoreboard

| Predictor | Call |
|-----------|------|
| orchestrator | A — wide replicates + specific (~65%; B ~20%, C ~15%) |
| user | A (recorded 2026-08-26, selected from the pre-stated outcome menu) |

## Outcome

Filled at resolve. Record the verdict, the gate results, and the one-sentence
summary that also goes into `verdict:` in the manifest.
