---
title: correctness-subspace-overlap
aliases:
- 'Correctness discriminative-subspace overlap across training checkpoints'
- SO subspace-overlap cell
- correctness subspace rotation-vs-Rashomon fork
tags:
- kg/experiment
- experiment
- correctness-readout
kg:
  id: experiment:correctness-subspace-overlap
  type: experiment
  status: canonical
related:
- '[[correctness-direction-rotation]]'
- '[[correctness-direction-weakly-identified-defeats-cosine-rotation-probe]]'
- '[[l2-logistic-bootstrap-svd-cannot-resolve-multidim-discriminative-subspace]]'
- '[[principal-subspace-angles]]'
- '[[subspace-identity-rotates-across-seeds-and-checkpoints-despite-stable-probe-performance]]'
- '[[cka-similarity-manipulable-without-functional-change]]'
- '[[per-answer-correctness-linearly-readable-post-generation]]'
- '[[answerability-and-correctness-are-orthogonal-readout-axes]]'
relationships:
- type: builds_on
  target: '[[correctness-direction-rotation]]'
  target_id: experiment:correctness-direction-rotation
  confidence: high
  evidence:
  - experiments/correctness-subspace-overlap/AMENDMENT.md (Motivation and
    posture; the CPU-only successor cell to CD, measuring the top-k
    discriminative subspace where CD measured only a single rank-1 axis)
- type: tests
  target: '[[correctness-direction-weakly-identified-defeats-cosine-rotation-probe]]'
  target_id: mechanism:correctness-direction-weakly-identified-defeats-cosine-rotation-probe
  confidence: high
  evidence:
  - experiments/correctness-subspace-overlap/AMENDMENT.md#outcome (Motivation
    and posture, "The gap this cell targets"; Outcome, "The cell could not
    adjudicate mechanism (a) vs (b)")
- type: supports
  target: '[[l2-logistic-bootstrap-svd-cannot-resolve-multidim-discriminative-subspace]]'
  target_id: mechanism:l2-logistic-bootstrap-svd-cannot-resolve-multidim-discriminative-subspace
  confidence: high
  evidence:
  - experiments/correctness-subspace-overlap/AMENDMENT.md#outcome (Outcome,
    red-team finding on the nature of the limit)
- type: related_to
  target: '[[principal-subspace-angles]]'
  target_id: method:principal-subspace-angles
  confidence: high
  evidence:
  - experiments/correctness-subspace-overlap/AMENDMENT.md (Method, Subspace
    overlap metric; the Grassmann projection metric this cell reports is the
    same principal-angle construction)
- type: related_to
  target: '[[subspace-identity-rotates-across-seeds-and-checkpoints-despite-stable-probe-performance]]'
  target_id: mechanism:subspace-identity-rotates-across-seeds-and-checkpoints-despite-stable-probe-performance
  confidence: medium
  evidence:
  - experiments/correctness-subspace-overlap/AMENDMENT.md (Related work and
    novelty; Subspace Chronicles independently replicates the
    stable-readout-versus-unstable-direction dissociation at pretraining
    scale using principal subspace angles on directly-fit probe weights)
- type: related_to
  target: '[[cka-similarity-manipulable-without-functional-change]]'
  target_id: mechanism:cka-similarity-manipulable-without-functional-change
  confidence: medium
  evidence:
  - experiments/correctness-subspace-overlap/AMENDMENT.md (Related work and
    novelty; the Reliability of CKA analysis paper's similarity-inflation
    regime in high-dimension low-sample settings motivates this cell's
    disjoint-split reliability and label-permutation null design)
- type: related_to
  target: '[[per-answer-correctness-linearly-readable-post-generation]]'
  target_id: mechanism:per-answer-correctness-linearly-readable-post-generation
  confidence: high
  evidence:
  - experiments/correctness-subspace-overlap/AMENDMENT.md (Design, Method;
    probes the same post-generation correctness dial at its native readout
    position)
- type: related_to
  target: '[[answerability-and-correctness-are-orthogonal-readout-axes]]'
  target_id: mechanism:answerability-and-correctness-are-orthogonal-readout-axes
  confidence: medium
  evidence:
  - experiments/correctness-subspace-overlap/AMENDMENT.md (Motivation and
    posture; recasts the CD four-stage timeline in subspace terms against the
    separately-tracked answerability axis)
---

CPU-only Tier-2 probe-fit successor to
[[correctness-direction-rotation]] (CD). CD measured only a rank-1
discriminative axis per checkpoint and found it weakly identified (split-half
cosine floor 0.174), leaving open whether the correctness readout's 0.679
cross-checkpoint cold transfer rides on (a) a stable low-dimensional
discriminative SUBSPACE within which a single fitted axis is an arbitrary,
poorly-reproducible vector (Rashomon-set underdetermination), or (b) a
discriminative subspace that genuinely rotates across checkpoints. This cell
estimates the top-k discriminative subspace (bootstrap-normal SVD, k in
{1,2,4,8,16,32}) and its Grassmann principal-angle overlap across the CD
four-stage timeline and the S (Instruct base) to T (deployed grpov2)
bracket, against a label-permutation null and a disjoint-split within-stage
reliability reference, plus a floor-and-ceiling recovery curve accounting
for the 0.679 transfer.

Resolved 2026-07-20 (null-result, instrument-limited), adjudicated after
adversarial red-team review (six findings, sign-off conditional on wording).
SO-G0 (data adequacy) passed. SO-G1 (subspace-overlap-confirmed) FAILED on
all three limbs at k=8 over L19-L24: (i) S->T overlap 0.01157 versus
permutation-null mean 0.01085 and 95th percentile 0.01419, a margin of
+0.00072 against the required +0.15, inside the null band; (ii) within-stage
full-n reliability S 0.0185 and T 0.0293 versus the required 0.70 (the 1/m
extrapolation R^2 was 0.007-0.226 at every gate layer, so the pre-registered
conservative m=n/2 fallback was used throughout); (iii) recovery closed
fraction 0.1750 versus the required 0.75. SO-G2 (readout sanity) passed
(best-layer full-PCA OOF AUROC 0.809-0.860 inherited from CD; the k=1
recovery point at L20, 0.7009, lands within 0.10 of the documented 0.679
frozen-axis cold transfer as a pipeline sanity check). The falsifier
(Reading B, genuine rotation) did NOT fire: its precondition of within-stage
reliability >= 0.70 was unmet, and the k=1/k=2 overlaps sit above their nulls
so the "indistinguishable at every k" clause also fails. Two pinned seeds
agree the headline call is seed-stable.

Adopted reading: the pre-stated middle ground. Neither Reading A (shared
flat subspace) nor Reading B (genuine rotation) is adopted; the cell could
not adjudicate mechanism (a) versus (b).

A post-hoc red-team diagnosis (labeled as such, no gate retuned) found the
limit is estimator-structural rather than sample-size: a planted-signal
simulation using the cell's own estimator at matched sample size,
dimensionality, and class balance showed k=8 within-stage reliability
>= 0.70 is unreachable for ANY signal, including a perfectly separable
redundant flat 8-dim subspace, the exact mechanism-(a) case the gate was
built to detect (best planted case 0.104; real-data 0.0185-0.0293 sit inside
the range a genuine moderate 8-dim signal would produce, 0.018-0.073). L2-
regularized logistic regression collapses a redundant or flat discriminative
subspace onto one stable weighted normal, so bootstrap-normal SVD directions
beyond the first describe estimator noise regardless of true dimensionality
(detailed in
[[l2-logistic-bootstrap-svd-cannot-resolve-multidim-discriminative-subspace]]).
Because both Reading A and the falsifier required the reliability limb to
pass, both were unreachable before any data were seen, so the falsifier's
non-firing carries no evidential weight.

What the run does establish (label-clean, surviving the estimator limit):
the k=1 S->T overlap is above its permutation null (0.00896 versus 95th
percentile 0.00472, 6.7x the null mean) while k=4 through k=32 sit inside the
null, so the single shared direction underlying the 0.679 transfer is real
and no reproducible shared structure was detected beyond it; and S's
discriminative 8-subspace reads T only about 0.04 AUROC above a random 8-dim
slice of S's own PCA-128 span (recovery 0.742 versus floor 0.701 at L20;
at k=32 recovery 0.766 falls below floor 0.771), so the transferable signal
is diffuse across S's span rather than concentrated in S's top discriminative
directions.

Carried caveats: the recovery ceiling is label-leaky (T's top-k basis is fit
on full T labels before CV scoring, inflating it to 0.885 at k=1 down to
0.864 at k=32 against this run's own full-PCA OOF AUROC of 0.814), which
depresses the closed_fraction and makes limb (iii)'s FAIL conservative
rather than definitive; the two pre-registered subspace estimators
(bootstrap-SVD primary versus deflation) agree only 0.17-0.23 at k=8 across
stages; and the matched-population S->T bracket (334 shared row keys) gives
k=8 overlap 0.0087 against 0.0128 full-population, so the near-null result
is not a population artifact. Exploratory Tier-2 evidence, never pooled with
the locked Phase 1 headline matrix or the S/T headline readings. Source of
truth: `experiments/correctness-subspace-overlap/AMENDMENT.md`, Outcome
section, resolved 2026-07-20.
