---
title: 'First-Person Framing Does Not Open the Shut Text Channel, Ambiguous-Leaning-Negative (Amendment AB, Qwen3.5-4B)'
tags:
- kg/paper
- paper
- epistemic-humility
- internal
kg:
  id: paper:internal-ab-first-person-injection
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
- qwen3.5-4b
metrics:
- auroc
provenance: 'Internal amendment (Tier-2, direct follow-up to Amendment AA). Source of truth: experiment/protocol/AMENDMENT-AB-first-person-injection.md, section 7 (Results) and section 8 (Verdict, locked 2026-07-03). Same harness as AA Arm B (run_arm_b.py + cot_inject.py), same model, same frozen pools, same probe directions (gate L14 / dial L16), same sampled decode (temp 0.7, top_p 0.9, seed 20260701). Raw artifacts (gitignored): steering/results/ab-{1,2,3}-*/result.json. Committed aggregates: steering/reports/ab_v1/.'
related:
- '[[first-person-framed-probe-score-injection-does-not-open-text-channel]]'
- '[[trust-axis-injection-does-not-move-answer-abstain-revise-behavior]]'
- '[[high-probe-accuracy-does-not-imply-causal-use]]'
- '[[chain-of-thought-prompting]]'
- '[[linear-probe]]'
- '[[unanswerable-questions]]'
- '[[auroc]]'
relationships:
- type: supports
  target: '[[first-person-framed-probe-score-injection-does-not-open-text-channel]]'
  target_id: mechanism:first-person-framed-probe-score-injection-does-not-open-text-channel
  confidence: high
- type: related_to
  target: '[[trust-axis-injection-does-not-move-answer-abstain-revise-behavior]]'
  target_id: mechanism:trust-axis-injection-does-not-move-answer-abstain-revise-behavior
  confidence: high
- type: related_to
  target: '[[high-probe-accuracy-does-not-imply-causal-use]]'
  target_id: mechanism:high-probe-accuracy-does-not-imply-causal-use
  confidence: medium
- type: uses
  target: '[[chain-of-thought-prompting]]'
  target_id: method:chain-of-thought-prompting
  confidence: high
- type: uses
  target: '[[linear-probe]]'
  target_id: method:linear-probe
  confidence: high
- type: studies
  target: '[[unanswerable-questions]]'
  target_id: term:unanswerable-questions
  confidence: high
- type: measures
  target: '[[auroc]]'
  target_id: metric:auroc
  confidence: high
---

## Summary

Amendment AB asks whether Amendment AA's shut text channel was a framing
artifact: the registered AA note was out-of-distribution telemetry
(`[internal: gate 0.87 -- confident -- known]`); AB replaces it with the
maximum-effect natural-language variant V1, first-person recall-experience
prose that names the probe score as a percent AND states a score-conditional
decision rule (e.g. "I am not confident I have the knowledge needed to answer
this correctly, only about 12% sure. When I am this unsure the right move is
to say I don't know rather than guess."), tested against a within-batch
shuffled-score placebo on the same gate@early and dial@late cells as AA, plus
a new dial@final (think-end, immediately before the answer commits) cell
added by a pre-launch revision. No V1 cell passes its effect gate. The verdict
is AMBIGUOUS-LEANING-NEGATIVE rather than a clean falsifier only because the
gate@early cell shows a small but CI-excluding-zero abstention delta far below
the gate threshold.

## Claims

- Evidence label: pre-registered gate AB-G1 (V1 dial@late, PRIMARY).
  UNMEASURABLE -- instrument invalid: `compute_revised()` falls back to a
  full-text inequality check that a sampled regeneration almost never
  satisfies, so `revised` reads True in 500/500 rows in both arms and the
  metric is 0 by construction with CI [0,0]. Reported per the pre-registered
  UNDERPOWERED convention, excluded from pass/fail. Descriptive decision-level
  flows show the cell flat regardless (wrong->correct 8.1% real vs 8.9%
  placebo; answer->abstain 0 in both arms). This retroactively confirms the
  same saturation affected AA-7/AA-8 (also 500/500), so AA's dial-side nulls
  were made on a dead instrument, though AA's conclusion survives on the
  decision-level flows. (experiment/protocol/AMENDMENT-AB-first-person-injection.md
  sections 7-8.)
- Evidence label: pre-registered gate AB-G1f (V1 dial@final). MISS. Delta
  -2.7 points, 95% CI [-9.8, +4.3] -- includes zero (if anything the real note
  suppresses discrimination, not significant). Valid instrument at this
  position (revised flag has real variance, 470/500 vs 469/500).
- Evidence label: pre-registered gate AB-G2 (V1 gate@early). MISS at effect
  size. Real-vs-placebo unknown-question final abstention +2.0 points,
  95% CI [0.33, 3.85] -- CI excludes zero, but the effect is 5x below the
  required +10-point gate. Known-question answer rate 1.000 real vs 0.997
  placebo (no-regression clause moot given the effect-size miss).
- Evidence label: AB-G3 (decomposition). NOT TRIGGERED -- no V1 cell passed
  an effect gate, so the V2/V3/V4 ladder (isolating voice, percent, and
  decision-rule ingredients) did not run.
- Evidence label: Q-B (injection position). NO READING -- both dial cells
  (late and final) are flat, so the pre-stated clause routes to the Q-A
  falsifier rather than a position reading; descriptively, the commit-point
  position (final) did not rescue the effect (-2.7pt vs approximately 0 at
  late).
- Evidence label: descriptive trajectory readout. At dial@late, the predicted
  real-vs-placebo divergence in the think-text continuation did not appear
  (verification-marker rate 53.4% real vs 51.6% placebo; mean continuation
  length 241 vs 241 characters); only 1.8% of real-arm continuations mention
  any percent at all (placebo 4.8%), i.e. the injected note is largely
  absorbed without acknowledgment.
- Evidence label: overall verdict (section 8, locked). AMBIGUOUS-LEANING-
  NEGATIVE. The strict falsifier wording ("all real-vs-placebo CIs include
  zero") is not met, solely because AB-G2's +2.0-point delta is real; but
  SUCCESS (any of G1/G1f/G2 passing its threshold) is also not met. First-
  person framing with an interpretable percent and an explicit action rule
  does not open the text channel at the registered thresholds; it leaks a
  small (~2 point, ~2-3% verbatim-compliance) trickle on the gate cell and
  nothing on either dial cell. AA's presence-does-not-imply-use conclusion is
  strengthened to cover the strongest natural-language framing tried.
- Caveats: single family (Qwen3.5-4B), single seed pair; the gate@early cell
  inherits AA's near-floor abstention headroom, which is why AB-G1/AB-G1f
  (dial) were designated PRIMARY over AB-G2 (gate). Any promotion of the
  small gate@early effect would require a fresh registered replication at
  adequate power. Exploratory lab-notebook evidence, reported separately from
  and never pooled with the locked headline matrix.

## Relevance to experiment

AB is the direct follow-up to Amendment AA's text-injection arm
([[trust-axis-injection-does-not-move-answer-abstain-revise-behavior]]),
testing whether the strongest available natural-language framing (voice,
interpretable percent, explicit decision rule) rescues the channel AA found
shut. It does not, which strengthens the descriptive case that presence of an
accurate self-report does not imply causal use of it, alongside the general
literature mechanism
[[high-probe-accuracy-does-not-imply-causal-use]]. AB's finding is scoped to
the CoT text-injection write-form only; it says nothing about activation-level
writes, where Amendment AC's doubt-regulated caution coupling
([[doubt-regulated-caution-coupling-actuates-selective-refusal-release]])
stands as the program's write-side win.
