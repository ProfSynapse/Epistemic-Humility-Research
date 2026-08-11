# correctness-subspace-overlap notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

### 2026-08-11 -- Bookkeeping: AMENDMENT.md header corrected to match machine state

**Tier 3, bookkeeping only, no goalpost implications.** `AMENDMENT.md`'s header claimed a draft/not-signed (or otherwise stale) status that contradicted `experiment.yaml`'s machine state (`status: null-result`), which has read verdict "null-result, instrument-limited" on record. Corrected the AMENDMENT.md header ("Status:" line) to match the machine state. Follows the precedent set by `gemma-4-e4b-family-atlas/AMENDMENT.md`'s 2026-07-20 header correction. No signed content (question, prediction, falsifier, gates, Outcome) touched.

- 2026-07-20 (RUN, KILL FORENSICS, RED-TEAM, RESOLVE null-result): the
  first full launch (12:45 EDT, 8 workers) was killed 57m29s in with no
  traceback and no kernel OOM record; root cause was launching the
  process as a harness-tracked background Bash task, which the agent
  session runtime tore down mid-run. All compute was lost because the
  module writes outputs only at the end. This incident motivated the
  run-persistence safeguard package merged to main the same day (PR #318:
  sign-enforced persistence declarations, kill-resume smoke drill,
  experiments/common/launch_detached.sh). The relaunch ran fully detached
  (setsid/nohup, PID 902777) and exited cleanly: 76.4 min wall, module
  sha unchanged (de6c16fb...), SO-G0 clean, every gate-relevant field
  finite, no anomalies. The lead independently re-derived all SO-G1
  limb numbers, the k-sweep, and the two-seed agreement from the
  committed JSON before adjudication (exact match). Adversarial red-team
  review BEFORE any verdict: six findings, no blockers, sign-off
  conditional on wording. Decisive finding F1: a planted-signal
  simulation using the module's own estimator showed k=8 reliability
  >= 0.70 is unreachable for ANY signal (best planted Rashomon case
  0.104), so Reading A and the falsifier were both instrumentally
  unreachable and the middle ground was the only admissible outcome;
  F2 found the recovery ceiling label-leaky (conservative for the FAIL).
  Resolved null-result (instrument-limited, estimator-structural);
  orchestrator scoreboard call (Reading A) recorded WRONG on every band.
  A6: provenance artifacts staged to the durable exhaust store under
  subspace-overlap-derived/ (3 files, count-verified); per-draw arrays
  are consumed in memory by design and do not exist to stage (wording
  gap vs cell.yaml's exhaust_staging sentence, recorded in the Outcome).

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
