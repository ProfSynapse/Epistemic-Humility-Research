---
aliases:
- bootstrap-normal SVD directions beyond the first are estimator noise
- L2-regularized logistic regression collapses redundant subspaces onto one normal
- k>1 subspace-reliability gates are instrumentally unreachable for any signal
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:l2-logistic-bootstrap-svd-cannot-resolve-multidim-discriminative-subspace
  type: mechanism
  status: canonical
cause: "Estimating a rank-k>1 discriminative subspace as the top-k right singular vectors of B=200 balanced-bootstrap L2-regularized logistic-regression (saga) separating normals, then measuring within-stage reliability as the principal-angle overlap between two independent disjoint-split refits of that same estimator, even when the true discriminative structure is a genuinely redundant or flat multi-dimensional subspace."
effect: "Within-stage reliability at k=8 tops out at 0.104 in a planted-signal simulation's best case and cannot reach a 0.70 threshold for any signal, including a perfectly separable redundant flat 8-dim subspace deliberately constructed as the most favorable case for subspace recovery, because L2-regularized logistic regression collapses a redundant or flat discriminative subspace onto a single stable weighted normal: the bootstrap resamples' SVD directions beyond the first right singular vector are estimator noise regardless of the true underlying dimensionality. A subspace-reliability gate built on this estimator at k>1 is therefore instrumentally unreachable before any real data are seen, so it cannot adjudicate a flat/redundant discriminative subspace (Rashomon-set underdetermination) from genuine cross-checkpoint subspace rotation, and a null or low result on such a gate carries no evidential weight about which mechanism holds."
polarity: prevents
related:
- '[[correctness-subspace-overlap]]'
- '[[principal-subspace-angles]]'
- '[[correctness-direction-weakly-identified-defeats-cosine-rotation-probe]]'
- '[[subspace-identity-rotates-across-seeds-and-checkpoints-despite-stable-probe-performance]]'
relationships:
- type: supported_by
  target: '[[correctness-subspace-overlap]]'
  target_id: experiment:correctness-subspace-overlap
  confidence: high
  evidence:
  - experiments/correctness-subspace-overlap/AMENDMENT.md#outcome (Outcome,
    red-team finding on the nature of the limit; planted-signal simulation at
    matched n, dimensionality, and class balance)
- type: related_to
  target: '[[principal-subspace-angles]]'
  target_id: method:principal-subspace-angles
  confidence: high
  evidence:
  - experiments/correctness-subspace-overlap/AMENDMENT.md (Method, Discriminative
    subspace estimator; the bootstrap-SVD estimator this mechanism limits feeds
    the same Grassmann/principal-angle overlap metric)
- type: related_to
  target: '[[correctness-direction-weakly-identified-defeats-cosine-rotation-probe]]'
  target_id: mechanism:correctness-direction-weakly-identified-defeats-cosine-rotation-probe
  confidence: high
  evidence:
  - experiments/correctness-subspace-overlap/AMENDMENT.md#outcome (Outcome;
    this cell was built to resolve whether CD's weak single-axis
    identifiability was a flat k>1 subspace or genuine rotation, and found the
    successor instrument's own reliability limb estimator-structurally
    unreachable instead)
- type: related_to
  target: '[[subspace-identity-rotates-across-seeds-and-checkpoints-despite-stable-probe-performance]]'
  target_id: mechanism:subspace-identity-rotates-across-seeds-and-checkpoints-despite-stable-probe-performance
  confidence: medium
  evidence:
  - experiments/correctness-subspace-overlap/AMENDMENT.md (Related work and
    novelty; contrast case, that mechanism's subspace-rotation finding used a
    different estimator, principal subspace angles on directly-fit probe
    weights rather than a bootstrap-normal SVD, and is not subject to this
    specific structural limit)
---

A planted-signal simulation, built with the correctness-subspace-overlap
cell's own estimator at matched sample size, dimensionality, and class
balance, tested whether the cell's k=8 within-stage reliability gate could
ever pass for a signal it was designed to detect: a genuinely redundant,
perfectly separable flat 8-dimensional discriminative subspace. It could
not. The best planted case reached only 0.104 reliability, far below the
0.70 gate threshold, and the real-data values (0.0185-0.0293) were
indistinguishable from a moderate 8-dim planted signal (0.018-0.073). The
cause is structural to the estimator, not a matter of insufficient sample
size: L2-regularized logistic regression picks out one stable weighted
normal from a redundant or flat discriminative region, so the bootstrap
resamples' fitted normals cluster tightly around that single normal and the
SVD directions beyond the first describe only the estimator's own noise,
never the shape of the true subspace.

**Why it matters here:** it means a subspace-overlap or subspace-reliability
gate built on bootstrap-normal SVD at k>1 cannot do the job it was designed
for. Because both the headline positive reading and the pre-registered
falsifier in [[correctness-subspace-overlap]] required the reliability limb
to clear 0.70, and that limb was shown unreachable for any signal before any
real data were collected, the cell's non-firing falsifier carries no
evidential weight, and the flat-subspace-versus-rotation question the cell
was built to answer stays genuinely open rather than resolved against
either reading.

**Lineage:** diagnosed inside [[correctness-subspace-overlap]], the successor
instrument to [[correctness-direction-weakly-identified-defeats-cosine-rotation-probe]]
built specifically to adjudicate whether that mechanism's weakly-identified
single axis was an arbitrary vector within a stable flat subspace or
evidence of genuine geometric rotation. Contrasts with
[[subspace-identity-rotates-across-seeds-and-checkpoints-despite-stable-probe-performance]],
whose subspace-rotation finding was measured with principal subspace angles
on directly-fit probe weights rather than a bootstrap-normal SVD, and is not
known to share this structural limit. Source of truth:
`experiments/correctness-subspace-overlap/AMENDMENT.md`, Outcome section,
resolved 2026-07-20.
