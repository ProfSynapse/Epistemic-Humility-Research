# Margin separation at fine ladder resolution (M1b) notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

- (add dated entries as the experiment progresses)

## 2026-07-17 Pre-sign red-team review of the DRAFT (process upgrade from M1/M2)

An adversarial reviewer examined the unsigned draft (AMENDMENT.md, cell.yaml,
gates.yaml, experiment.yaml, the committed derivation) before PI signature,
specifically hunting the two defect classes that bit M1 (one-rung numerator
prose) and M2 (sign-convention omission). Verdict: SIGN-READY WITH EDITS.

Findings applied before signature (draft-stage fixes, no repin ceremony
needed since nothing was signed):

- BLOCKER B1: the falsifier enumerated only on-rung bounds, but the median
  of 400 rows is the mean of the 200th/201st order statistics (the 19th/20th
  among the 53 refined rows) and can straddle two rungs, producing failing
  bounds like 2.40 outside the enumerated set. The pass/fail surface
  (median <= 7.564912750679985) was always exact; the falsifier and bounds
  list were reworded, and scoreboard slot 2 redefined as a dose band.
- MAJOR: calibration-slice void scope aligned to whole-instrument VOID
  (a fallback to carried M1 values would mechanically reproduce M1's median
  and score detector drift as a substantive FAIL).
- MAJOR: the rejected known-row Option 2 carried an unstated numerator
  hazard (fresh collapse pattern moving the highest pre-collapse rung while
  gate constants stayed frozen); recorded in Decision record item 3, moot
  under the PI-decided Option 1.
- Minors: censored rows carry tipping_idx null (partition on
  tipping_censored first); drift-check and preflight row selection pinned to
  lexicographic row_key order; C1 ceiling stated as a fraction gate (at most
  2 of 53 flagged rows pass); the all-fine-rungs-non-well-formed case named
  and reported descriptively as fine-collapse.

Checked clean by the reviewer (independently verified): every dose and count
to the digit including exact float64 identity of 0.6 x reference with
18.912.../2.5; tipping_idx == 5 selects exactly 53 rows all at the 0.75x
dose in the pinned dataset (the indexing convention the merge rule assumes);
all six sha256 pins byte-match; the derivation script reproduces its report
exactly; no oracle leak or circularity in the conditional design; no M1-class
numerator error present; prose hygiene clean.

Known-row evidence: PI decided Option 1 (reuse M1 1.5x/2.0x runlogs under
RG0) in conversation, 2026-07-17, before signature.
