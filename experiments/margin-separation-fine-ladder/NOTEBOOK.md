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

## 2026-07-17 RG0 halt, drift diagnostics, and PI-decided resolution (Option 2)

The phase-1 build passed all six sha256 pins and the 181/53/166 partition
audit, then HALTED at the pre-registered rg0_drift_check: fresh 0.75x-rung
generations for the 8 lexicographically-smallest refined rows diverged in
completion TEXT from M1's committed runlog on 3 of 8 rows, while dose readback
passed cleanly (systematic ~0.0157 bf16-scale offset, well inside tolerance).
Per the signed cell.yaml rule the run stopped; no preflight, no full run.

Two integrity diagnostics were run (gitignored artifacts under
analysis/diagnostics/; booleans/lengths/offsets only, no text; no fine rung
generated, no criterion computed):

1. bitflip_53rows: all 53 refined rows regenerated fresh at 0.5x and 0.75x,
   detector bits compared to M1. Detector bits 52/53 (98.1%) identical at each
   rung. Bracket classification preserved on 51/53; 2 breaks, opposite
   directions (kuq_unknowns_all:2108 no longer tips at 0.75x; :901 now tips at
   0.5x). Byte match only 74% (0.5x) / 87% (0.75x). Row 131, the drift-check's
   69->294 char blowup, came back byte-identical to M1 here.

2. batch_sensitivity: the 8 drift rows regenerated at batch_size 1/4/8. Row
   131 is decisive: bs1 refused=False (269 ch), bs4 refused=True (69 ch,
   matches M1), bs8 refused=False (294 ch) -- the tipping bit flips with batch
   size alone. Several rows' text changes across batch sizes. Env: torch
   2.9.0+cu128, CUDA 12.8, RTX 3090; M1 carried no env stamp to diff.

Mechanism: bf16 forward-pass non-determinism driven by batch composition (a
throughput optimization, not a scientific choice). It is stochastic, not a
deterministic environment shift: the same (row, dose) yields different
completions depending only on batch-mates, and for boundary rows the tipping
bit itself flips. Consequently there is no batch-invariant "true" margin for
the median-determining boundary rows; even a deterministic batch_size-1 run
disagrees with M1's batched run on such rows.

PI decision (2026-07-17, in conversation): resolve M1b as a null-result
without a separation verdict rather than rework the design. Rationale: the
~4% per-row bracket noise (comparable to M1's accepted 3.5% non-monotone rate,
C1 ceiling 0.05) is the same order as the sub-rung separation M1b set out to
resolve, and M1b's point-estimate criterion at the 0.6x boundary (median vs
7.564912750679985) is not well-posed when the median sits within the
instrument's own reproducibility noise. Reworking (pinned-batch or bs-1
regeneration of a self-consistent set) could produce one internally
consistent draw but could not make the boundary classification batch-invariant,
so it would not cleanly answer the quantization-vs-real question either.

Scoreboard disposition: no criterion was computed; both predictors' calls
(PASS / marginal-pass band) are UNSCORED. Reported straight.

Finding recorded: qwen mid-band commitment-margin separation is
instrument-resolution-limited at the boundary. M1's Claim 1 falsification
(bound 2.0 vs floor 2.5) stands; the fine-ladder retest establishes that the
miss is neither a clean quantization artifact nor a clean real separation but
sits within the bf16 instrument's own ~4% classification noise.
