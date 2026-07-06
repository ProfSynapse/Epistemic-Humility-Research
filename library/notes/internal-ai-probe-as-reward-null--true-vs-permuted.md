---
title: 'Probe-as-Reward GRPO Training Does Not Couple the Policy to Its Own Readout; Congruence Inverts (Amendment AI)'
tags:
- kg/paper
- paper
- epistemic-humility
- internal
kg:
  id: paper:internal-ai-probe-as-reward-null
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
provenance: 'Internal amendment (Tier-A causal intervention; gates pre-stated before launch). Source of truth: experiment/protocol/AMENDMENT-AI-probe-as-reward.md, section 5 (Verdict, scored and adjudicated NULL by the user 2026-07-05). Sensor: L24 linear probe refit on the training-start checkpoint in the 4-bit training serving configuration (held-out OOF AUROC 0.9945). Training pool: 2,102 train divergent (mining-only, in-loop-sensor classified) + 16,665 concordant; 400-row locked holdout, category-stratified. Scorer: amendment_ai_verdict_score.py over the all-local evidence set (both arms full 2934/2934 steps, no halts).'
related:
- '[[probe-agreement-reward-does-not-couple-policy-to-its-own-readout]]'
- '[[propensity-direction-reads-but-does-not-actuate-fabrication]]'
- '[[doubt-regulated-caution-coupling-actuates-selective-refusal-release]]'
- '[[high-probe-accuracy-does-not-imply-causal-use]]'
- '[[answerability-and-correctness-are-orthogonal-readout-axes]]'
- '[[linear-probe]]'
- '[[unanswerable-questions]]'
- '[[auroc]]'
- '[[group-relative-policy-optimization]]'
relationships:
- type: supports
  target: '[[probe-agreement-reward-does-not-couple-policy-to-its-own-readout]]'
  target_id: mechanism:probe-agreement-reward-does-not-couple-policy-to-its-own-readout
  confidence: high
- type: uses
  target: '[[group-relative-policy-optimization]]'
  target_id: method:group-relative-policy-optimization
  confidence: high
- type: related_to
  target: '[[propensity-direction-reads-but-does-not-actuate-fabrication]]'
  target_id: mechanism:propensity-direction-reads-but-does-not-actuate-fabrication
  confidence: high
- type: related_to
  target: '[[doubt-regulated-caution-coupling-actuates-selective-refusal-release]]'
  target_id: mechanism:doubt-regulated-caution-coupling-actuates-selective-refusal-release
  confidence: high
- type: related_to
  target: '[[high-probe-accuracy-does-not-imply-causal-use]]'
  target_id: mechanism:high-probe-accuracy-does-not-imply-causal-use
  confidence: medium
- type: related_to
  target: '[[answerability-and-correctness-are-orthogonal-readout-axes]]'
  target_id: mechanism:answerability-and-correctness-are-orthogonal-readout-axes
  confidence: medium
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

Amendment AI asks whether GRPO with a probe-agreement reward, read from the
policy's own pre-generation activations by a sensor refit on the training-
start checkpoint, trains the model to consult its own readout. Per rollout
the reward is R_agree = p if abstained else (1 - p), where p is the L24
probe's P(unanswerable), plus small derived correctness and right-abstention
bonuses; a TRUE-sensor arm is trained against a PERMUTED-sensor control (same
reward statistics, sensor score permuted within gold class) on an identical
divergent-row-enriched pool, both arms running the full 2,934 steps with no
tripwire halts. On the held-out divergent eval, own-readout congruence is
measured for each arm against its OWN fresh eval probe. The TRUE arm ends up
LESS congruent with its own readout than the random-reward control: congruence
59.75% (TRUE) vs 76.75% (PERMUTED), a -17.0 point differential in the wrong
direction from the +10 point gate. The reward channel does not couple the
policy to its readout either; it strengthens the pattern of use-the-signal
nulls across trained channels.

## Claims

- Evidence label: pre-registered integrity gate AI-G0. PASS, both arms. TRUE
  2934/2934 steps, no halt, fresh-checkpoint probe OOF AUROC 0.9948; PERMUTED
  2934/2934 steps, no halt, OOF AUROC 0.9946 (both against the >= 0.8
  falsifier floor). Training destroyed nothing: the G1 result below is
  signal, not instrument failure. (experiment/protocol/AMENDMENT-AI-probe-as-reward.md
  section 5.)
- Evidence label: pre-registered primary gate AI-G1 (use-the-signal). FAIL,
  significantly inverted. TRUE congruence 59.75% vs PERMUTED 76.75% on the
  400-row gold-labeled holdout; differential -17.0 points, 10k paired
  bootstrap 95% CI [-21.5, -12.5] (seed 0) -- the gate required >= +10 points
  with CI excluding 0, and the CI excludes 0 on the opposite side. Every
  descriptive stratum points the same direction (fresh-divergent -18.1,
  D-over -16.5, D-under -30.8, union origin -23.8, mining origin -16.6).
- Evidence label: pre-registered no-regression gate AI-G2. FAIL for both arms
  vs the pinned GRPO-v2 reference (93.41 / 33.38 / 53.85 on the standard
  SelfAware behavior-panel trio). TRUE: abstain-when-unanswerable 93.90
  (+0.49pt, within 5pt); answer-when-answerable 71.25 (+37.87pt, fails);
  correctness-among-answered 33.63 (-20.22pt, fails). PERMUTED (descriptive):
  89.73 / 86.22 / 27.99 -- both arms release the generic GRPO over-refusal
  drift, the control drifting harder; the TRUE arm alone preserves the
  refusal boundary and holds higher precision among answered (33.6 vs 28.0).
- Evidence label: mechanical verdict tier (section 2 rules applied to the
  observed gates). NULL (G1 fail, G0 pass): the reward channel also does not
  couple the readout. Composition note (post-hoc, not a re-scoring): 387/400
  holdout rows are D-over (readout says answerable, gold unknown), so
  congruence-with-own-readout on this pool numerically tracks answer rate
  (TRUE answered 238/400, PERMUTED 316/400); the negative differential has a
  mechanistic reading -- the TRUE arm learned to refuse divergent rows whose
  own readout still says "answer", anti-congruent by the locked measure but
  boundary-preserving in behavior.
- Evidence label: registered interpretation. With the most direct incentive
  available, the reward IS the readout computed from the policy's own
  pre-generation states, the trained policy ends up less congruent with its
  readout than a random-reward control. The differential behavior the sensor
  reward did buy (boundary held, 40% fewer hallucinations on unknowns than
  PERMUTED, higher precision) is consistent with GRPO learning the semantic
  correlates of what the sensor fires on, not readout consultation. This
  extends the knows-but-doesn't-consult shape to the reward channel, joining
  the use-the-signal nulls M (SFT distillation), N (KL), R (co-train), AA/AB
  (text self-report).
- Caveats: single checkpoint lineage (clean-SFT base), single seed per arm;
  seed replication explicitly deferred to backlog by the user 2026-07-05.
  Exploratory lab-notebook evidence, reported separately from and never
  pooled with the locked headline matrix.

## Relevance to experiment

AI closes the training-side branch of the use-the-signal question with the
most direct incentive design tried (reward equals readout) and still finds no
coupling, joining
[[propensity-direction-reads-but-does-not-actuate-fabrication]] (AL, the
injection-side branch) as sibling nulls in different channels on the same
question. Both stand against Amendment AC's activation-coupling win
([[doubt-regulated-caution-coupling-actuates-selective-refusal-release]]),
which shows the negative result is channel- and axis-specific, not a general
claim that the model's internal states are never behaviorally accessible.
