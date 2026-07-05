---
amendment: AL
slug: radial-anti-propensity-steering
status: SIGNED 2026-07-05 (user recorded predictions and answered "Sign and
  launch"; local GPU runs authorized, no cloud spend); gates in section 4
  LOCKED as drafted; control-law choice (ungated primary + gated secondary)
  approved by the user 2026-07-05 from the ceiling-table comparison
question: >-
  Does pushing against the confabulation-propensity direction at generation
  time causally convert residual confabulations into refusals on the AI-TRUE
  checkpoint, at the low collateral the ceiling simulations predict, or is
  the propensity readout one more correlate that does not actuate?
predictions:
  orchestrator:
    calls:
      AL-G1: PASS (~75%)
      AL-G2: PASS (~45%)
      AL-G3: PASS (~50%)
    recorded: 2026-07-05
    basis: >-
      The scope check says the direction is anti-aligned with the
      answer-vs-refuse axis, so collateral should stay low even if the push
      does nothing useful (G1 easy). Actuation is the real bet: five
      use-the-signal channels failed, but those asked the model to CONSULT
      its readout; direct activation injection has better precedent (AG
      muzzle +34pt moved behavior through the caution axis, AC external
      coupling +8.7pt). Against that, the propensity direction is
      caution-residualized by construction, so its behavioral lever is
      unproven and the sim kill models assume what G2 tests.
  user:
    calls:
      AL-G1: PASS
      AL-G2: PASS
      AL-G3: PASS
    recorded: 2026-07-05
    quote: >-
      All three gates called PASS at signing ("Sign and launch"), followed
      by "LETS BE BOLD!" - the user takes the actuation bet at full
      confidence where the orchestrator sits at 45-50% on G2/G3.
outcome: null
scoreboard: pending
---

# Amendment AL — Radial anti-propensity steering on the AI-TRUE checkpoint

**Status:** DRAFT (this file signs when the user records a prediction and
says proceed; gates in section 4 lock at signing).
**Tier:** A (new evidence cell; causal intervention; gates pre-stated).
**Branch:** `amendment-al-radial-steering` (this branch; one amendment, one
branch, one PR).
**Depends on:** AI (provides the TRUE checkpoint and the pivot decision),
the session-0038 AL-prep instruments (doubt-axis check, radial ceiling sims
gated/mean-diff/ungated, familiarity-vs-knowing, propensity scope check),
and the session-0037 commitment-signal line (AK prep) that the scope check
renamed confabulation propensity.
**Relation to AK:** AK (signed, not launched) reads the commitment point
along the answer window; AL writes against the propensity direction at the
pre-generation anchor onward. AL does not consume AK and neither blocks the
other scientifically, but both need the local GPU; AL runs first per the
user's pivot directive.

## 1. Motivation and strategic position

The AI-TRUE checkpoint retains 116 residual confabulations on the 1,662-row
A0 surface (90 correct, 1,222 refused). Session-0038 prep established, at
simulation level: (a) the residual confabs form a compact region (the confab
cloud) that reads boundary-elevated without any actually-knowing signal;
(b) every answer-protecting gate shelters that region rather than carving it
out (gate permutation p=1.0, robust to gate construction); (c) the only
channel with statistically real reach is the anti-propensity push
(permutation p=0.005 at every operating point); and (d) the propensity
direction is confabulation-specific, not generic answer commitment (cosine
-0.35 against the answer-vs-refuse direction, chance transfer at matched
caution). All of that is readout-plus-simulation evidence. The kill models
(oracle, Bernoulli half-effect) assume the push works. This amendment is the
causal test of that assumption.

If it passes, the program has its first write-side win on a fabrication
control axis, and the escalation ladder (multi-seed replication, then a
propensity-penalty training channel per the probe-as-reward pattern) opens.
If it fails, the propensity direction joins the correlate pile and the
steering line needs a different handle; that is a publishable boundary
either way (the sixth use-the-signal null, first in the injection channel).

## 2. Hypotheses

- H-actuate: the propensity projection is causally upstream of the
  fabricate-vs-refuse choice, so subtracting the direction from the hidden
  state at generation time converts pushed confabs into refusals at or above
  the half-effect rate the ceiling sim priced.
- H-specific: the effect runs through the direction and the row selection,
  so a permuted-assignment control (same number of rows pushed, same alpha,
  same direction, shuffled row choice) kills materially fewer confabs.
- H-cheap: because the direction is anti-aligned with the answer axis,
  collateral on correct answers stays within the simulated envelope.

## 3. Design

### 3.1 Surface and baseline

The existing session-0038 TRUE A0 surface is the baseline arm (1,662 rows,
graded: 90 correct / 120 wrong / 114 answerable-refused / 1,222
unanswerable-refused / 116 confabs). No regeneration of the baseline; the
steered arms regenerate the SAME 1,662 questions with the same generation
config and grader as the AL-prep A0 cell.

### 3.2 Frozen readouts and steering direction

- Caution score c: L35 logistic on refused-vs-not, fit on the full baseline
  surface, frozen.
- Propensity score: L24 PCA-128 (randomized, seed 20260705), standardized,
  caution-residualized, mean-diff confab-vs-unanswerable-refused, fit on the
  full baseline surface, frozen; z-scaled by the baseline distribution.
  (The ceiling sims used OOF projections; the deployed law needs one frozen
  direction. Instrument note: full-sample refits of these cells shift AUROC
  by well under 0.01 in prior refits, and the thresholds are z-scores on the
  same population, so the sim thresholds transfer.)
- Steering direction d_raw: the raw-2560-dim preimage of the PCA-space
  propensity direction (inverse-transform through the scaler and PCA
  components), unit-normalized in raw space. The push SUBTRACTS alpha *
  d_raw from the residual stream at layer 24, every position from the
  pre-generation anchor onward, for selected rows only.
- Alpha (single pre-registered value): the raw-space projection gap between
  the confab mean and the unanswerable-refused mean along d_raw, i.e. the
  push that moves an average confab's propensity reading onto the refused
  population mean. A descriptive dose ladder {0.5x, 2x} runs on the pushed
  rows only (section 6, gate-free).

### 3.3 Arms

1. PRIMARY (ungated balanced law): rows with baseline propensity z-score
   above 1.5484 are pushed (98 rows at baseline: 30 confabs, 64 honest
   refusals, 1 correct, 3 wrong). Everything else generates untouched.
2. CONTROL (permuted assignment): identical alpha, direction, and pushed-row
   COUNT, but the pushed set is drawn uniformly at random from all 1,662
   rows (seeded, one draw, recorded). This is the causal analog of the
   ceiling sim's p=0.005 permutation null.
3. SECONDARY (exploratory, gated-logistic balanced law): the gated sim's
   balanced operating point (gate threshold -2.742, push threshold from the
   gated findings), run identically and reported separately, never pooled
   with the primary claim. Motivated by its higher simulated reach (46/116
   oracle vs 30/116 ungated).

All arms are local GPU generation sweeps on the same seed and config; the
read pass (batch-1 pre-generation forwards to score c and propensity) is
shared across arms.

## 4. Gates (LOCK at signing)

Aim-small derivation from the ungated ceiling table (balanced point,
half-effect mean 15.2 kills CI [8, 23]; permuted-assignment expectation
about 3 to 4 kills at half effect):

- AL-G1 (collateral, honesty floor): at most 3 of the 90 baseline-correct
  rows flip to refusal in the primary arm. (Correct-to-wrong flips are
  tracked descriptively and do not gate.)
- AL-G2 (reach): at least 5 of the 116 baseline confabs are killed in the
  primary arm (killed = the row no longer produces a graded confabulation;
  refusal or hedge both count; a confab that becomes a different confab does
  not).
- AL-G3 (specificity): primary-arm kills minus control-arm kills is at
  least 5, with a 1,000-resample row bootstrap CI excluding zero.

FALSIFIER: AL-G2 or AL-G3 failing means the propensity direction does not
actuate fabrication at this operating point; the result is recorded as a
use-the-signal null for the injection channel and no goalposts move. AL-G1
failing with G2/G3 passing means the channel works but the law is too blunt;
that is a PARTIAL outcome, claimable only as mechanism-not-deployable.

## 5. Preconditions and approvals

1. User sign-off on this document and a recorded user prediction
   (dual-prediction practice; scoreboard docs/prediction-scoreboard.md).
2. Local GPU free (lms.exe unload --all if LM Studio holds it).
3. No cloud spend; everything local. The RunPod parity cell (r5) is
   independent infra validation and does not gate AL.
4. Grader identical to the AL-prep A0 cell; grading config byte-pinned.

## 6. Instrumentation (descriptive, gate-free)

- Dose ladder {0.5x, 2x} on the pushed rows of the primary arm.
- Flavor breakdown of kills and leaks (the gated sim predicted leak
  concentration in ambiguous rows).
- Post-push propensity re-read on pushed rows (did the projection actually
  move by the commanded amount; separates actuation failure from
  injection failure).
- Wrong-answer conversions (the ungated sim prices 3 at balanced; a benefit,
  not gated).
- Secondary-arm (gated law) full table for the follow-up design.
- Map-territory exhaust: per-row provenance (scores, thresholds, arm,
  pushed flag, grade before/after) packaged for publication with approval.

## 7. Interpretive caveats (pre-stated)

- Single checkpoint, single seed; a pass licenses a mechanism claim on this
  checkpoint only, with multi-seed replication required before any headline.
- The propensity direction needs refit per checkpoint (reference axes
  transferred at cosine 0.17 in the doubt-axis check); portability is a
  separate question from actuation.
- The alpha calibration assumes linear dose-response along the direction;
  the dose ladder bounds this descriptively.
- Baseline grades come from one grading pass; regeneration noise on
  unpushed rows is absorbed by comparing arms on the same grader, and the
  control arm shares any regeneration drift.
