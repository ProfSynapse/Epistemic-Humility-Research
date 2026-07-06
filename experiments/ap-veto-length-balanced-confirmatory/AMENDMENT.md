# ap-veto-length-balanced-confirmatory

Status: draft (not signed; do not launch as confirmatory evidence). Tier-2
confirmatory follow-up to Amendment AM. Never pooled with the locked Phase 1
matrix or the PR #205 published veto operating characteristics.

Machine state lives in `experiment.yaml`; it is not duplicated here.

## Motivation and posture

Amendment AM asked whether a post-generation correctness veto (the post-L20
S/W/U content-trust dial) catches the residual confabulations the pre-generation
radial controller leaves standing. Its gates passed as literally worded (OOF
veto AUROC 0.9168, permutation p=0.001), but an adversarial audit before
recording found the separation is dominated by an UNDISCLOSED answer-length
confound and is therefore not the content signal the gates were meant to
license (AM outcome section 9):

- The residual confabs are long rambles (answer-token median 94, 47% truncated
  at the 96-token cap) and the good class is short facts (median 24). The two
  are nearly length-disjoint.
- The veto reads the hidden state at `content_end`, whose position encodes
  answer length. Answer length ALONE separates residual-vs-good at AUROC 0.943,
  HIGHER than the veto's 0.917 (corr 0.645).
- A genuine non-length content signal does appear in the broader
  hallucination-vs-good population when length is matched (veto ~0.77 at the
  [17,30]-token band where length-only is ~0.57), but AM could not decouple the
  two on its all-long residual set.

AM's own outcome names the required fix: "a follow-up would need a
length-balanced residual/good construction." This is that follow-up. It exists
to promote (or retract) the ~0.77 length-matched content signal from a
single-seed, same-data descriptive estimate to a pre-registered result on a
fresh generation. It is confirmatory of the content-vs-length question
specifically, not a multi-seed generalization claim.

## Design

Substrate: the SAME raw-base checkpoint and AH-baseline generation surface as
AM (greedy decode, same system prompt and grader), pinned from AM's config at
`exp sign`. Modal, cost-capped, single fresh seed. Two changes from AM, both
aimed at defeating the length/truncation artifact:

1. **Extended token budget.** Regenerate with `max_new_tokens = 192` (up from
   AM's 96) so the 47% of confabs that truncated at the cap now complete, and
   `content_end` reflects the natural answer end rather than the decode-length
   ceiling. The harness reports the residual truncation rate in the matched
   set; a truncation rate above 10% is flagged as a caveat on the read.

2. **Length-balanced construction.** Screen the BROADER hallucination-vs-good
   population, not AM's 43-row all-long residual (which has no length overlap
   and cannot be balanced post hoc). Hallucination = answered-and-incorrect
   rows; good = correct-answerable rows, on the fresh generation. Build the test
   set by 1:1 nearest-neighbour caliper matching on answer token length (caliper
   +/- 3 tokens; unmatched rows dropped), so within the matched set the two
   classes have overlapping, near-identical length distributions.

Readout: refit the correctness veto OUT-OF-FOLD on the matched set's post-L20
`content_end` hidden states, using the identical pipeline AM used (5-fold,
PCA -> scaler -> logistic regression fit inside each fold; no feature carried
from the pool). Report the OOF veto AUROC.

Primary contrast: the veto AUROC against an answer-length-only AUROC computed on
the SAME matched set. The length-only baseline is the falsification anchor: the
whole claim is that the veto adds content signal OVER length.

Fresh generation seed distinct from AM's 20260705, pinned at `exp sign`.

## Prediction

On the length-matched, extended-token construction, the refit veto retains a
genuine content signal (OOF AUROC ~0.72 to 0.80) that beats the length-only
baseline (~0.50 to 0.58) by a margin whose bootstrap 95% CI excludes 0,
confirming AM's ~0.77 length-matched estimate as a real content signal rather
than a length/truncation artifact.

## Falsifier

On the length-neutralized matched set (AP-G0 passing), if the OOF veto AUROC
falls below 0.68, OR the veto-minus-length margin's bootstrap 95% CI includes 0,
then AM's separation was length/truncation-driven with no genuine content signal
on the raw base, and the two-signal-coverage backstop claim is retracted rather
than promoted. If AP-G0 fails (matching did not neutralize length), the run is
void and no content verdict is drawn.

## Gates

Locked at `exp sign`; derived from AM section 9's exploratory estimates (veto
~0.77, length-only ~0.57, matched), floored below those points to absorb
fresh-seed and matching-loss variance.

- **AP-G0 (length neutralized, precondition):** on the length-matched set, the
  answer-length-only AUROC is <= 0.60. If it exceeds 0.60 the caliper match did
  not remove the confound and the run is VOID (no content claim drawn). This
  gate validates the instrument before any content read.
- **AP-G1 (content signal exists):** OOF veto AUROC >= 0.68 on the matched set,
  with bootstrap 95% CI lower bound > 0.60 (1000 resamples, seed pinned at
  sign). The floor sits below the 0.77 exploratory point and above the G0
  length ceiling.
- **AP-G2 (content beats length, the crux):** the paired margin
  (veto AUROC minus length-only AUROC) on the matched set has a bootstrap 95% CI
  excluding 0 AND a point estimate >= +0.10.

All three must hold for the content signal to be confirmed. AP-G2 is the
operative bet; AP-G0 is a precondition and AP-G1 a floor.

## Predictions scoreboard

| Predictor | Call |
|-----------|------|
| orchestrator | AP-G0 PASS; AP-G1 PASS (~72%, content signal real but modest); AP-G2 PASS but the tight bet (~65%) |
| user | AP-G1 PASS and AP-G2 PASS at full confidence (real content signal; AM's ~0.77 survives length-balancing). Recorded 2026-07-06 before sign. |

Modal cost cap pre-registered at $10 (user, 2026-07-06); auto-kill at the cap.

## Outcome

Filled at resolve. Record the verdict, the gate results, the residual
truncation rate in the matched set, and the one-sentence summary that also goes
into `verdict:` in the manifest.
