---
title: correctness-geometry-scale-ladder
aliases:
- Correctness-geometry scale ladder (1.7B->8B->14B)
- crystallization-index scale ladder
tags:
- kg/experiment
- experiment
- correctness-readout
kg:
  id: experiment:correctness-geometry-scale-ladder
  type: experiment
  status: canonical
related:
- '[[correctness-direction-rotation]]'
- '[[correctness-subspace-overlap]]'
- '[[correctness-direction-weakly-identified-defeats-cosine-rotation-probe]]'
- '[[l2-logistic-bootstrap-svd-cannot-resolve-multidim-discriminative-subspace]]'
- '[[correctness-identifiability-sharpens-with-scale-under-adaptive-layer-choice]]'
relationships:
- type: builds_on
  target: '[[correctness-direction-rotation]]'
  target_id: experiment:correctness-direction-rotation
  confidence: high
  evidence:
  - experiments/correctness-geometry-scale-ladder/AMENDMENT.md (Motivation and posture)
- type: builds_on
  target: '[[correctness-subspace-overlap]]'
  target_id: experiment:correctness-subspace-overlap
  confidence: high
  evidence:
  - experiments/correctness-geometry-scale-ladder/AMENDMENT.md (Motivation and posture)
- type: tests
  target: '[[correctness-direction-weakly-identified-defeats-cosine-rotation-probe]]'
  target_id: mechanism:correctness-direction-weakly-identified-defeats-cosine-rotation-probe
  confidence: high
  evidence:
  - experiments/correctness-geometry-scale-ladder/AMENDMENT.md (Motivation and posture,
    "diffuseness is a small-model artifact" hypothesis)
  - experiments/correctness-geometry-scale-ladder/AMENDMENT.md#outcome
- type: related_to
  target: '[[l2-logistic-bootstrap-svd-cannot-resolve-multidim-discriminative-subspace]]'
  target_id: mechanism:l2-logistic-bootstrap-svd-cannot-resolve-multidim-discriminative-subspace
  confidence: high
  evidence:
  - experiments/correctness-geometry-scale-ladder/AMENDMENT.md (Estimators, "FORBIDDEN"
    clause excluding the k>1 bootstrap-SVD estimator by construction, per SO's finding)
- type: supports
  target: '[[correctness-identifiability-sharpens-with-scale-under-adaptive-layer-choice]]'
  target_id: mechanism:correctness-identifiability-sharpens-with-scale-under-adaptive-layer-choice
  confidence: medium
  evidence:
  - experiments/correctness-geometry-scale-ladder/AMENDMENT.md#outcome (G1 resolution
    on the real run)
---

Tier-2 exploratory probe-fit cell (CPU-only, never pooled with the locked
PROTOCOL v0.3 headline matrix) asking whether the per-answer correctness
signal's weak identifiability at Qwen3-4B ([[correctness-direction-rotation]]
[CD]: stable readout AUROC 0.809-0.860 but a within-stage split-half cosine
floor of 0.174; [[correctness-subspace-overlap]] [SO]: only a single k=1
shared axis clears its label-permutation null, with no reproducible
higher-rank structure) is a small-model artifact that crystallizes into a
compact, identifiable geometric object as scale grows, using an
identical-pool ladder of three Amendment-X raw-instruct-base extractions
(unsloth Qwen3 1.7B/8B/14B, matched-n N*=377/377 correct/wrong, PCA-128 per
scale, label-agnostic).

**Instrument history (three pre-outcome iterations, all synthetic-only).**
v1's mean-shift planted-signal generator failed its own validation gate
(G_val) at all four estimators and all three scales, a pre-registration
instrument-iteration loop rather than a resolve-as-null. v2 rebuilt the
generator as a correlated-redundant flat-Rashomon construction and added a
new hard-blocking construction-validity gate, which then failed for a
mathematical reason: its criterion (a), "k=1 must be genuinely insufficient
to decode a planted rank-r signal," is unsatisfiable by any two-class
Gaussian mean-shift construction, because the Bayes-optimal decision
boundary for such a model is always a single linear direction (the LDA
argument, `w` proportional to `Sigma^-1 * mu`). The lead and the cell's
designer concurred this criterion tested the wrong axis against SO's real
committed target (itself nearly k=1-decodable while directionally unstable)
and RETIRED criterion (a) rather than patching it, authorizing a v3 rebuild.
v3 replaced it with a monotone-degradation criterion across a redundancy
ladder plus a derived index-resolution ceiling, designated the split-half
k=1 direction-reliability estimator E1 as PRIMARY (the other three
estimators demoted to descriptive companions never eligible to gate the
headline), and PASSED construction-validity at all three scales, making
G_val actionable. G1's thresholds were then locked from the v3 planted bands
before any real per-row correctness label had been read.

**VOID first real run (instrument-integrity note).** The first launch of the
signed real-label driver was VOID: the pinned build had the synthetic data
path hardwired (an `if True` stub that never called the real-layer cache),
so its output never touched a real correctness label despite running to
completion. The run was quarantined under a `.CONTAMINATED-synthetic`
prefix, root-caused, and fixed with a minimal repin of the driver module
(data-routing only; no gate, threshold, or estimator change) before
relaunch. The resolving run's own contamination check (explained-variance
ratios of 0.87/0.87/0.80 across scales, decreasing with hidden dimension,
the real high-dimensional signature that the 128-dimensional synthetic
generator cannot produce) confirms it read real labels.

**M3 resolution.** The crystallization index `c` (E1 full-n primary,
unclipped, scored against frozen v3 planted bands, z=1.645 one-sided) rises
monotonically under the scale-adaptive best-dial layer choice (the
per-scale layer with highest correct-vs-wrong AUROC: 1.7B L21, 8B L20, 14B
L28): c = -0.062 -> +0.086 -> +0.240, a `Delta_c` of 0.302 that clears both
the frozen-band-only sigma reading (0.254) and the frozen-plus-real-draw
sigma reading (0.288). Under the fixed relative-depth layer choice (~0.6 of
each scale's layer count: 1.7B L17, 8B L22, 14B L24), c does not rise
monotonically: +0.033 -> +0.129 -> +0.075, dipping at 14B. The registered
gate requires both layer choices to show the rise (REQUIRE-BOTH); since they
disagree, PASS is not awarded, and since best-dial's raw rise exceeds every
defensible half-width, FALSIFIED is not triggered either. G1 resolves as the
pre-stated middle ground M3 ("trend present at best-dial, absent at fixed
depth"), chosen over M1 (non-monotonic) because only the fixed_depth arm
tracks a non-monotone shape; best_dial is cleanly monotone, so M3 is the
label that captures the actual cross-layer-choice disagreement.

**Window-scan robustness qualification (descriptive, not a gate surface).**
A +/-3-layer window scan around each scale's best-dial layer shows the
sharpening trend is layer-robust in a stronger sense than the M3 label
alone suggests: per-layer median c runs roughly -0.04 (1.7B) to +0.13 (8B)
to +0.24 (14B), and every layer in the 8B window exceeds every layer in the
1.7B window. The REQUIRE-BOTH conjunction's failure traces to one
anomalously low-c layer in the 14B fixed-depth window, not to the
scale-sharpening trend being generally absent at fixed depth; the gate
verdict stays M3, and the window scan does not upgrade it.

**Selection-provenance disclosure.** The best-dial layers are the same
layers, on the same pool and the same correctness labels, that E1 itself
consumes: a real selection exposure. Checked and found not to bite: at 1.7B
and 8B, best-dial sits among the LOWEST-c layers of its own +/-3 window, so
selecting a layer for correctness AUROC did not cherry-pick for direction
reliability. Two-seed robustness also holds: a second seed's best-dial draws
reproduce the first seed's means within 0.008 at every scale.

**Prediction scoreboard (proposed).** The orchestrator's pre-registered
DIFFUSE-STABLE call (c stays near 0 at every scale) is refuted by best-dial's
Delta_c = 0.240 clearing the trend threshold under both sigma readings and
by the layer-robust window trend. The user's PARTIAL/NON-MONOTONE call (a
rise that stalls or reverses) matches the fixed_depth arm almost verbatim
and correctly rejected both a clean sharpening and a flat diffuse-stable
reading. Source of truth: `experiments/correctness-geometry-scale-ladder/AMENDMENT.md`,
"G1 resolution on the real run" (end of the Outcome section), resolved
2026-07-20.
