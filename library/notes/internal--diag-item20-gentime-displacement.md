---
title: 'Generation-Time Displacement Geometry: The Trajectory Loads Off the Epistemic Plane on Confabulating Rows (diagnostics item 20)'
tags:
- kg/paper
- paper
- epistemic-humility
- internal
kg:
  id: paper:internal-diag-item20
  type: paper
  status: canonical
year: 2026
area: epistemic-humility
status: lab-notebook
source: internal
source_kind: epistemic-humility-research-program
authors:
- Joseph Rosenbaum (Synaptic Labs)
models:
- qwen3-4b
metrics:
- auroc
provenance: 'Internal lab-notebook diagnostics (item 20). Script experiment/phase1/probe/diag_item20_gentime_decomposition.py (commit 7745cdfe); data staging professorsynapse/eh-al-prep-staging tag diag-item20-gentime-r2; grpo-v2 checkpoint (adapter @8914081d) over the 600-row unknown pool at six generation positions. L35 axes: canonical caution_direction_L35 plus caution_perp_direction_L35 (perp_fraction 0.558) plus a doubt axis reconstructed with the identical construction (sanity: reproduces cos(caution,doubt) = -0.8296 exactly). Analysis artifact experiment/phase1/probe/analysis/diag_item20/. Ungated exploratory evidence, never pooled with the locked headline matrix.'
related:
- '[[generation-time-computation-loads-off-the-epistemic-plane]]'
- '[[answerability-and-correctness-are-orthogonal-readout-axes]]'
- '[[post-generation-veto-is-rederived-not-carried]]'
- '[[pre-generation-commitment-signal-predicts-confabulation]]'
- '[[internal-confab-mechanics--cpu-fleet]]'
- '[[activation-addition]]'
- '[[known-unknown-direction]]'
- '[[unanswerable-questions]]'
- '[[auroc]]'
relationships:
- type: supports
  target: '[[generation-time-computation-loads-off-the-epistemic-plane]]'
  target_id: mechanism:generation-time-computation-loads-off-the-epistemic-plane
  confidence: high
- type: related_to
  target: '[[answerability-and-correctness-are-orthogonal-readout-axes]]'
  target_id: mechanism:answerability-and-correctness-are-orthogonal-readout-axes
  confidence: high
- type: related_to
  target: '[[post-generation-veto-is-rederived-not-carried]]'
  target_id: mechanism:post-generation-veto-is-rederived-not-carried
  confidence: high
- type: related_to
  target: '[[pre-generation-commitment-signal-predicts-confabulation]]'
  target_id: mechanism:pre-generation-commitment-signal-predicts-confabulation
  confidence: medium
- type: related_to
  target: '[[internal-confab-mechanics--cpu-fleet]]'
  target_id: paper:internal-confab-mechanics
  confidence: high
- type: studies
  target: '[[known-unknown-direction]]'
  target_id: term:known-unknown-direction
  confidence: high
- type: studies
  target: '[[unanswerable-questions]]'
  target_id: term:unanswerable-questions
  confidence: high
- type: measures
  target: '[[auroc]]'
  target_id: metric:auroc
  confidence: medium
---

## Summary

Internal lab-notebook diagnostics (item 20) decomposing the generation-time hidden-state
trajectory of a clean-SFT to GRPO-v2 checkpoint against the L35 epistemic axes (doubt,
caution, caution_perp). On confabulating rows the state moves a great deal but almost
none of that movement lands on the readable doubt / caution_perp plane, at every position
from first-visible token through answer-end, with no crystallization at the answer end.
This extends the earlier session-0035 anchor-only observation that priming writes almost
entirely off the readable epistemic axes to the full mid-generation trajectory:
generation-time computation is dominated by content machinery while the epistemic-plane
loading stays small and flat. Caveat: the extractor captures states only on answered rows
over an all-unknown pool, so n=41 and every row is a confabulation, giving no
answered-versus-refused contrast in this capture.

## Claims

- Evidence label: per-position displacement decomposition against the doubt / caution_perp
  plane (n=41 answered rows). Roughly 99 percent of every generation position's
  displacement from the pre-generation anchor lies outside the plane (in-plane fraction
  0.10-0.16, residual fraction 0.986-0.994), even though displacement norms are large
  (370-560): the state moves a lot, just off-plane (script
  diag_item20_gentime_decomposition.py, commit 7745cdfe; staging diag-item20-gentime-r2;
  adapter @8914081d).
- Evidence label: mean-displacement cosine and per-axis variance fraction. The
  mean-displacement absolute cosine stays at or below 0.17 against every axis, per-axis
  variance fraction stays 0.3-2.7 percent at every position, and the delta profile
  oscillates in sign with no monotone growth and no answer-end or think-close
  crystallization (supports
  [[generation-time-computation-loads-off-the-epistemic-plane]]).
- Evidence label: axis-construction sanity check. The reconstructed doubt axis reproduces
  cos(caution, doubt) = -0.8296 exactly and caution_perp is orthogonal to doubt by
  construction (cos 0.0000, perp_fraction 0.558), confirming the decomposition basis
  matches the canonical program axes.
- Caveats: single checkpoint, single seed; answered-only capture over an all-unknown pool
  so n=41 and all rows are confabulations (no answered-versus-refused contrast); readout,
  not causal. Exploratory lab-notebook evidence, reported separately from and never pooled
  with the locked headline matrix.
