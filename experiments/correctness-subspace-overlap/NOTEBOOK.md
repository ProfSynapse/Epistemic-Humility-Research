# correctness-subspace-overlap notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

- 2026-07-20: Scaffolded from the v2 design packet (lead-adjudicated,
  `subspace_designer_final.md`). The packet's changelog records three
  required statistical fixes over v1, all adopted here:
  - Reliability moved from in-bootstrap pairwise overlap (upward-biased,
    resamples share about 63 percent of rows) to disjoint half-split
    reliability at fit-sizes m in {n/8, n/4, n/2} with a pinned 1/m
    extrapolation to full n (R^2 >= 0.90, else fall back to the m=n/2
    conservative median).
  - The primary null moved from an isotropic random-subspace draw (too easy
    under activation anisotropy) to a label-permutation null that refits
    the whole bootstrap-SVD pipeline on shuffled labels (P=100), with the
    isotropic draw demoted to a reported secondary baseline.
  - The recovery curve is now bracketed by a chance floor (T restricted to
    a random k-subspace of S) and a ceiling (T restricted to its own top-k
    subspace), and SO-G1(iii) is a relative closed-fraction criterion
    against that floor-to-ceiling gap rather than an absolute AUROC target.

  Lead adjudications recorded: bootstrap-SVD estimator with balanced
  bootstrap adopted as the subspace estimator (deflation kept only as a
  secondary robustness check); gate fixed at k=8 with the full k grid
  {1,2,4,8,16,32} reported; per-stage symmetric PCA basis adopted as
  primary (shared pooled basis kept as secondary robustness); permutation
  null (P=100) adopted as primary, isotropic (N=200) demoted to secondary;
  disjoint-split reliability (R=15, B_rel=30) with pinned 1/m extrapolation
  and R^2 >= 0.90 fallback adopted; recovery floor/ceiling with a >= 0.75
  closed-fraction gate adopted; seeds pinned as primary
  bootstrap/null/permutation 20260720, PCA/fold 20260719 (CD comparability),
  robustness 20260721; position restricted to post-generation only; the
  cross-family scale extension deferred and marked out of scope for this
  packet.
