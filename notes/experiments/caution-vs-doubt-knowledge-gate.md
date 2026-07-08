---
title: 'Caution vs Doubt: a late refuse/answer gate over an early knowledge axis'
kg:
  id: experiment:caution-vs-doubt-knowledge-gate
  type: experiment
  status: canonical
tags:
  - kg/experiment
  - mech-interp
  - caution-axis
  - knowledge-axis
  - doubt
status: running
governance: exploratory
phase: phase3
lane: local
est_compute: '~1-3 GPU-hours/RTX 3090 per GPU slice; the headline knowledge/depth analysis is GPU-free'
relationships:
  - type: tests
    target: '[[gap-4-probe-transfer]]'
    target_id: gap:4-probe-transfer
    confidence: high
  - type: builds_on
    target: '[[uncertainty-monitor-hypothesis]]'
    target_id: experiment:uncertainty-monitor-hypothesis
related:
  - '[[uncertainty-monitor-hypothesis]]'
  - '[[mech-interp-model-variation-panel]]'
---

## Question & Hypothesis

This note branches off [[uncertainty-monitor-hypothesis]]. That line established the
**caution axis (A2)**: a deep, knowledge-orthogonal, lexically-clean direction at
L35 that separates within-known over-refusals from answered knowns (~0.91 AUROC),
and (B2) fires *before* the refusal is verbalized (pre-commitment). The open
question that line could not resolve is **what the caution signal is reading**.

**RQ.** Are **caution** (the refuse/answer decision) and **doubt** (graded
internal uncertainty about the answer) *separable* signals living in *different
places and depths*? And is within-known over-refusal better described as a
**miscalibrated late gate over borderline-known items**, rather than suppression
of fully-known answers?

**Hypothesis (two-stage gate).**
1. **Doubt** = graded position on an **early knowledge axis** (how knowable is
   this item), legible from the input.
2. **Caution** = a **late binary gate** (back-half layers, peaking ~L35) that
   reads that doubt and decides whether to withhold.
3. Over-refusal happens when *genuine intermediate doubt* meets an
   *over-aggressive caution gate* — not when the model withholds a fully-known
   answer.

**Falsifiers.**
- Doubt and caution are the *same* direction (high cos under a rigorous,
  non-shared-anchor / whitened comparison) → reject the two-signal claim.
- Over-refused items project as fully "known" (indistinguishable from answered
  knowns on a clean knowledge axis) → the "borderline" reframing fails; revert to
  the stronger "suppression of known answers" reading.
- Emitted `response_confidence` tracks the caution axis as well as / better than
  the knowledge axis → caution is not a *binary* gate distinct from graded doubt.

## Design

Pinned identity (same as the A.4 sweep / B2): SFT-merged Qwen3-4B base +
`clean_sft_grpo_v2` adapter; JSON response_confidence system prompt;
extraction `extraction__55254a04aa1f`; behavior rows
`current_selfaware_behavior_rows/clean_sft_grpo_v2/rows.jsonl`.

Three behavior cells carry the contrasts (counts in the full overlay):
`known_refused` (168), `known_correct_answered` (373), `unknown_refused` (676).
Two orthogonal contrasts fall out of holding one factor fixed:
- **CAUTION** = `known_refused` vs `known_correct_answered` (knowledge fixed=known,
  vary behavior) — the A2 axis.
- **KNOWLEDGE** = `known_refused` vs `unknown_refused` (behavior fixed=refused,
  vary knowability) — isolates the knows/doesn't-know signal at constant action.

### Founding result (GPU-free, recorded 2026-06-27)

Layer-resolved 5-fold logistic AUROC, h_lora, end-of-question residuals, balanced
168 rows/group (`scratchpad/depth_knowledge_caution.py`):

| layer | CAUTION (kr vs ka) | KNOWLEDGE (kr vs ur) |
|------:|-------------------:|---------------------:|
| L2    | 0.704              | 0.969                |
| L6    | 0.740              | 0.988                |
| L18   | 0.834              | 0.988                |
| L26   | 0.898              | 0.996                |
| L34   | 0.879              | 0.996                |
| L35   | 0.907              | 0.996                |
| L36   | 0.897              | 0.996                |

- **Knowledge is early + near-ceiling** (0.97 from L2). Caveat: extraction is at
  the *end of the question prompt, pre-generation*, so this is **prospective
  answerability / question familiarity**, not verified answer retrieval. The
  early saturation is consistent with surface familiarity of the question.
- **Caution is late + climbing**, peaking at L35 (the *second-to-last* block;
  37 hidden states L0..L36). The refuse-vs-answer decision among known items is a
  **late-forming gate**, not settled early.
- **Humility-tax projection.** Clean knowledge axis fit on `ka` vs `ur` (never
  sees `kr`); project the over-refused group: `ka`=-180 (known anchor),
  `kr`=-228, `ur`=-297 (unknown anchor) → over-refused sit **58% of the way from
  UNKNOWN toward KNOWN**. Over-refused items are an **intermediate, partially-known
  population**, not internally identical to confidently-answered ones.

Geometry caveat: raw mass-mean cos(caution, knowledge) ≈ -0.5, but inflated by the
shared `kr` anchor; the rigorous whitened-probe orthogonality (~0.02, session
0025) is the trusted separation number.

## Prerequisites & Gating

- Extraction `extraction__55254a04aa1f` present (h_lora safetensors L0..L36).
- Behavior overlay rows present with `behavior_cell`.
- GPU slices gated behind explicit user approval for the live Docker/unsloth run
  (docker.exe, image `unsloth/unsloth:latest`, mount
  `F:\Code\Epistemic-Humility-Research:/workspace/repo`, entrypoint
  `/opt/venv/bin/python`, uid-1001 output dirs pre-created + chmod 777).

## Runbook

1. **GPU-free — doubt-vs-caution split via emitted confidence** (next slice):
   correlate per-row emitted `response_confidence` (parsed from the JSON answer)
   against caution-axis and knowledge-axis projections on **answered** rows.
   Prediction: graded confidence ~ knowledge axis (doubt); caution axis tracks
   the binary refuse/answer split but not graded confidence.
2. **GPU — doubt axis from generations**: mass-mean contrast over generated
   hedged-but-answered ("I think X, though I'm not certain") vs confident-asserted
   ("It's X") completions, **no refusals in either arm**. Report cos(doubt,
   knowledge) and cos(doubt, caution); read-trajectory to test causal ordering
   (does doubt fire before caution in the stream?).
3. **GPU — layer-band caution ablation**: ablate the caution axis across a sweep
   of single layers; find the earliest layer where over-refusal drops = where the
   gate becomes load-bearing. (Companion to the B1 single-site L35 ablation in
   [[uncertainty-monitor-hypothesis]].)

## Validation contract

- AUROC tables come from held-out CV (`cv_auroc`, StratifiedKFold), never
  in-sample fits, for any separability claim.
- Projection/"humility-tax" claims use a knowledge axis fit on groups that
  EXCLUDE the projected group (no circularity).
- Geometry (cos) claims state the construction and flag shared-anchor inflation;
  prefer whitened / non-overlapping-anchor numbers for headline separation.
- Treat all outputs as Tier-2 exploratory local mechanism evidence; single seed.

## Outputs & provenance

Analyses land under `experiment/phase1/probe/analysis/` (GPU outputs gitignored);
findings recorded in `docs/sessions/20260627T093723Z-caution-vs-doubt-knowledge-gate.md` and
here. This branch does not feed the meta-analysis until promoted by a governed
decision.

## Variations

- Source role: `h_lora` (default) vs `delta` vs `h_base` for the depth profile.
- Answer-position vs prompt-position extraction to separate "question
  familiarity" from "verified retrieval" in the knowledge signal.
- KUQ vs SelfAware framing (the caution construct flips on KUQ; check whether the
  knowledge axis / depth profile is more stable across datasets than caution).

## Revision (2026-06-27): single graded doubt axis, not two clean signals

GPU-free `scratchpad/confidence_vs_axes.py` (556 B2 known rows) updates the
hypothesis and **walks back the strict two-signal claim**:

- **Emitted `response_confidence` is flat/uninformative** (~0.82 on correct
  answers, ~0.81 on wrong) → ~zero Spearman with either axis. The model does not
  *verbalize* internal doubt; the channel cannot adjudicate doubt-location. (A
  calibration/expression gap: the internal axis knows more than the stated number.)
- **The knowledge axis itself separates refuse/answer strongly** (AUROC 0.873 in
  the "refuse = less-known" direction), and its ordering is **monotonic**:
  correct-answered (-184) > wrong-answered (-202, n=15 tentative) > refused-known
  (-228) > unknown (-297). It tracks *real* correctness even among answered items.
- **Caution and the clean knowledge axis are largely collinear in raw space**:
  raw mass-mean cos ≈ **-0.83**, *not* the ~0.02 near-orthogonality reported in
  session 0025 (that was a whitened/logistic construction). Both can hold: shared
  bulk variance, near-orthogonal residual.

**Updated leading account:** the dominant raw geometry is **one graded epistemic
(knowledge/doubt) axis**; within-known over-refusal is **thresholding its
low-known tail**, i.e. caution is largely *doubt-thresholding*, with only a small
whitened-orthogonal caution-specific residual on top. The strict "early doubt +
separate late binary gate" picture is downgraded; the *depth* split (knowledge
early, refuse/answer separability late) still stands.

**Caveat this forces onto B1:** ablating the raw caution θ at L35 is ~83%
ablating the knowledge/doubt axis too. So the `known_correct_answered`
specificity control becomes the key discriminator — if ablation *also* harms
answered-correctness, we removed doubt/knowledge, not a clean gate.

## Resolution (2026-06-27): a separate gate DOES exist — held-out, not cosine

`scratchpad/caution_residual_geometry.py` (L35, kr=168/ka=300/ur=300,
shrinkage-whitened cov, 5-fold held-out) settles the oscillation:

- Raw cos(caution, knowledge) = **-0.83**, but **whitened/Mahalanobis cos =
  -0.56**, and **55.7%** of the caution direction is orthogonal to the doubt axis.
- **Held-out refuse/answer AUROC among knowns:** doubt axis alone **0.875**
  (refuse = low-known tail); caution **with the doubt axis projected out** still
  **0.825**; full caution 0.894. Removing the entire rank-1 doubt direction barely
  dents refuse/answer separability → **a genuine caution-specific gate exists,
  not reducible to doubt-thresholding.**

**Method lesson (durable):** raw cosine in high-dim activation space is dominated
by a few shared high-variance dimensions and *overstates* collinearity. Trust
**held-out discriminability after orthogonalization**, not raw cosine. This also
reconciles the session-0025 whitened ~0.02 (stronger whitening drives -0.83 →
-0.56 → toward 0).

**Settled model (revised two-component):** a graded **doubt/knowledge axis**
(refuse = its low-known tail) **plus** a partially-separate **caution gate**
carrying refuse/answer structure orthogonal to doubt (≥55% of the caution
direction). They are *correlated* (both elevated on the low-known tail) but
*separable*. Open: the orthogonalization removed only the rank-1 mass-mean doubt
direction; a full multi-dim knowledge-probe subspace removal is the stronger test.

**Refined B1 design:** the cleanest causal arm ablates the **doubt-orthogonalized
caution_perp** direction (isolates the gate), not the raw θ (83% doubt-aligned).
The in-flight single-site L35 raw-θ ablation is still informative *if* read with
the `known_correct_answered` control as the doubt-vs-gate discriminator.

## Status log

- 2026-06-27: created (running). Founding GPU-free depth/knowledge/projection
  result recorded; branched from [[uncertainty-monitor-hypothesis]].
- 2026-06-27: confidence-vs-axes slice done → emitted confidence flat; caution and
  knowledge largely collinear (raw cos -0.83); single-graded-doubt-axis account
  adopted (see Revision). Next: whitened + split-half non-overlapping-anchor
  geometry to size the caution-specific residual; re-read B1 under the
  collinearity caveat.
- 2026-06-27: linchpin geometry done (see Resolution) → caution_perp held-out
  AUROC 0.825 after projecting out doubt → **separate gate confirmed**; raw cosine
  retired as an instrument in favor of held-out discriminability. Revised
  two-component model settled. Next: multi-dim knowledge-subspace removal; refined
  B1 ablates caution_perp; re-read in-flight B1 with the known_answered control.
- 2026-06-27: calibration gap quantified (`scratchpad/calibration_gap.py`,
  n=389 answered, 16 wrong → directional). EMITTED confidence flat (mean 0.821,
  std 0.015) + underconfident (says 0.82, right 96%), AUROC 0.56, **ECE 0.142**.
  Doubt-axis logistic probe **ECE 0.004**, AUROC 0.65–0.67. Per-cell confidence
  flat (0.811–0.821) vs doubt monotone (correct −176 > wrong −194 > refused −226).
  Headline: **"the model knows but doesn't say"** — internal state is calibratable
  by linear readout; the verbalized number is a collapsed prior. Likely cause: no
  proper-scoring pressure on the confidence field in training. Unifying synthesis:
  refusal AND stated-confidence are both timid readouts decoupled from one
  well-ordered doubt axis (refusal gradient-hypersensitive; confidence flat+low).
  Next: power the discrimination test with more wrong-answered rows; consider a
  Brier/log-loss confidence retrain (links to session 0018).
- 2026-06-27: **B1 causal intervention COMPLETE (GPU, 2164 units, raw-θ L35).**
  Verdict **LOAD-BEARING**. Ablating the caution axis on `known_refused`:
  refusal **0.994 → 0.030** (Δ−0.96) and **57.1%** of the de-refused knowns answer
  **correctly** (knowledge recovery). **Specificity holds:** `known_correct_answered`
  refusal stays **0.00** (+0.00 collateral), correct-rate 1.00 → 0.979 (≈intact).
  Dose-response is **monotone & bidirectional**: shift_plus2 (+2θ) *induces* 19.6%
  new refusals on previously-answered knowns and saturates known_refused at 100%;
  shift_minus2 (−2θ) partially de-refuses (refusal 0.65, 28.6% correct); ablate is
  the strongest de-refusal. **Reading under the 83%-doubt-aligned caveat:** the
  specificity control passes (answering not harmed), so this is not a global
  doubt/knowledge wipe — it is behaviorally specific to the over-refusal direction.
  The 57% (not ~98%) correct-on-de-refusal is the two-component fingerprint: the
  over-refusal was *partly* spurious caution (recovered) and *partly* real residual
  doubt (the bundled doubt component — these knowns are genuinely harder). Confirms
  the caution gate is **causal for over-refusal**, not merely correlational.
  Next: refined B1 ablating **caution_perp** (doubt-orthogonalized) to attribute
  the residual split cleanly; commit B1 module/runner/config/tests + PR.
