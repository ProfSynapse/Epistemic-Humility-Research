# Gate diagnosticity: does a cost/harm gate's denominator ever touch the intervention?

Standing rule: before trusting any cost or harm gate's PASS, decompose its
denominator into rows the intervention actually reached (fired/dosed) versus
rows it never touched (unfired/undosed), and report the fired fraction
alongside the gate verdict. A cost gate computed over an UNCONDITIONAL
denominator (every row of a population, regardless of whether the
intervention fired on it) measures the population's BASELINE properties, not
the intervention's cost, whenever the fired fraction is small. If that
fraction is exactly zero, the gate is vacuous by construction: it cannot fail
no matter how badly the intervention performs, because nothing in the
denominator was ever exposed to it.

This is a property of how the metric is defined relative to a readout gate
(fire = intervention applied to this row), not of any one harness. It applies
to any cost/harm/selectivity gate whose denominator is a population rather
than the subset the readout gate actually dosed: steering-cell cost floors,
mechinterp gate-scoring cells, and any future abstention/harm cap built the
same way.

## The counterintuitive law

A gate built this way gets MORE diagnostic power as the readout gate's
separation gets WORSE, not better. A near-perfect readout gate (very high
AUC between the fired and unfired populations) fires on almost none of the
"should not fire" population, so almost none of that population's rows are
ever genuinely exposed to the intervention — there is nothing for the cost
metric to detect. A weaker, less-separated readout gate fires on more of
that population, which puts more rows into the genuinely-affected subset,
which is exactly what gives the cost metric something to measure. Do not
read a passing cost gate as "the intervention is safe/selective" without
first checking where the family/layer/cell sits on this axis — a pass from
a near-perfect readout gate and a pass from a middling one are not
comparable evidence, even though both cleared the identical registered
threshold.

## The arithmetic floor (Wilson-upper caps specifically)

Any registered gate with a Wilson-95%-upper-CI cap is unsatisfiable below a
computable minimum denominator N, independent of how well the intervention
performs — even a perfect 0-success draw can fail the cap if N is too small.
Compute the floor for a given cap by finding the smallest N for which
`wilson_ci(0, N).upper < cap`; do not assume any particular N is safe without
checking. (Illustrative instance, not a universal constant: for the common
cap `Wilson-upper < 0.10`, the floor is N=35 — at N=34 a perfect 0/34 draw
still has Wilson-upper > 0.10.) A gate whose registered denominator can fall
below this floor needs either a stated minimum-N precondition or an explicit
NOT-ADJUDICABLE disposition for cells that miss it (see below) — a miss
below the floor is an artifact of N, not evidence about the intervention.

## Illustrative instance (numbers, marked as example only)

A cost gate defined as `not_well_formed_correct` over the FULL known-correct
population (not filtered by whether the readout gate fired) can pass with
100% of its denominator undosed: e.g. a held-out population of 334
known-correct rows in which the readout gate fired on 0 of them still
produces a valid, gate-passing point estimate and Wilson CI — one entirely
attributable to baseline malformedness that existed before any intervention
ran. Working the arithmetic the other way: at that same N, the largest total
success count that still clears a `<=0.05` point cap plus `<0.10` Wilson-upper
cap is ~16; if the readout gate's own false-positive rate on its fit pool
implies an expected ~3 genuinely-dosed rows at that scale, then even a 100%
failure rate on every one of those ~3 rows is still swallowed by the cap.
Applying a weaker readout gate's fire rate (roughly 9% instead of <1%) to the
same N would put ~30 rows into the dosed subset instead of ~3, and the
minimum dosed-failure rate needed to flip the gate to FAIL drops to roughly
40%, a real, checkable threshold instead of an unreachable one. Same
registered gate, same cap, wildly different diagnostic power, purely as a
function of fire rate.

## Design prescription for a FUTURE non-vacuous gate

Not a retroactive change to any locked/registered gate — a locked gate's PASS
stands exactly as registered even when it is later shown to be
non-diagnostic; that caveat travels forward with the result, it does not
reopen the verdict. For a NEW pre-registration, prefer:

1. **Dosed-rows-only denominator.** Define the cost metric over
   `[row for row in population if row.fired]`, not the full population. This
   is what a "cost of the intervention" claim actually needs to measure.
2. **A fire-rate/N floor for adjudicability.** State a minimum genuinely-dosed
   N (derived from the registered Wilson-upper cap per the arithmetic-floor
   method above, not copied from a different gate's cap) below which the
   gate cannot be evaluated at all.
3. **A NOT-ADJUDICABLE disposition, distinct from PASS.** For any
   family/layer/cell whose readout gate is too well-separated to produce
   enough genuinely-dosed rows to clear the floor, the cost gate reports
   NOT-ADJUDICABLE, not PASS. This is the disposition that actually matters:
   without it, a vacuous pass is indistinguishable from a real one in the
   scoreboard, and a well-separated readout gate gets silently rewarded with
   an unfalsifiable cost claim.

## Checkable habit (apply before trusting any gate result, not only at design time)

Before accepting a cost/harm gate's PASS as evidence:

1. Split the gate's denominator into fired vs unfired rows.
2. Report the fired fraction next to the gate's point estimate and CI.
3. If the fired fraction is 0, say so explicitly and do not read the PASS as
   evidence about the intervention's cost — it is evidence about the
   population's baseline only.
4. If the fired fraction is small but nonzero, run the arithmetic-floor and
   max-tolerable-cost computation above before treating the PASS as having
   caught anything.

## Review checklist (pre-sign, for any new cost/harm gate)

- Denominator defined as dosed-rows-only, OR an explicit justification for
  why the unconditional population is the intended measurement target (rare
  — most "cost of dosing" claims want the dosed subset).
- Minimum-N floor computed from the registered Wilson-upper cap via the
  smallest-N-where-0-successes-clears-the-cap method, not assumed or copied.
- A NOT-ADJUDICABLE disposition registered for cells that miss the floor,
  distinct from PASS and from FAIL.
- Fire rate (fired/total) reported as a companion number to the gate's point
  estimate and CI in every scored output, not only recoverable by forensic
  reconstruction after the fact.
