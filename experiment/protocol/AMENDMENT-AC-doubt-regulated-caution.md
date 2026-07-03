# Amendment AC — Doubt-Regulated Caution (closed-loop coupling at inference)

Status: SIGNED 2026-07-02 (user in-conversation: plan approved "i like it proceed
get it running locally after olmo"; conservative framing explicitly requested:
"can we be somewhat conservative on this one... i want to be cautiously
optimistic here"). Tier-2 exploratory local mechanism evidence under
`PHASE3-control-system-protocol.md` (this is the first cell to address its RQ4:
does the signal support a viable control loop, or only an offline diagnostic?).
Not headline evidence; never pooled with the locked Phase 1 matrix.

Run lane: LOCAL 3090 only. Queued behind the OLMo Y-cell extraction and the
Amendment AB V1 local cells. No cloud spend.

## 1. Motivation and posture (read this before the gates)

Two facts are established on the deployed checkpoint (clean-SFT -> GRPO-v2
seed1), both from session 0026:

- The internal doubt axis at L35 is excellent as a READOUT: known/unknown
  AUROC 0.972, while the emitted confidence scalar sits at ~0.52 (cp008,
  `calibration_gap_clean_sft_grpo_v2_seed1.json`).
- The caution gate is causally real and separable from doubt: caution_perp
  (the doubt-orthogonalized caution direction, perp fraction 0.558) is
  independently load-bearing — ablating it drops known_refused refusal
  0.994 -> 0.524 with specificity intact, and shift_plus2 induces new refusals
  on well-known items (refined B1, cp010).

The pathology is that the gate fires largely independent of doubt (65%+
over-refusal on known items). This amendment asks the narrowest causal version
of the obvious next question: **if we make the gate value a live function of
the doubt readout, does the coupling itself carry measurable information —
beyond what simply deleting the gate already achieves?**

POSTURE — this is a conservative cell and the expected result is modest:

- On this checkpoint family, every prior attempt to make the internal signal
  DRIVE behavior has failed or fizzled (Amendment M collapsed onto the action,
  N showed the emitted/action decoupling is structural, R falsified the
  co-train channel, AA Arm A was flat 8/8). The readout side keeps winning;
  the use-the-signal side is 0-for-4. We pre-state that prior here.
- The likely spoiler is named up front: raw caution is ~83% doubt-aligned, so
  the model's own gate is already PARTIALLY doubt-conditional, and constant
  ablation already de-refuses in a doubt-correlated way. The realistic
  expectation is a SMALL selectivity margin for explicit coupling, possibly
  zero.
- A null is a reportable result: it closes RQ4 Stage 1 negatively ("the loop
  adds nothing at inference either; the deficit is deeper than a missing
  wire") and slots coherently next to M/N/R/AA. The cell's value is that it
  decides RQ4 Stage 1 cheaply in either direction.

## 2. Mechanism (the math, pre-registered)

All quantities live in the L35 residual stream of clean-SFT->GRPO-v2 seed1.

Sensor (read, offline, CPU): doubt axis `u_d = unit(mean(h[known_correct_answered])
- mean(h[unknown_refused]))` from the frozen extraction
(`extraction__55254a04aa1f`) + behavior overlay. Each eval row's knownness
`d_i = h_i . u_d`, standardized over the eval-row population:
`z_i = (d_i - mu_d) / sigma_d`.

Actuator (write, during generation): `c_hat = unit(caution_perp)` from the
committed refined-B1 direction JSON (`caution_perp_direction_L35.json`,
layer 35, sigma = row-population std of projections). New arm mode `couple`:

```
h' = h - (h . c_hat) c_hat + g_i * sigma_c * c_hat
```

i.e. erase the model's own gate value and write a doubt-proportional setpoint,
at every position, exactly like the existing ablate/shift hooks. The gain is a
proportional controller:

```
g_i = -alpha * z_i, clipped to [-2, +2], with alpha = 1 (pre-registered)
```

Minus sign: feels known (z>0) -> gate written low -> answer; feels unknown
(z<0) -> gate written high -> refuse.

Design properties (why this is well-posed):

- `c_hat ⟂ u_d` by construction (that is what caution_perp is), so the write
  does not disturb the variable being read, and the read is computed offline
  from frozen activations BEFORE any intervention — no within-item feedback.
- `couple` with `g ≡ 0` IS the existing constant-ablate arm, so the constant
  comparison is nested inside the coupling family, not a separate apparatus.
- The permuted placebo is the same equation with `z_i` shuffled across eval
  rows (fixed seed): identical gain distribution, information removed. Any
  coupled-vs-permuted difference is attributable purely to the doubt signal.

## 3. Cells, rows, arms

Checkpoint/prompt/decoding: identical to refined B1 (merged clean-SFT base +
GRPO-v2 adapter, same system prompt, greedy, max_new_tokens 96).

Rows: the frozen behavior overlay
(`analysis/current_selfaware_behavior_rows/clean_sft_grpo_v2/rows.jsonl`),
cells `known_refused`, `known_correct_answered`, AND `unknown_refused` (the
selectivity target B1 did not need but AC's claim requires).

Arms (one pre-registered configuration; no alpha sweep, no coupling-form
fishing):

| arm | mode | gain |
|-----|------|------|
| baseline | baseline | — |
| coupled | couple | `g_i = -z_i` (real, clipped ±2) |
| permuted | couple | same gains, row-shuffled (seed 20260702) |
| ablate | ablate | `g ≡ 0` (constant comparison, re-run in-frame) |

Smoke gate before the full run: 25 rows/cell (75 rows x 4 arms = 300 units),
pass = coupled shows ANY directional known-vs-unknown separation vs permuted
(point estimate, no CI at smoke n). Full run only after smoke passes; if the
smoke shows nothing, report the smoke and stop (the falsifier can fire early
and cheaply).

## 4. Gates and falsifier (pre-stated; conservative)

Selectivity gap per arm := (known_refused de-refusal rate) - (unknown_refused
de-refusal rate), where de-refusal = 1 - refusal_rate relative to that cell's
baseline-arm refusal.

- **AC-G1 (primary, modest)**: coupled beats permuted on the selectivity gap
  by >= 5pt, bootstrap 95% CI (row-level, 10k resamples) excluding 0. This is
  the whole claim: the wire carries information.
- **AC-G2 (secondary, estimate only — no pass/fail)**: coupled vs constant
  ablate on the selectivity gap and on per-de-refused correctness, reported
  with CIs. We pre-state that ~0 is the EXPECTED outcome here given the 83%
  doubt-alignment of the model's own gate; any positive margin is upside, and
  we commit to not spinning a null on G2 as a failure of G1.
- **Specificity guard (applies to the coupled arm, pass/fail)**:
  known_correct_answered refusal rise <= 5pt and correctness drop <= 3pt vs
  baseline (the B1 convention).

FALSIFIER: permuted ≈ coupled on AC-G1 (margin < 5pt or CI includes 0). Then
the doubt readout contributes nothing at the intervention site; the selectivity
seen is a magnitude artifact. Consequence, pre-committed: report as a negative,
no alpha-tuning rescue runs, no alternative-coupling-form runs under this
amendment; RQ4 Stage 1 closes negative and any Stage 2 (per-token online
controller) proposal must be a new signed amendment that engages with this
null.

Prediction (cautiously optimistic, ordered): most likely outcome is AC-G1
passes with a small margin (5-15pt) while AC-G2 shows ~0 vs constant ablate;
second most likely is the falsifier fires. A large AC-G1 margin (>25pt) would
be a surprise and should be checked for leaks (gain-map row alignment,
permutation correctness) before being believed.

## 5. Metrics (all reported, none gated beyond §4)

Per arm x cell: n, refusal_rate, correct_rate (the existing analyze table,
extended with unknown_refused). Derived: selectivity gap + CI per
interventional arm; per-de-refused correctness; dose-response DESCRIPTIVE
curve of refusal vs written gain (binned g_i), coupled arm only.

## 6. Implementation surface (all CPU-testable except the run itself)

1. `experiment/phase1/probe/build_doubt_gain_map.py` (NEW, CPU): loads the
   frozen extraction + overlay, fits `u_d`, computes z_i and gains for the
   three eval cells, emits `doubt_gain_map_L35.json` carrying alpha, clip,
   mu_d/sigma_d, the real gains, the permuted gains, and the permutation seed.
   Explicit `--extraction-dir/--overlay/--direction/--out` args (the frozen
   data lives untracked in the main working tree).
2. `phase3_residual_intervention.py`: add mode `couple` to the pure-numpy
   reference + hook (erase + write, as §2); `parse_arms` accepts
   `gain_map`/`gain_key` on couple arms; `analyze_arms` gains an optional
   groups argument (default unchanged — B1 behavior and tests untouched).
3. `phase3_residual_intervention_runner.py`: for couple arms, load the gain
   map once and resolve the per-row alpha in the (arm, row) loop; rows missing
   from the map are a hard error (no silent 0-gain).
4. `config/phase3_ac_doubt_coupled_intervention.yaml` + a `_smoke` variant
   (25 rows/cell via `rows_filter.max_rows_per_cell`, a small runner
   extension; deterministic first-N in file order).
5. Tests: couple-mode math (g=0 == ablate; coordinate write value), gain-map
   builder on synthetic activations (sign convention: known-side rows get
   negative gain), runner gain resolution (missing row raises), permutation
   is seed-stable and value-preserving.

## 7. Provenance

- Doubt axis construction mirrors `build_caution_perp_direction.py` (same
  extraction `extraction__55254a04aa1f`, same overlay, same ka/ur anchors).
- Caution direction: `analysis/current_clean_grpo_v2_caution_residual_direction/caution_perp_direction_L35.json`
  (refined B1 artifact, perp_fraction 0.558).
- Comparison constants: refined B1 ablate known_refused 0.994 -> 0.524,
  de-refused correctness 68.7% (cp010); raw-theta B1 58.9% (cp #110).
- Analysis outputs stay untracked per the phase3 convention; the summary
  numbers and verdict land in this doc's §8 and the session note.
- Gain map BUILT 2026-07-02 (local-only per convention, deterministic from the
  frozen inputs above):
  `python3 build_doubt_gain_map.py --extraction-dir <extraction__55254a04aa1f> --overlay <clean_sft_grpo_v2/rows.jsonl> --out analysis/ac_doubt_gain_map/doubt_gain_map_L35.json`
  -> 1217 rows (kr 168, ka 373, ur 676); mu_d -245.28, sigma_d 60.52;
  per-cell mean z: kr +0.35, ka +1.18, ur -0.73 (signs as predicted in §2:
  known-side positive, unknown negative); gains in [-2.00, +1.86], 23 rows at
  the -2 clip (all high-confidence known rows). Offline preflight: all 1217
  config rows resolve in both `gains` and `gains_permuted`; smoke slice is
  25/25/25. Note the modest kr mean z (+0.35): the coupled push toward
  answering on known_refused is weak on average, consistent with the
  conservative small-margin prediction (§4).

## 8. Result

**AC-G1 PASS — the wire carries information.** Run 2026-07-03, local 3090,
sequential registered instrument (engine PR #154's batched path was qualified
by the equivalence spot check but not used for the evidence run). Smoke
(25/cell) passed the §3 gate first: coupled gap +0.04 vs permuted −0.08,
monotonic dose curve. Full run: 1217 rows (kr 168 / ka 373 / ur 676) × 4 arms
= 4868 units, greedy, max_new_tokens 96. Analysis:
`analyze_ac_doubt_coupled.py`, paired row-level bootstrap, 10k resamples,
seed 20260703.

| arm | kr refusal (n=168) | kr correct | ka refusal (n=373) | ka correct | ur refusal (n=676) | selectivity gap |
|-----|-----|-----|-----|-----|-----|-----|
| baseline | 0.994 | 0.000 | 0.003 | 0.997 | 1.000 | — |
| coupled | 0.506 | 0.333 | 0.000 | 0.973 | **0.580** | **+0.068** |
| permuted | 0.518 | 0.339 | 0.000 | 0.976 | 0.504 | −0.019 |
| ablate | 0.536 | 0.327 | 0.000 | 0.973 | 0.503 | −0.039 |

- **AC-G1 (gated): PASS.** Coupled − permuted selectivity-gap margin
  **+8.7pt, 95% CI [+5.6, +12.0]** — ≥5pt and CI excludes 0. Landed inside
  the pre-stated "most likely" band (5–15pt); well under the >25pt
  check-for-leaks trigger.
- **AC-G2 (estimate only, no gate): +10.7pt vs constant ablate, CI [+7.1,
  +14.5].** The pre-stated expectation was ~0; the positive margin is upside.
  Mechanistically the coupling's edge is on the unknown side: it PRESERVES
  unknown_refused refusal (0.580) where ablate and permuted release it
  indiscriminately (0.503/0.504), while matching their known_refused release.
  De-refused correctness is flat across arms (coupled 0.675 [0.578, 0.771];
  permuted 0.704; ablate 0.705 ≈ refined B1's 0.687) — the doubt signal
  decides WHICH rows get released, not how well released rows answer.
- **Specificity guard: PASS.** ka refusal rise −0.3pt (≤5pt); ka correctness
  drop 2.4pt (≤3pt, close but under).
- **Dose-response (descriptive, coupled arm):** monotone from refusal 0.000
  at g∈[−2,−1.5] (n=98) through 0.465 at [−0.5,0) to 0.645 at [0,0.5), with
  wobble above (0.585 / 0.483 at mid-positive bins, 0.800 in the small n=25
  top bin). The written gain demonstrably drives refusal.
- **Falsifier: NOT fired.** In-frame B1 replication held (ablate kr 0.994 →
  0.536 vs refined B1's 0.994 → 0.524).

**Verdict: RQ4 Stage 1 closes POSITIVE, at the pre-registered modest scale.**
Making the caution gate a live function of the frozen doubt readout carries
information beyond deleting the gate — the first use-the-signal result on
this checkpoint family after M/N/R/AA went 0-for-4. Scope: in-distribution,
one layer, one checkpoint, per-item open-loop gains (§ Limitations); a
per-token online controller or held-out transfer is Stage-2 material and
needs a new signed amendment.

## Limitations (pre-stated)

- In-distribution: u_d and the gains are fit on the same frozen row population
  the intervention is evaluated on (the B1 convention). A pass here is a
  mechanism statement about this checkpoint and row set, not a deployable
  controller claim; transfer would need a held-out replication.
- Single layer, single checkpoint, greedy decoding, per-item (not per-token)
  gain. The erase-then-write happens at one site while downstream layers
  recompute freely — the model can in principle reconstruct its gate from
  other pathways; that is part of what makes this a real test, and the most
  likely mechanical reason for a null.

## Changelog

- 2026-07-02: created and signed (conservative framing per user directive).
- 2026-07-03: smoke passed §3 gate; full run (4868 units) + §8 verdict:
  AC-G1 PASS (+8.7pt, CI [+5.6, +12.0]), guard PASS, falsifier not fired.
