# Evidence-responsiveness: the naming test (M4)

Status: SIGNED 2026-07-17 (PI conditional authorization in conversation: sign unless the pre-sign red-team found something prediction-changing; it did not. Instrument pinned at sign). Pre-sign red-team applied; see NOTEBOOK 2026-07-17.

## Motivation and posture

The framework's earnability criterion for mentalistic names (docs/research/
margin-theory-framework.md section 3) has four parts. A name like "doubt" is
earned for the c_hat activation when it (a) tracks actual ignorance, (b)
drives abstention when amplified, (c) does so direction-specifically, and (d)
"responds to evidence the way doubt should: supplying the true answer
in-context should collapse the projection on that row and lengthen its
margin." Qwen satisfies (a) through (c); (d) is the one untested part, and M4
tests it. Mistral fails (c), so mentalistic naming is already retired there
regardless of (d): M4 is qwen-only, consistent with the qwen-only spine.

M4 is the naming test the framework names in section 4: "Supply the true
answer in-context; measure the c_hat projection shift and the margin shift on
the same rows." It is a within-row paired comparison with a large expected
effect if (d) holds, so unlike M1b (a boundary point-estimate sitting inside
the instrument noise) it is well-posed against the ~4% batch-composition
tipping noise M1b characterized, provided the paired arms share one batching
regime (the M1b instrument lesson, applied here from the start).

Posture: exploratory instrument/mechanism tier, qwen35_4b only, reported
separately, never pooled with the locked Phase 1 headline matrix. M4
adjudicates a naming criterion; it cannot move a locked verdict.

## Design

Substrate, the c_hat known-unknown direction (hs20, layer_index 19), the dose
law, the detector stack, and the capture convention are carried from the
M1/M2 lineage byte-identically (pins in `cell.yaml`). The readout SIGN is
pinned explicitly (registered score = negative z, confab-positive): the raw
on-disk projection is confab-negative, the same trap that halted M2's S1 gate
and that the design derivation re-hit on its first pass.

Two channels, three arms, on M1's registered subsample (design derivation at
`analysis-committed/design_derivation/m4_design_report.json`, which reproduced
M1's confab median tipping 9.456 and M2's readout AUROC 0.9821 exactly before
deriving):

- **Channel 1, projection collapse** (capture only, forward pass, no
  generation): the per-row negative-z c_hat projection in each arm, on all
  400 confab rows and 360 known rows. Confab test is a conjunction: leg 1,
  the paired median shift toward the known regime
  (no_answer_baseline_z minus true_answer_z) meets a floor; leg 2,
  specificity, the true-answer shift exceeds the false-answer shift by a
  paired bootstrap 95% CI excluding zero.
- **Channel 2, margin lengthening** (single-dose survival, Option A): for
  each of the 308 confab rows with a genuine (non-censored) M1 tipping dose,
  the boundary push is applied at that row's own M1 tipping dose under each
  generation arm; the row "survives" if it is non-abstaining and well-formed
  there, meaning its margin lengthened past its baseline tipping point. The
  test is the paired survival-rate difference (true minus false). The
  no_answer_baseline survival is expected ~0% by construction but is measured
  (not assumed), doubling as an in-regime staleness check on the reused M1
  tipping doses (channel-2 S1; pre-sign red-team m3).

The context is injected BEFORE the question in the two answer arms so the
len-1 capture anchor stays the question's last token in all three arms, the
position where c_hat was validated by M2 (AUROC 0.982); injecting after the
question would move the anchor to the suffix and make leg 1 a cross-anchor
comparison (pre-sign red-team M1). Three arms: no_answer_baseline (recaptured
fresh in-regime, not reused from M2), true_answer (gold answer injected
in-context before the question), false_answer_placebo (a within-dataset
category-matched distractor). All arms captured and generated in one
self-consistent batching regime with pinned batch composition. Total new
model passes: 2280 captures + 924 generations (308 x 3 arms) = 3204, on the
local 3090.

Instrument configs pinned at sign: `cell.yaml`, `gates.yaml`.

## Decision record

Each knob is DERIVED (from committed data), CONVENTION (carried from a
resolved experiment), JUDGMENT (a choice with rationale), or TO-CONFIRM (a
recommended default the PI confirms or adjusts at sign).

1. **Collapse floor** (DERIVED, LOCKED at sign): leg 1 floor = 0.5 x the
   baseline median gap, 0.9741885346591197 z (half-way from the confab median
   3.0005 to the known median 1.0521, both from committed M2 data). The
   derivation offered 0.25/0.5/0.75/1.0 x gap; 0.5 is the "meaningfully toward
   the known regime" bar matching criterion (d)'s qualitative wording. The
   other three fractions are NOT retained as fallbacks (pre-sign red-team m6:
   exactly one fraction is the registered bar, no post-hoc selection). The gap
   is estimated tightly (Cohen's d 3.34, AUROC 0.982), so baseline-gap noise is
   not the binding constraint; the specificity leg guards the real risk (a
   shift from any injected text rather than the true answer). Leg 1 is a clean
   SAME-anchor comparison after the before-question template fix (red-team M1),
   and is read only after the S1 baseline-reproduction gate confirms the fresh
   baseline reproduces M2's confab median 3.0005 within 0.10 z (red-team M2).
2. **Specificity leg** (JUDGMENT, required): leg 2 exists because leg 1 alone
   cannot distinguish "responds to the true answer" from "responds to any
   in-context answer-shaped text," which is the whole point of a naming test.
   The false-answer placebo arm supplies the contrast. This is the
   derivation's insistence and the orchestrator adopts it as non-optional.
3. **Known-row margin control** (JUDGMENT): known rows get the channel-1
   projection specificity check only, no channel-2 margin test. 89.4% of
   known rows are right-censored (no finite own-tipping dose to lengthen), so
   a margin test would re-measure a ceiling. The projection control still
   does its job (a row already in the known regime should show little
   collapse).
4. **Margin-lengthening design** (DERIVED population + JUDGMENT option):
   Option A single-dose survival at each row's own M1 tipping dose (308 rows;
   924 generations across three arms including the baseline staleness arm)
   over Option B full-ladder re-run (6160+ generations, 10x), because
   re-laddering reintroduces the M1b batch-composition tipping noise at every
   rung for no benefit at the one dose that matters. The no_answer_baseline
   arm is generated (not assumed 0%) as a channel-2 staleness check: if its
   survival exceeds 0.05 the reused M1 doses do not reproduce in-regime and
   channel 2 is voided (red-team m3).
5. **Margin floor** (DERIVED, LOCKED at sign): D2 absolute floor 0.056, the
   normal-approx (Wald) 95% half-width 1.96*sqrt(0.25/308)=0.0558 at worst-case
   p=0.5, n=308, rounded to 0.056 (an unpaired anchor; the paired design has
   strictly smaller variance, so a real effect is comfortably resolvable), plus
   the CI-excludes-zero condition. This is the normal-approx, not a true Wilson
   interval (Wilson at n=308 is 0.0555; both round to 0.056); label corrected
   per red-team m4.
6. **Instrument reuse and sign** (CONVENTION): c_hat hs20 direction (sha256
   937d1bff...), layer_index 19, negative-z confab-positive orientation, and
   the M1/M2 capture and detector stacks, all byte-identical. The sign is
   pinned in harness code, never re-derived at runtime.
7. **Single batching regime** (CONVENTION from M1b): all arms captured and
   generated in one run with a pinned, recorded batch composition; the M2
   baseline capture is recaptured fresh rather than reused, so no paired
   comparison mixes batching regimes.
8. **Seeds** (CONVENTION): bootstrap 48260721, distractor permutation
   48260722, calibration slice 48260723; continuing the registered lineage
   (M1 ...714-16, M2 ...717-18, M1b ...719-20).
9. **False-answer construction** (JUDGMENT): a within-dataset,
   category-matched distractor drawn by a seeded permutation; the
   row_key -> donor_key mapping (opaque ids, no text) is committed
   pre-generation. Answer-shaped and category-appropriate but incorrect.
10. **Self-blinding** (CONVENTION from M2): no paired shift, specificity
    difference, or survival rate computed pre-sign; only baseline
    distributions, hashes, counts, and id lists of already-committed data.

## Prediction

Supplying the true answer in-context both collapses the c_hat projection on
confab rows (paired median shift toward the known regime at or above the
floor, and specifically larger than the false-answer placebo) and lengthens
their margins (true-answer survival at each row's own tipping dose exceeds the
placebo by more than the floor, CI excluding zero): qwen earns earnability
criterion (d), and the known-unknown direction responds to evidence the way
doubt should.

## Falsifier

With all gates valid, at least one channel fails its floor: either the
projection does not collapse toward the known regime specifically for the true
answer (D1 fails), or the margin does not lengthen for the true answer over
the placebo (D2 fails). Criterion (d) is not earned at the qwen mid-band
operating point, and evidence-responsiveness does not license the mentalistic
name for c_hat even though (a) through (c) hold. A single-channel pass is
reported as a channel dissociation, not rounded to earned or not-earned.

## Gates

See `gates.yaml` (pinned at sign). Integrity: SC0 provenance/staging with the
pre-committed 308-row eligibility list and distractor mapping plus the
single-regime attestation; SC1 dose readback (M1's amended rule) and mandatory
GPU preflight; SC2 blinded channel-2 calibration with CG1 floors and the 0.05
disagreement gate; SC3 coverage plus the 400/308/360 partition audit.
Criterion: D1 (both legs) AND D2 for (d) earned; either failing is
not-earned; a single-channel pass is a reported dissociation. Construct: C1
known-control specificity and the single-regime requirement; on_failure
instrument void, reported straight.

## Predictions scoreboard

Registered 2026-07-17 at sign, after design-info disclosure (baseline gap
3.0005 vs 1.0521, collapse floor 0.5 x gap = 0.9742, margin floor 0.056,
shown to both predictors before calls).

| Predictor | Slot 1: criterion (d) earned? | Slot 2: which channel is stronger |
|-----------|-------------------------------|-----------------------------------|
| orchestrator | EARNED (both channels pass) | projection |
| user | SPLIT (projection collapses, margin does not) | projection |

The predictors DIFFER on Slot 1 (the differentiating value M1b lacked): the
orchestrator expects the in-context true answer to both collapse the readout
and let rows survive their old tipping dose (the answer gives the model
something to hold onto against the push), earning (d); the PI expects a
channel dissociation where the readout updates to the evidence but the
steering margin, a property of the boundary geometry, does not move. Both
agree the projection channel responds more strongly (Slot 2). The PI's
authorization was conditional on the red-team finding nothing
prediction-changing; it found none (the anchor and baseline-gate fixes tighten
the projection test without changing what "split vs earned" means).

## Outcome

Filled at resolve. Record the verdict, the gate results, and the one-sentence
summary that also goes into `verdict:` in the manifest.
