---
title: 'Causal Confidence Steering Is a Use-the-Signal Null in Both the Activation and Text-Injection Channels (Amendment AA, Qwen3.5-4B)'
tags:
- kg/paper
- paper
- epistemic-humility
- internal
kg:
  id: paper:internal-aa-causal-confidence-steering-null
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
provenance: 'Internal amendment (Tier-2 exploratory evidence line, Paper 5: reading vs. writing the trust axis). Source of truth: experiment/protocol/AMENDMENT-AA-causal-confidence-steering.md (Stage-1 verdict registered 2026-07-02). Pools: SelfAware known/unknown rows (gate cells, shared rows from extraction__55254a04aa1f/rows.jsonl) and PopQA+TriviaQA answerable pool (dial cells). Directions: unit-normed gate probe (L14, AUROC 0.998) and dial probe (L16, AUROC 0.827) fitted 2026-07-01 by persist_probe_direction.py from the Amendment-Z extraction directions. Roll-up: amendment_aa_qwen3.5-4b_result.json (amendment_aa_verdict.py, missing_cells = []).'
related:
- '[[trust-axis-injection-does-not-move-answer-abstain-revise-behavior]]'
- '[[answerability-and-correctness-are-orthogonal-readout-axes]]'
- '[[high-probe-accuracy-does-not-imply-causal-use]]'
- '[[activation-steering]]'
- '[[chain-of-thought-prompting]]'
- '[[linear-probe]]'
- '[[unanswerable-questions]]'
- '[[auroc]]'
relationships:
- type: supports
  target: '[[trust-axis-injection-does-not-move-answer-abstain-revise-behavior]]'
  target_id: mechanism:trust-axis-injection-does-not-move-answer-abstain-revise-behavior
  confidence: high
- type: related_to
  target: '[[answerability-and-correctness-are-orthogonal-readout-axes]]'
  target_id: mechanism:answerability-and-correctness-are-orthogonal-readout-axes
  confidence: high
- type: related_to
  target: '[[high-probe-accuracy-does-not-imply-causal-use]]'
  target_id: mechanism:high-probe-accuracy-does-not-imply-causal-use
  confidence: medium
- type: uses
  target: '[[activation-steering]]'
  target_id: method:activation-steering
  confidence: high
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

Amendment AA is the first causal test of whether the gate (answerability) and
dial (correctness) probe directions that read near-perfectly from Qwen3.5-4B's
residual stream (gate AUROC 0.998 at L14, dial AUROC 0.827 at L16) can be
written back in to move answer/abstain/revise behavior, and whether any effect
is position-locked to the anchor (gate) or end (dial) as the readout work
predicted. Two independent write-forms were tried on the same items: Arm A
activation steering (h <- h + alpha * d at the probe's layer, alpha swept
{-4,-2,-1,0,+1,+2,+4}, at the anchor during the initial pass and the end
during a revision pass) and Arm B CoT text injection (a third-person telemetry
note carrying the probe score, e.g. `[internal: gate 0.87 -- confident --
known]`, injected early or late in the reasoning trace, against a within-batch
shuffled-score placebo). Neither write-form moved either metric past its
effect gate at any operating point meeting the coherence floor. FALSIFIER-1
registered: the channel stays shut.

## Claims

- Evidence label: pre-registered effect gates AA-G1..AA-G4, all cells. Arm A
  gate@anchor and gate@end: FLAT, no alpha on the sweep met the effect gate
  (fallback alpha* = -2.0 reported descriptively only). Arm A dial@end and
  dial@anchor: FLAT (adequacy met: 351 wrong / 149 correct). Arm B gate@early
  (real vs placebo): abstention delta +0.33 points, 95% CI [0.00, 1.04] --
  five times below the required +10-point gate. Arm B gate@late: FLAT. Arm B
  dial@late and dial@early: appropriate-revision discrimination exactly 0.000
  in BOTH the real and placebo conditions (adequacy met on both cells).
  (experiment/protocol/AMENDMENT-AA-causal-confidence-steering.md section 7,
  table of per-cell results.)
- Evidence label: pre-registered primary gate AA-G5 (position asymmetry).
  Zero eligible passing arm x signal combinations reached AA-G5, because no
  combination passed its own effect gate (G1-G4) first.
- Evidence label: registered interpretation (verdict, 2026-07-02). Near-
  perfect latent answerability and usable correctness information do not
  translate into answer/abstain/revise behavior under either the sub-symbolic
  (activation add) or the symbolic (think-block telemetry note) write channel
  on this checkpoint.
- Named confound (pre-stated, not a new gate): the anchor position in Arm A is
  a single-token surface in the k-shot render, so Arm A flatness at the anchor
  does not by itself distinguish a causally inert signal from an intervention
  surface too small to matter; the anchor-vs-end account is not falsified by
  AA-1/AA-4 alone.
- Instrument caveat carried forward (retroactively confirmed by Amendment AB):
  the dial cells' revision-discrimination metric was saturated at 0.000 in
  every condition because under the "double-check your answer" instruction
  this model essentially never revises anything (later diagnosed in Amendment
  AB as `revised` falling back to a full-text-inequality check that a sampled
  regeneration almost never satisfies); the dial-side nulls (AA-G3/AA-G4) are
  therefore weaker evidence than the gate-side nulls, which used a live
  instrument.
- Caveats: single family (Qwen3.5-4B), single seed; Stage 2 (cross-family
  replication) was not run because its bar required a Stage-1 passing pattern
  to replicate, and none passed. Exploratory lab-notebook evidence, reported
  separately from and never pooled with the locked headline matrix.

## Relevance to experiment

AA is the opening cell of the Paper 5 line (reading vs. writing the trust
axis) and the first of the family of resolved write-side nulls that must be
read against the standing counterexample, Amendment AC
([[doubt-regulated-caution-coupling-actuates-selective-refusal-release]]), a
closed-loop erase-and-write on a different axis (doubt-regulated caution) on a
different checkpoint that DID actuate behavior. AA's own null motivated the
direct follow-up, Amendment AB
([[first-person-framed-probe-score-injection-does-not-open-text-channel]]),
which asks whether AA's text channel specifically was shut by a framing
artifact rather than genuine channel absence.
