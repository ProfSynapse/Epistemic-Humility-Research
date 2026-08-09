---
title: wrong-answer-cell-power-fix
aliases:
- Wrong-answer cell power fix
- paper-3 internal-vs-stated re-estimation (360 wrong rows)
- M7 comparator power re-estimation
tags:
- kg/experiment
- experiment
- correctness-readout
- calibration
kg:
  id: experiment:wrong-answer-cell-power-fix
  type: experiment
  status: canonical
related:
- '[[internal-paper3--knows-but-doesnt-say]]'
- '[[known-unknown-direction]]'
- '[[selfaware]]'
- '[[auroc]]'
- '[[expected-calibration-error]]'
- '[[calibration]]'
- '[[verbalized-confidence-channel-bottleneck]]'
- '[[known-unknown-axis-does-not-carry-answer-correctness-at-deployment]]'
relationships:
- type: builds_on
  target: '[[internal-paper3--knows-but-doesnt-say]]'
  target_id: paper:internal-paper3
  confidence: high
  evidence:
  - experiments/wrong-answer-cell-power-fix/AMENDMENT.md (section 1, Motivation
    and posture; re-estimates manuscript.md:314, :315-316, :330-331, :336-337,
    :341-348, :1024-1026, the internal-vs-stated numbers that previously rested
    on n=16 wrong-answered rows)
- type: tests
  target: '[[verbalized-confidence-channel-bottleneck]]'
  target_id: mechanism:verbalized-confidence-channel-bottleneck
  confidence: high
  evidence:
  - experiments/wrong-answer-cell-power-fix/AMENDMENT.md (section 3, Prediction;
    section 4, Falsifier; tests whether the internal-vs-emitted calibration
    contrast survives once the wrong-answered population is powered)
- type: supports
  target: '[[known-unknown-axis-does-not-carry-answer-correctness-at-deployment]]'
  target_id: mechanism:known-unknown-axis-does-not-carry-answer-correctness-at-deployment
  confidence: high
  evidence:
  - experiments/wrong-answer-cell-power-fix/experiment.yaml (verdict field)
  - experiments/wrong-answer-cell-power-fix/analysis-committed/real_run_results.md
- type: related_to
  target: '[[known-unknown-direction]]'
  target_id: term:known-unknown-direction
  confidence: high
  evidence:
  - experiments/wrong-answer-cell-power-fix/AMENDMENT.md (section 2.5, the
    axis under test, fold-wise refit rather than cold transport)
- type: related_to
  target: '[[selfaware]]'
  target_id: dataset:selfaware
  confidence: high
  evidence:
  - experiments/wrong-answer-cell-power-fix/AMENDMENT.md (section 2.3, Arm A;
    all 3369 SelfAware rows)
- type: related_to
  target: '[[auroc]]'
  target_id: metric:auroc
  confidence: high
- type: related_to
  target: '[[expected-calibration-error]]'
  target_id: metric:expected-calibration-error
  confidence: high
- type: related_to
  target: '[[calibration]]'
  target_id: term:calibration
  confidence: medium
  evidence:
  - experiments/wrong-answer-cell-power-fix/analysis-committed/real_run_results.md
    (A5-A7, raw and base-rate-reweighted calibration accounting)
---

Registered re-estimation of the internal-versus-stated numbers in paper 3
("Knows but Doesn't Say"), [[internal-paper3--knows-but-doesnt-say]]. The
paper's discrimination and calibration contrast between the internal
known-unknown axis and the model's emitted `response_confidence` traced, on
its correctness half, to one checkpoint carrying only 16 wrong-answered rows
at 95.9 percent correct; this cell finds the wrong answers already exist at
deployment rendering (360 wrong / 420 correct on the primary checkpoint,
verified against the scored rows) and extraction-backfills them rather than
generating new ones, a 24-fold increase in the wrong-cell count with no
change to the rendering surface. Primary arm A is extraction-only over the
existing, already-graded deployment-render generations; a secondary
forced-answer generation arm B was registered but not run (PI decision, not
gating the verdict).

Resolved 2026-08-09 (falsified, PI approved) after an adversarial red-team
pass that independently reproduced every reported number from the
safetensors. Primary falsifier fires as worded: the fold-wise-refit
known-unknown axis at pinned L35 ranks the model's own correct versus wrong
answers at AUROC 0.5597 (CI 0.5185-0.5993), below the registered 0.60 floor
(E1 FAIL), and its gap over the emitted channel is +0.0390 with CI including
0 (E2 FAIL), below the +0.05 floor. All G0 integrity gates pass (render
parity, join integrity, grader parity, data adequacy on both checkpoints).
Detailed in
[[known-unknown-axis-does-not-carry-answer-correctness-at-deployment]].

**Scope, binding for any write-up.** The result overturns
manuscript.md:336-337 at the axis level only. An unregistered, ungated
full-dimension context probe on the same pre-generation vectors reaches
AUROC 0.6769 (grpov2 checkpoint) and 0.6995 (clean-SFT control checkpoint),
so correct-versus-wrong is linearly present in the residual stream; what
fails is that the known-unknown axis specifically does not carry it at
deployment. The M7 comparator drop against the historical frozen-manifest
reading (AUROC 0.649, a different, neutral-prompt render on a 96-percent-
correct population) is power and render-surface confounded and is never
differenced without that caveat.

The calibration half of the contrast is not overturned: the raw
internal-versus-emitted ECE gap survives decisively and widens under power
(A7 raw +0.2373, CI 0.1853-0.2769); the base-rate-reweighted accounting of
the same gap is arithmetically degenerate (reweighting labels to the paper's
0.959 base rate without recalibrating collapses ECE to the distance of the
mean prediction from 0.959) and carries no calibration content against the
raw result. E4 (four-cell ordering) passes under the adjudicated
out-of-fold reading (correct-minus-wrong step 4.85, CI excludes 0); the
clean-SFT control checkpoint shows the same picture (A1 0.5457, both
channels near or below chance).

Predictions scoreboard: the orchestrator's registered call (internal AUROC
0.60-0.72, gap +0.08 to +0.20, calibration contrast widens) was wrong on the
discrimination half and right on the calibration half. Exploratory Tier-2
evidence, single model, single seed, reported separately from and never
pooled with the locked PROTOCOL v0.3 headline matrix; a powered
re-estimation is not itself a confirmatory replication. Source of truth:
`experiments/wrong-answer-cell-power-fix/AMENDMENT.md`,
`experiments/wrong-answer-cell-power-fix/experiment.yaml`,
`experiments/wrong-answer-cell-power-fix/NOTEBOOK.md`, resolved 2026-08-09.
