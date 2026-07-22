# M4c: evidence-derived doubt direction constructive search notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

- (add dated entries as the experiment progresses)

## 2026-07-18 draft created (pre-sign)

Scaffolded from the lead's design derivation after M4-WK merged (PR #306).
The five design-derivation open questions are resolved in the AMENDMENT
rulings record: rung (b) conditional on a rung-(a) pass (PI ruling
2026-07-18), sequencing next-before-family-memo (PI ruling 2026-07-18),
reference dose 8x sigma_c, 50/50 split at seed 48260728, native-comparator
strong bar lower CI >= -0.05, top-PC as report-only secondary (lead technical
rulings). Pre-sign red-team of this draft is required before PI signature;
predictor scoreboard slots fill at sign.

## 2026-07-18 pre-sign red-team applied

Independent adversarial review of the draft (all 7 assigned attack surfaces):
verdict SIGN WITH FIXES, 0 blockers, 2 majors, 4 minors. Reviewer disk-verified
the capture inventory (3 arms x 1001 rows, roles 400/360/241), the byte-level
direction pins, the native comparator's disjointness from the held-out rows
(M4-WK disjointness_check.json n_intersection=0), and every quoted M4-WK
number. Remediation applied in this commit, all pre-sign (nothing frozen yet):

- M-A: falsifier and outcome table now split below-floor into (a1) CI covers
  0.5 (no content / copying) vs (a2) CI excludes 0.5 from below (reversed
  orientation, lift to PI); mirrored in gates.yaml D_a and the manifest
  falsifier.
- M-B: self-blinding machine-enforced: permutation routine byte-pinned in
  cell.yaml; analysis re-derives the split and recomputes d_ev from raw
  tensors, hard-asserting equality with committed artifacts (SC0 void on
  failure).
- m-1: covariance-shaped null disclosed as conservative; isotropic-null
  percentile added as ungated companion.
- m-2: D_a point estimate gates; CI reported-only.
- m-3: 8x sigma_c reference-dose convention cited to M4-WK's realized values
  (reference_dose_abs 8.46933 = 8 x sigma_c 1.05867 in
  c_hat_worldknown.json), verified by the lead against the committed json.
- m-4: native comparator recomputed on identical held-out rows; 0.86275 is
  the full-population anchor only.

## 2026-07-18 rung (b) ruling and CPU-rung adjudication

Lead verification of the build report: rung-(a) AUROC independently
re-derived from the committed heldout_projections.jsonl (0.725208,
byte-exact); commit order sign -> staging -> split freeze -> fit ->
enforcement -> readouts confirmed from git. Build-agent flagged resolutions
ACCEPTED by the lead: (1) the .gitignore blanket directions/ pattern fix
(M4-WK precedent; the four pinned files untouched and hash-matching); (2)
mu_c/sigma_c for the rung-(b) reference dose computed from the 200 FIT
confab baseline projections only, the sole self-blinding-compatible
population (deviation from M4-WK's fit-confab+correct convention, affects
only the not-run rung-(b) numeric); (3) detector_stack.applicable false in
staging (no grading consumer among the CPU rungs); (4) KUQ comparator
recomputed on held-out rows beyond the letter of m-4 (ungated, symmetric
treatment, no gate touched).

PI ruling (2026-07-18): rung (b) NOT RUN. The pre-registered condition (a
rung-(a) pass) is met, but the PI declines funding: under the signed outcome
table the pass-a-fail-c cap is unchangeable by rung (b), and a J-space-style
expansion of d_ev would require its own future amendment. Recorded as
condition-met-declined, not a gate failure and not a void.
