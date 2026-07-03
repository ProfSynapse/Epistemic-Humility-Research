# Amendment AE — Training-Free Doubt-Coupled Caution on the Raw Base

Status: DRAFT (unsigned). Prediction, falsifier, gates, and controller constants
lock at signing. Tier-2 exploratory local mechanism evidence under
`PHASE3-control-system-protocol.md` (RQ4 Stage 1, base-model substrate). Not
headline evidence; never pooled with the locked Phase 1 matrix.

Run lane: LOCAL 3090 only. No cloud spend. Queued behind Amendment AC's PR
(one amendment = one branch = one merged PR before the next launches); relative
order vs Amendment AD's launch is the user's call at sign-time.

## 1. Motivation and posture

Amendment AC asks whether the doubt→caution wire carries information on the
TRAINED checkpoint, where an over-firing caution gate already exists and the
coupling *releases* refusals. This amendment asks the mirror question on the
substrate where our strongest result lives: the RAW instruct base.

What is established, and what this cell adds:

- The SENSOR is training-free. Amendments W/X/Y/Z/SR: the full two-signal
  readout (gate 0.997, dial 0.834, veto) reads off raw untrained bases across
  sizes and families; the boundary signal predates post-training (Y). Training
  did not create these activations — it helped us find them.
- The ACTUATOR is so far only proven on the trained checkpoint. caution_perp is
  causally load-bearing there (refined B1: ablate drops known_refused refusal
  0.994 -> 0.524 with specificity), but it was FIT from trained-model refusal
  behavior and has never been fit or tested on the base. Untested is not
  falsified: AA Arm A's flat result steered the DOUBT axis (surface-confounded,
  and flatness was the two-axis prediction) — it says nothing about caution
  steering on the base.
- The base rarely refuses: on unanswerable questions it confabulates
  (Amendment S/U surface — the U veto reads those confabulations as
  lowest-trust, but the base still EMITS them).

So the test is: **can an inference-time doubt-coupled caution write CREATE
calibrated abstention on a model that never trained on abstention?** Sensor
free (W), actuator written in — no SFT, no GRPO, no gradient anywhere. If the
wire carries information here, the two-signal mechanism is a complete
training-free control story at one site; if not, the caution gate is something
post-training ASSEMBLES rather than merely sharpens — which is itself the
cleanest statement of what training buys that we would have on record.

POSTURE — conservative, mirroring AC:

- The use-the-signal side is 0-for-4 on trained checkpoints (M, N, R, AA); AC
  is in flight. We pre-state that prior.
- The named spoiler: writing caution into a base that never expresses refusal
  may push it OFF-POLICY — degenerate JSON, garbled text — rather than into
  clean abstention. A degeneracy guard is gated for exactly this.
- A null is reportable: it bounds the training-free claim at the readout
  boundary ("signals present, control surface absent") and gives Paper 5 its
  sharpest sensor/actuator asymmetry statement.

## 2. Mechanism (pre-registered; identical controller, new substrate)

All quantities live in the L35 residual stream of the RAW base
(`unsloth/Qwen3-4B-bnb-4bit`, NO adapter — the Amendment S/W surface,
model_tag `qwen3-4b-instruct`).

Sensor (read, offline, CPU after one extraction pass): base doubt axis
`u_d_base = unit(mean(h[known_correct_answered]) - mean(h[unknown_answered]))`
fit on BASE activations over the base's own behavior cells (§3). Each eval
row's knownness `d_i = h_i . u_d_base`, standardized over the eval-row
population: `z_i = (d_i - mu_d) / sigma_d`.

Actuator: two caution directions, each orthogonalized against `u_d_base`
(re-orthogonalized in the BASE geometry, so the write never disturbs the
variable being read):

- **D-native (PRIMARY)**: fit on the base itself, same construction as refined
  B1 (`build_caution_perp_direction.py` machinery): contrast refused vs
  answered rows from the base's baseline collection under the standard
  abstention-affording prompt, then project out `u_d_base`. Adequacy floor to
  fit: >= 40 base refusal rows; below floor, D-native is BLOCKED (reported,
  not silently swapped).
- **D-transferred (SECONDARY, descriptive)**: the trained checkpoint's
  committed `caution_perp_direction_L35.json`, re-orthogonalized against
  `u_d_base`. Pre-stated expectation: WEAKER or null (Amendment T precedent:
  probe directions drift across checkpoints — cold transfer 0.679).

Making D-native primary and D-transferred secondary avoids a two-cell
multiplicity problem: AE-G1 is judged on D-native alone; D-transferred is
reported with the same statistics but gates nothing.

Arm mode `couple`, exactly the AC hook (erase + write at every position):

```
h' = h - (h . c_hat) c_hat + g_i * sigma_c * c_hat
g_i = -alpha * z_i, clipped to [-2, +2], alpha = 1
```

The SAME equation as AC — no sign flip, no new constants. On the trained
checkpoint its actionable side was z>0 (feels known -> gate written low ->
release). On the base the actionable side is z<0 (feels unknown -> gate
written high -> refuse). One controller, two substrates: that symmetry is the
point, and it is why nothing here is tuned to the base.

`sigma_c` = row-population std of projections onto c_hat, computed per
direction on the base eval rows (the B1/AC convention).

Permuted placebo: same gains, row-shuffled with a fixed seed (20260704).
Identical dose distribution, information removed — carries the whole claim.

## 3. Cells, rows, arms

Model/prompt/decoding: raw base as §2; the SAME JSON-schema system prompt as
AC/B1 (abstention-affording: "If the answer is not known to you, say 'I don't
know the answer'"); greedy; max_new_tokens 96; enable_thinking false. The
prompt affordance keeps the surface comparable to AC and gives the base a
legal way to express refusal; a no-affordance neutral-prompt variant is
explicitly OUT of this amendment's gates (future descriptive work at most).

Rows: the frozen SelfAware pool (the AD slice: 300 known + 300 unknown). A
one-off BASELINE COLLECTION pass (baseline arm only) assigns each row a base
behavior cell. Primary eval cells:

- `unknown_answered` — base confabulates on an unanswerable question. The
  intervention TARGET: induce refusal here.
- `known_correct_answered` — base answers a known question correctly. The
  specificity cell: keep answering here.

Adequacy floor (pre-stated): >= 150 rows in EACH primary cell under baseline
collection; below floor on either, stop and report (no pool swap). The
S-surface prior (base answers nearly everything; ~72% wrong on the free-answer
set) makes both floors very likely to clear. The refused complement cells
(`unknown_refused`, `known_refused`) are kept for the D-native fit and for
descriptive tables, not gated.

Arms (one pre-registered configuration; no alpha sweep, no coupling-form
fishing), run for D-native and repeated for D-transferred:

| arm | mode | gain |
|-----|------|------|
| baseline | baseline | — |
| coupled | couple | `g_i = -z_i` (real, clipped ±2) |
| permuted | couple | same gains, row-shuffled (seed 20260704) |
| constant | couple | `g ≡ mean(g_i)` over eval rows (uniform dose anchor) |

`constant` replaces AC's `ablate` as the nested constant comparison: on the
base there is no over-firing gate to delete (ablate ≈ noop is the
expectation), so the informative constant control is the same average dose
without modulation — the "just make it refuse more" strawman, quantified.

Smoke gate before each full direction cell: 25 rows/cell x 4 arms (200 units,
D-native first). Pass = ANY directional coupled-vs-permuted separation on the
selectivity gap (point estimate) AND the degeneracy guard holds at point
estimate. If the smoke shows nothing, report the smoke and stop — the
falsifier can fire early and cheaply.

## 4. Gates and falsifier (pre-stated; conservative)

Induced-refusal per arm x cell := arm refusal_rate - baseline refusal_rate
(baseline is ~0 in both primary cells by construction).

Selectivity gap per arm := induced-refusal(unknown_answered) -
induced-refusal(known_correct_answered). (The AC gap, inverted: there the wire
had to RELEASE selectively; here it has to IMPOSE selectively.)

- **AE-G1 (primary, D-native only)**: coupled beats permuted on the
  selectivity gap by >= 5pt, row-level bootstrap 95% CI (10k resamples)
  excluding 0.
- **Degeneracy guard (pass/fail, coupled arm, both cells)**: ungradeable-output
  rate (non-JSON / schema-violating / empty answer) rises <= 5pt vs baseline.
  A "refusal" that is actually output shredding does not count as control;
  refusal grading itself only counts parseable abstentions.
- **Specificity guard (pass/fail, coupled arm)**: among known_correct_answered
  rows that REMAIN answered, correctness drop <= 3pt vs baseline (B1
  convention), and induced-refusal on known_correct_answered <= 15pt (the gap
  can pass while quietly muzzling knowns; this caps that).
- **AE-G2 (secondary, estimate only — no pass/fail)**: policy quality of the
  coupled arm — answered-only accuracy vs baseline answered-only accuracy, and
  point-estimate AUROC of (refused vs known-label) as an abstention-alignment
  summary. D-transferred: full same table, reported, gating nothing.

FALSIFIER: permuted ≈ coupled on AE-G1 (margin < 5pt or CI includes 0) for
D-native. Then the doubt signal contributes nothing through this actuator on
the base; the caution gate is not causally assembled pre-training at this
site. Consequence, pre-committed: report as a negative; NO alpha tuning, NO
alternative direction fits, NO layer sweeps, NO prompt-variant rescues under
this amendment; any Stage-2 proposal must be a new signed amendment engaging
with this null. D-transferred failing while D-native passes (or vice versa) is
reported as-is — the claim rides on D-native alone.

Prediction (cautiously optimistic, ordered):

1. Most likely: D-native passes AE-G1 with a small margin (5-15pt) with some
   degeneracy pressure visible but under the guard; D-transferred weaker or
   null (T-precedent direction drift).
2. Second: the falsifier fires — the base has the sensor but no assembled
   control surface; training builds the actuator. (This closes the
   training-free claim at the readout boundary, cleanly.)
3. A large margin (>25pt) or a squeaky-clean degeneracy profile would be a
   surprise: check gain-map row alignment, permutation correctness, and the
   refusal grader on base idiom before believing it.

## 5. Metrics (all reported, none gated beyond §4)

Per direction x arm x cell: n, refusal_rate, induced-refusal, correct_rate,
ungradeable_rate. Derived per interventional arm: selectivity gap + CI;
answered-only accuracy; dose-response DESCRIPTIVE curve of refusal vs written
gain (binned g_i, coupled arm only — the AC §5 curve, expected to run the
other way: refusal rising with positive g). Baseline collection cell census
(the base's own behavior fingerprint on this pool) reported once.

## 6. Implementation surface (all CPU-testable except the runs)

1. Baseline collection config (NEW): phase3 runner, base model, NO adapter,
   arms = [baseline] only, full 600-row pool. A small overlay builder
   (`build_base_behavior_overlay.py`, NEW, CPU) converts its rows.jsonl into
   the behavior-cell overlay consumed downstream (cell rules pre-stated: refused
   per existing grader; correct per existing grader; ungradeable tracked).
2. Base extraction at L35, pre-answer position, on the same pool/prompt
   (reuse the existing extraction machinery; W/S extractions are checked for
   position/layer compatibility first and reused if they match, else ONE new
   extraction pass — GPU, cheap).
3. `build_doubt_gain_map.py` (EXISTS): reused unchanged with the base
   extraction + base overlay (doubt_pos_cell known_correct_answered,
   doubt_neg_cell unknown_answered) -> `doubt_gain_map_base_L35.json`.
4. `build_caution_perp_direction.py` machinery: D-native fit on base
   extraction/overlay (refused vs answered contrast, >= 40-row floor);
   D-transferred = committed trained direction re-orthogonalized against
   `u_d_base` (small script or flag; the perp-projection step already exists).
5. `phase3_residual_intervention{,_runner}.py`: NO changes expected — couple
   mode, gain maps, vector-alpha batching, and rows_filter all exist. The
   `constant` arm is a couple arm with a degenerate gain map (all rows same
   g), which the existing machinery already supports; if a wrinkle appears it
   gets a test first.
6. `analyze_ac_doubt_coupled.py`: extended (or thin-wrapped) for the inverted
   gap, degeneracy guard, and answered-only accuracy; same paired row-level
   bootstrap. CPU tests mirror the AC analysis tests.
7. Equivalence: the engine's batched path is qualified (PR #154 spot check);
   either engine is acceptable here since the instrument is being registered
   NOW as either-engine (fingerprint records which; no mid-cell switching).

## 7. Provenance

- Base surface: `unsloth/Qwen3-4B-bnb-4bit`, no adapter — Amendment S free-answer
  surface; W ran the full two-signal readout on it (gate 0.997 / dial 0.834 /
  veto 0.75).
- Trained-side comparison constants: refined B1 (ablate 0.994 -> 0.524,
  de-refused correctness 68.7%); AC's result lands in its own §8 and is the
  trained-substrate twin of this cell.
- Sensor-side training-free evidence: W (base), X (1.7B-14B), Y (pre-train-only
  era), Z+SR (cross-family, seed-robust).
- Direction-transfer prior: T (cold probe transfer 0.679, direction drift);
  P (caution-direction cosine 0.185 across datasets while READOUT transfers) —
  both argue D-transferred is the weaker horse, as pre-stated.
- Analysis outputs stay untracked per the phase3 convention; summary numbers
  and the verdict land in this doc's §8 and the session note.

## 8. Result

(unfilled — no run authorized yet; sign first, then baseline collection +
smoke, then full per §3)

## Limitations (pre-stated)

- In-distribution: u_d_base, both directions, and the gains are fit on the
  same frozen row population the intervention is evaluated on (the B1/AC
  convention). A pass is a mechanism statement about this base, pool, and
  site — not a deployable training-free-abstention product claim; transfer
  needs a held-out replication.
- Single layer, single base checkpoint, greedy decoding, per-item (not
  per-token) gain; downstream layers recompute freely and may reconstruct or
  ignore the written gate — the most likely mechanical route to a null.
- Greedy may understate effects (SR: sampled decode revealed what greedy
  hid); if the result is a near-miss null, a sampled-decode replication is a
  legitimate NEW amendment, not a rescue of this one.
- The prompt affordance means this tests "training-free" abstention control,
  not "prompt-free": the instruction names the abstention option; the wire
  decides WHEN. Removing the affordance entirely is future work.

## Changelog

- 2026-07-03: drafted (user-directed: base-model mirror of AC; "everything we
  found around answerability doubt and caution showed up with no training" —
  this cell tests exactly whether that extends from sensor to actuator).
