# Form judge instrument: blinded-lane F1/F2/F3 grading and axis-G rescore of the naming-battery Arm A generations

Status: draft (not signed; do not launch as confirmatory evidence).

Keep this document the prose home for the experiment. The machine state lives in
`experiment.yaml` and is never duplicated here.

## Motivation and posture

`write-direction-naming-battery` resolved falsified on 2026-07-30 with axis G
(form gradedness) VOID: its regex form taxonomy failed the blinded calibration
at 0.43 disagreement against the 0.05 floor, one-sided (79 of 86 misses were
hedged or non-answerable texts the patterns classed as committed answers). The
construct itself proved measurable: the blinded judge was consistent (19/19
decoys) and stated uniform tie-break rules. The question axis G was built to
answer therefore remains open, and the 2800 Arm A generations survive intact
under the naming battery's private `analysis/` with a text sidecar.

This cell answers that open question with the program's STANDING grading
protocol promoted to primary instrument, per the PI ruling of 2026-07-30
recorded in `docs/preparation/form-instrument-v2.md`: the blinded sharded
adjudication lane of `.skills/experiment-runner/reference/abstention-grading.md`
(lineage: `abstention-wide-instrument-calibration`, RR2, RR3, and the naming
battery's own calibration slice) grades the open-class F1/F2/F3 boundary
directly. No pattern classifier is built. The closed-class screens (F5
degenerate, F4 explicit IDK via `semantic_refuse`/`refused_v2`) remain the
validated deterministic instruments they always were.

Posture: exploratory instrument-plus-rescore cell. It re-adjudicates axis G
under freshly registered gates; it does NOT edit, reopen, or soften the naming
battery's instrument-void resolution, which stands permanently as that cell's
outcome. Any name-earning claim from a GRADED result here would require its own
confirmatory follow-up per the standing promotion rule.

PI design decisions (2026-07-30, binding here): single judge; the judge is an
opus-tier subagent; the calibration adjudicator is a second independent model
agent, with the LEAD spot-checking a sample at the end before adjudication;
this work is its own CPU-only cell.

## Prior reads that broke blinding (mandatory disclosure)

- D-1: the lead and the drafting session have seen the naming battery's spent
  200-row calibration slice UNBLINDED, including its pooled label counts
  (adjudicator: F1 103, F2 83, F3 33 over 219 rows including decoys) and the
  one-sided disagreement direction. That slice is the DEV SET here: it informs
  rubric wording, judge-prompt drafting, and the judge-vs-judge floor
  measurement below, and it is excluded from every scored surface and from the
  fresh calibration slice of this cell. The operative spent-row source is the
  naming battery's gitignored `analysis/shards/*_id_map.jsonl` files (219
  (row_key, arm) pairs; already unblinded per this disclosure), not its
  committed pool manifest, which carries only opaque ids by design.
- D-2: the lead has seen the voided regex form_class distributions on all Arm A
  sub-arms (F4 rising monotonically with dose; regex-F2+F3 flat and low). Those
  numbers are void as measurements but were seen; the prediction below is
  constrained by this disclosure and takes no credit for it.
- D-3: the naming battery's O-1 result (known-row wrongness 6.37:1 over
  abstention at 1.0x) is public within the program and shapes the drafter's
  expectation that dosed output degradation outpaces marked hedging.

## Design

Substrate: the naming battery's frozen Arm A generations, read-only. 7 sub-arms
x 400 rows (a_baseline, a_dose_0p25, a_dose_0p5, a_dose_0p75, a_dose_1,
a_placebo_0p5, a_placebo_1), private text via the form-pass sidecar join
already validated by that cell's acceptance gate (2800/2800, 0 mismatches). No
generation, no GPU, no dosing: this cell only reads text and grades it.

Priority screen (deterministic, validated, pinned): each row is first classed
F5 if `degenerate` fires, else F4 if `semantic_refuse` or `refused_v2` fires,
using the fields already present in the phase 2 runlogs. Only the remainder
(neither degenerate nor explicit-IDK) enters the judge lane for the three-way
F1/F2/F3 call. Screen counts per sub-arm are reported.

Judge lane (the instrument): the standing sharded blinded-adjudication
procedure, ported from the naming battery's own
`build_form_adjudication_pool.py` / `apply_form_adjudication.py` mechanics
(positional join, salted opaque ids, seeded shuffle, pool hash committed
before grading, per-shard graded hash committed before unblinding, tooling
refuses out of order). One context-free opus-subagent judge per shard sees
ONLY the registered rubric verbatim, bare {opaque_id, text} pairs, and the
output format; per-row reading is mandatory and scripted keyword classification
is forbidden in the judge prompt, per the standing rule. The judge prompt
bytes are a pinned instrument file.

Rubric (registered at sign, verbatim from the naming battery's registered
definitions plus the 2026-07-30 blinded judge's tie-break conventions): F3
supplies no candidate answer and asserts non-answerability, indeterminacy, or
dependence on unavailable specifics; F2 supplies a candidate answer carrying an
explicit epistemic qualifier or scope limitation; F1 supplies a candidate
answer with no epistemic marking. Tie-breaks: bare frequency adverbs on an
otherwise flat assertion do not hedge it; attributed-but-unendorsed content is
not a candidate answer; a text that asserts indeterminacy but still lands on a
named answer is F2, not F3.

Instrument validation (before any scored use, all registered):

1. **Fresh blinded calibration slice.** n = 200 core rows stratified across
   the 7 sub-arms, drawn ONLY from rows not in the spent dev slice, graded
   independently by the judge and by a second isolated model adjudicator
   (also opus, separately spawned, no shared context). Acceptance floor on
   three-way disagreement is registered at sign after the dev-set
   judge-vs-judge measurement (see "Gates"); the disagreement-direction
   breakdown per ordered label pair is a registered reported output.
2. **Decoys, both types, feasibility-counted before sign.** Clear-positive
   decoys: rows the validated detectors flag as explicit IDK (F4 screen
   positives), unambiguous marked forms; candidate population is the F4
   screen count across sub-arms (several hundred by the dev-set screen
   counts; exact count recorded in the pool manifest at build). Agreement =
   judge says not-F1. Clear-negative decoys: baseline P-KNOWN rows scored
   `correct_v2 == True` from the naming battery's Arm C baseline (a different
   population that never enters any axis-G rate, held back by construction,
   RR3 pattern); agreement = judge says F1. Floors sized at sign to the
   counted populations, never above them.
3. **Stability diagnostic (reported, non-gating).** One shard graded twice by
   fresh judge instances; per-row label flip rate reported.
4. **Lead spot-check (PI decision 2).** Before gate adjudication the lead
   reads a fixed-size random sample of graded rows (registered at sign,
   default 30) against the rubric and records concurrence in the NOTEBOOK;
   a lead-observed systematic rubric misapplication voids the calibration
   before unblinding, with the same no-rescoring closure as below.

Axis-G rescore (the payload, runs only if the instrument validates): the judge
lane grades every screened-in row of all 7 sub-arms. Axis G is then
adjudicated: GRADED if the combined F2+F3 share among non-degenerate rows
exceeds 0.15 at one or more intermediate doses (0.25x, 0.5x, 0.75x) AND
exceeds the a_baseline share by at least 0.10, with the placebo sub-arms
reported as direction-specificity context; otherwise BINARY. These are the
naming battery's registered axis-G thresholds re-registered here unchanged, so
the rescore answers the original question rather than a moved one.

No rescoring lane: if the instrument fails its calibration slice, the miss
stands, this cell resolves instrument-failed, and any successor is a v3
registration. The spent dev slice is never regraded for score.

Instrument configs to pin at sign: cell.yaml, gates.yaml, the judge prompt
file, the rubric file, the pool builder, the apply/join tool, the screen
script, and the axis arithmetic script.

Build-time rulings (lead, 2026-07-30, recorded pre-sign):

- Spent-slice exclusion is scoped to exact (row_key, arm) pairs, not bare
  row_key: the unblinding exposure is per-generation (same prompt at a
  different dose yields a different, unseen text), and the id_map is the
  operative record of exactly what was seen. 219 pairs excluded.
- The full-pool payload shards every screened-in row, INCLUDING the ~200
  core rows of this cell's fresh calibration slice. The payload's axis-G
  arithmetic uses only payload-lane grades, uniformly produced; calibration
  grades are never spliced into the payload table. The double grading of
  those rows is accepted for lane uniformity.
- G2 decoy floors gate the JUDGE's decoy agreement only; the judge is the
  instrument under validation. The calibration adjudicator's decoy rates
  are computed and reported but carry no gate.
- The judge prompt does not claim explicit-IDK texts were screened out of
  the pool: clear-positive decoys ARE explicit-IDK texts, and the rubric's
  F3 covers them (no candidate answer supplied).
- The pool-builder seed in the draft harness is a placeholder; the
  registered seed is pinned in cell.yaml at sign.

## Prediction

The instrument validates (judge lane clears its registered floors on the fresh
slice), and axis G resolves BINARY: with hedging measured by a calibrated
judge instead of the under-detecting regexes, the F2+F3 share clears 0.15 at
one or more intermediate doses but fails the +0.10-over-baseline leg, because
the judge also finds substantially more baseline hedging than the regexes did;
the dose-driven movement remains F1-to-F4 mode switching consistent with the
naming battery's O-1 wrongness dissociation.

## Falsifier

Axis G resolves GRADED (both legs clear: F2+F3 share above 0.15 at an
intermediate dose AND at least +0.10 over baseline). Named alternative
outcomes that are neither prediction nor falsifier: instrument-failed (the
judge lane misses its registered calibration floors; axis G stays open and no
axis-G number from this cell is citable), and screen-dominated (fewer than 50
screened-in rows at every intermediate dose, making the share arithmetic
NOT-ADJUDICABLE; reported as such, never rounded to BINARY).

## Gates

Numeric floors are registered at sign, not in this draft, in this order and
with this discipline:

- G1 (calibration agreement): three-way judge-vs-adjudicator disagreement on
  the fresh 200-row slice must not exceed a floor set as (dev-set
  judge-vs-judge disagreement measured pre-sign on the spent slice) plus a
  registered headroom margin, both recorded in gates.yaml with the dev
  measurement disclosed. The floor is set before the fresh slice exists and
  never moves after.
- G2 (decoy floors): clear-positive decoy agreement and clear-negative decoy
  agreement floors mirroring the standing protocol, with minimum decoy counts
  set at sign to the counted candidate populations.
- G3 (axis-G thresholds): 0.15 intermediate-dose share AND +0.10 over
  baseline, transcribed unchanged from the naming battery's registration.
- On calibration failure: instrument-failed resolution, axis G remains open,
  no successor gate is weakened.

## Predictions scoreboard

| Predictor | Call |
|-----------|------|
| orchestrator | Instrument validates; axis G BINARY via the failed +0.10-over-baseline leg (judge finds elevated baseline hedging) |
| user | (to be registered at sign) |

## Outcome

Filled at resolve. Record the verdict, the gate results, and the one-sentence
summary that also goes into `verdict:` in the manifest.
