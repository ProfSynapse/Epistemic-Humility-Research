# Amendment AE — Training-Free Doubt-Coupled Caution on the Raw Base

Status: SIGNED 2026-07-03 (user, in-conversation: "Sign it and boot it up";
launch approved in the same message). Prediction, falsifier, gates, and
controller constants are LOCKED as written. Tier-2 exploratory local mechanism
evidence under `PHASE3-control-system-protocol.md` (RQ4 Stage 1, base-model
substrate). Not headline evidence; never pooled with the locked Phase 1 matrix.

Run lane: LOCAL 3090 only. No cloud spend. Amendment AC's PR (#156) is MERGED
with AC-G1 PASS, so the one-merged-PR-at-a-time discipline is satisfied; the
user prioritized AE ahead of Amendment AD's launch (2026-07-03, "let's skip to
AE since we found something useable").

## 1. Motivation and posture

Amendment AC asks whether the doubt→caution wire carries information on the
TRAINED checkpoint, where an over-firing caution gate already exists and the
coupling *releases* refusals. This amendment asks the mirror question on the
substrate where our strongest result lives: the RAW instruct base.

What is established, and what this cell adds:

- The SENSOR is training-free. Amendment W (result table): answerability gate
  known/unknown AUROC **0.997 @ L18** (pre-gen anchor, CI [0.995, 0.999]) on
  the raw base; correctness dial 0.834 @ L20 post-gen (S); hallucination veto
  0.7545 @ L20 (CI [0.728, 0.782]). X replicates the gates across 1.7B-14B; Y
  shows the boundary signal predates post-training; Z/SR cross-family. W's own
  headline: "the mechanism is a readout property of the untrained base ...
  What GRPO training buys is *behavioral* abstention (the model refuses on its
  own) and a *sharper* veto (+0.226) — not the latent signal itself"; gate
  gain from training ~0 (0.997 -> 0.999).
- The ACTUATOR is so far only proven on the trained checkpoint. caution_perp
  is causally load-bearing there (refined B1: ablate drops known_refused
  refusal 0.994 -> 0.524 with specificity), but it was FIT from trained-model
  refusal behavior (pos=known_refused n=168, neg=known_correct_answered n=373,
  doubt axis projected out; raw caution-doubt cos -0.83, perp fraction 0.558)
  and has never been fit or tested on the base. Untested is not falsified:
  AA Arm A steered the GATE/DIAL (answerability/trust) axes, not caution; its
  flatness was surface-confounded and predicted by the two-axis view — it says
  nothing about caution steering on the base.
- The base's behavior under THIS amendment's prompt is uncharacterized, and we
  say so rather than assume. The "answers freely / confabulates on
  unanswerables" evidence (S: n_answered 1836, 500 correct / 1336 wrong; W's
  forced-answer hallucination set) comes from ANSWER-ENCOURAGING or forced
  surfaces on PopQA/TriviaQA-heavy pools. Under an abstention-AFFORDING prompt
  on SelfAware, the instruct base may abstain more than those surfaces
  suggest. The baseline-collection pass (§3) is the first measurement of this,
  and the adequacy floors gate on its outcome in BOTH directions.

So the test is: **can an inference-time doubt-coupled caution write CREATE
calibrated abstention on a model that never trained on abstention?** Sensor
free (W), actuator written in — no SFT, no GRPO, no gradient anywhere. If the
wire carries information here, the two-signal mechanism is a complete
training-free control story at one site; if not, the caution gate is something
post-training ASSEMBLES rather than merely sharpens — which is itself the
cleanest statement of what training buys that we would have on record.

POSTURE — conservative, updated for AC's result (2026-07-03, its §8):

- The use-the-signal record is now 1-for-5: M, N, R, AA failed, then **AC
  PASSED** — coupled beat permuted +8.7pt (CI [+5.6, +12.0]) and beat constant
  ablate +10.7pt (CI [+7.1, +14.5]). The SAME controller equation, gain
  machinery, and erase+write hook AE uses just carried information on the
  trained substrate. The updated prior, stated honestly: the WIRE is proven;
  what remains untested is whether the base has a control surface for it to
  actuate.
- AC's mechanism decomposition is the directly load-relevant precedent: the
  coupling's entire edge was on the POSITIVE-gain side — writing the gate
  HIGH on high-doubt rows HELD unknown_refused refusal at 0.580 where
  constant ablate released it to 0.503. That is existence proof that the
  caution WRITE (not just the erase) causally raises refusal on the trained
  model. AE's actionable side is exactly that positive-gain write; the
  substrate changes, the actuation direction does not.
- The named spoiler: writing caution into a base that never expresses refusal
  may push it OFF-POLICY — degenerate JSON, garbled text — rather than into
  clean abstention. A degeneracy guard is gated for exactly this.
- A null is reportable: it bounds the training-free claim at the readout
  boundary ("signals present, control surface absent") and gives Paper 5 its
  sharpest sensor/actuator asymmetry statement.

## 2. Mechanism (pre-registered; identical controller, new substrate)

Substrate: the RAW base (`unsloth/Qwen3-4B-bnb-4bit`, NO adapter — the
Amendment S/W checkpoint, model_tag `qwen3-4b-instruct`). The WRITE site is
the L35 residual stream (fixed: it is where both caution directions live and
where B1/AC intervened; no base evidence localizes a caution axis anywhere, so
parallelism is the only non-arbitrary choice — named in Limitations). The READ
layer is chosen by the pre-stated rule below and may differ from L35.

Sensor (read, offline, CPU after one extraction pass): base doubt axis
`u_d_base = unit(mean(h[known_correct_answered]) - mean(h[unknown_answered]))`
fit on BASE activations over the base's own behavior cells (§3).

Two pre-stated deviations from the AC sensor, with reasons:

- **Negative cell**: AC used `unknown_refused`; here it is `unknown_answered`,
  because the base's unknown-refused cell may be tiny and unknown_answered is
  the intervention target. This changes the axis semantics slightly
  (knownness-vs-confabulation rather than knownness-vs-refused-unknown); it is
  the base-appropriate mean-difference analog, not a swap made after seeing
  results.
- **Sensor read layer**: AC read at L35 because the trained doubt axis was
  validated there (AUROC 0.972). There is NO base evidence at L35; the base
  gate evidence is 0.997 @ L18 pre-gen (W). Rule, fixed before any
  intervention run: read `u_d_base` at the layer maximizing known/unknown
  AUROC on the frozen AE extraction (deterministic offline rule on the frozen
  pool, computed once, before any intervention). Sensor adequacy floor:
  that AUROC >= 0.90, else stop and report (no layer shopping beyond the one
  pre-stated argmax rule, no intervention run on an inadequate sensor).

Each eval row's knownness `d_i = h_i . u_d_base`, standardized over the
eval-row population: `z_i = (d_i - mu_d) / sigma_d`. Read and write layers may
differ; the read is offline from frozen activations before any intervention
(the AC convention), so no within-item feedback exists either way.

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
collection; below floor on either, stop and report (no pool swap). We do NOT
predict the census: the S-surface prior ("answers freely") is from an
answer-encouraging prompt on a different pool and may not transfer to an
abstention-affording prompt on SelfAware. Both failure directions are live and
pre-stated: (a) the base refuses almost never -> D-native falls under its
40-row fit floor -> the PRIMARY cell is VOID (reported; D-transferred remains
descriptive only; no silent promotion of D-transferred to primary); (b) the
base refuses so much that unknown_answered falls under 150 -> stop and report
(there is then little confabulation to suppress and the experiment's premise
is thinner than assumed — itself an informative census). The refused
complement cells (`unknown_refused`, `known_refused`) are kept for the
D-native fit and descriptive tables, not gated.

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

Prediction (cautiously optimistic, ordered; bands unchanged by AC's pass —
the evidence moved our confidence in the WIRE, not in the base's surface):

1. Most likely: D-native passes AE-G1 with a small margin (5-15pt) with some
   degeneracy pressure visible but under the guard; D-transferred weaker or
   null (T-precedent direction drift). AC's quantitative anchor: on the
   trained substrate the positive-gain write was worth ~8pt of held refusal
   over no-modulation (ur 0.580 vs 0.503); a base effect of similar order is
   the optimistic case, since there the write must overcome a never-trained
   policy rather than reinforce a trained one.
2. Second: the falsifier fires — the base has the sensor but no ASSEMBLED
   control surface (W's "training buys behavioral abstention" as substrate
   fact, not just behavior description); training builds the actuator. This
   closes the training-free claim at the readout boundary, cleanly, and
   makes the AC-vs-AE contrast the paper's sensor/actuator asymmetry figure.
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
2. Base extraction, pre-gen anchor position, ALL layers, on THIS amendment's
   pool + prompt (NEW pass — GPU, cheap). The S/W extractions canNOT be
   reused: S is the answer-encouraging neutral prompt on PopQA/TriviaQA, W is
   the forced-answer surface; the sensor must be read under the same rendered
   prompt the intervention runs on. Use the R/session-0029 faithful pre-gen
   anchor position (the cos-0.9998 render), as S did.
3. `build_doubt_gain_map.py` (EXISTS): reused with the base extraction + base
   overlay (doubt_pos_cell known_correct_answered, doubt_neg_cell
   unknown_answered; sensor layer per the §2 argmax rule) ->
   `doubt_gain_map_base.json`.
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

- Base checkpoint: `unsloth/Qwen3-4B-bnb-4bit`, no adapter (model_tag
  `qwen3-4b-instruct`) — the S/W checkpoint. Note the SURFACES differ: S was
  free-answer under an answer-encouraging neutral prompt (PopQA+TriviaQA,
  n_answered 1836 -> 500 correct / 1336 wrong); W added forced-answer
  generation for the veto set. AE's abstention-affording SelfAware surface is
  new and gets its own baseline census + extraction.
- Sensor-side training-free evidence (W result table): gate 0.997 @ L18
  pre-gen CI [0.995, 0.999]; dial 0.834 @ L20 post-gen (S); veto 0.7545 @ L20
  CI [0.728, 0.782]; training buys +0.226 veto sharpening and ~0 gate gain.
  X (1.7B-14B), Y (pre-train-only era), Z+SR (cross-family, seed-robust).
- Trained-side comparison constants: refined B1 (ablate 0.994 -> 0.524,
  de-refused correctness 68.7%); caution_perp artifact:
  `caution_perp_direction_L35.json` (L35, hidden 2560, sigma 25.53,
  pos known_refused n=168, neg known_correct_answered n=373, raw
  caution-doubt cos -0.83, perp fraction 0.558).
- AC result (trained-substrate twin, its §8, 2026-07-03, PR #156): AC-G1 PASS
  +8.7pt CI [+5.6, +12.0] over permuted; +10.7pt CI [+7.1, +14.5] over
  constant ablate; the edge lives on the positive-gain side (coupled held
  unknown_refused at 0.580 vs ablate 0.503); dose-response monotone through
  the actionable range; de-refused correctness flat across arms (~0.67-0.70).
  In-frame B1 replication: ablate kr 0.994 -> 0.536.
- Direction-transfer prior: T (S-fit dial probe applied cold across
  checkpoints reads 0.679 — the transferable component drifts);
  P (cross-DATASET caution-direction cosine 0.185 while the answerability
  READOUT transfers near-fully) — both argue D-transferred is the weaker
  horse, as pre-stated.
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
- Single write layer, single base checkpoint, greedy decoding, per-item (not
  per-token) gain; downstream layers recompute freely and may reconstruct or
  ignore the written gate — the most likely mechanical route to a null.
- The L35 write site is an ASSUMPTION on the base: it is inherited from
  B1/AC parallelism and from D-transferred living there, not from any base
  localization evidence (the base's known readout peaks are L18 pre-gen /
  L20 post-gen). A null here is therefore "no effect at this site with these
  directions," not "no caution surface anywhere in the base"; a layer sweep
  would be a new amendment.
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
- 2026-07-03: corrected against primary sources (W/S/B1/T/P): sensor layer
  rule + floor, census language neutralized, extraction reuse ruled out.
- 2026-07-03: updated for AC's result before signing (user: "Before signing
  anything we should change based on our results"): posture now 1-for-5 with
  the wire proven; AC's positive-gain-write evidence (ur 0.580 vs 0.503)
  named as the direct precedent for AE's actionable side; quantitative anchor
  added to prediction 1; AC constants added to §7. Gates, falsifier, bands,
  and controller constants UNCHANGED by the update.
