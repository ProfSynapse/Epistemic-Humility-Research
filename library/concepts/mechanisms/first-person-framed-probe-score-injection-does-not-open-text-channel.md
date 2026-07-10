---
aliases:
- First-person probe-score injection does not open the text channel
- Amendment AB ambiguous-leaning-negative
- maximum-effect natural-language framing still fails to move revision/abstention behavior
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:first-person-framed-probe-score-injection-does-not-open-text-channel
  type: mechanism
  status: canonical
cause: "On Qwen3.5-4B (Amendment AB), injecting a first-person recall-experience note that names the gate or dial probe score as a percent and states a score-conditional decision rule (e.g. naming a band-specific action: commit, verify, or say I don't know), into the reasoning trace at the early, late, or think-final (commit-point) position, against a within-batch shuffled-score placebo, on the same gate and dial pools as Amendment AA."
effect: "No V1 cell passes its effect gate. Dial@late (AB-G1, PRIMARY) is unmeasurable: the revision-detection instrument saturates (revised reads True in 500/500 rows both arms), though descriptive decision-level flows stay flat. Dial@final (AB-G1f, valid instrument): real vs placebo appropriate-revision discrimination delta -2.7 points, 95% CI [-9.8, +4.3], includes zero. Gate@early (AB-G2): real-vs-placebo unknown-question abstention delta +2.0 points, 95% CI [0.33, 3.85] (CI excludes zero but the effect is 5x below the +10-point gate). Verdict: AMBIGUOUS-LEANING-NEGATIVE -- SUCCESS is not met (no cell clears its effect gate) and the strict falsifier wording is not met either (AB-G2's small delta is real), so first-person framing with an interpretable percent and an explicit action rule leaks only a ~2-point, ~2-3%-verbatim-compliance trickle and opens nothing at the registered thresholds."
polarity: prevents
related:
- '[[internal-ab-first-person-injection--ambiguous-negative]]'
- '[[trust-axis-injection-does-not-move-answer-abstain-revise-behavior]]'
- '[[high-probe-accuracy-does-not-imply-causal-use]]'
- '[[doubt-regulated-caution-coupling-actuates-selective-refusal-release]]'
- '[[chain-of-thought-prompting]]'
relationships:
- type: supported_by
  target: '[[internal-ab-first-person-injection--ambiguous-negative]]'
  target_id: paper:internal-ab-first-person-injection
  confidence: high
- type: related_to
  target: '[[trust-axis-injection-does-not-move-answer-abstain-revise-behavior]]'
  target_id: mechanism:trust-axis-injection-does-not-move-answer-abstain-revise-behavior
  confidence: high
- type: related_to
  target: '[[high-probe-accuracy-does-not-imply-causal-use]]'
  target_id: mechanism:high-probe-accuracy-does-not-imply-causal-use
  confidence: medium
- type: related_to
  target: '[[doubt-regulated-caution-coupling-actuates-selective-refusal-release]]'
  target_id: mechanism:doubt-regulated-caution-coupling-actuates-selective-refusal-release
  confidence: high
- type: related_to
  target: '[[chain-of-thought-prompting]]'
  target_id: method:chain-of-thought-prompting
  confidence: high
---

Amendment AB (experiments/first-person-injection/AMENDMENT.md,
verdict locked 2026-07-03) tests whether Amendment AA's shut CoT text channel
([[trust-axis-injection-does-not-move-answer-abstain-revise-behavior]]) was a
prompt-register artifact rather than genuine channel absence, by replacing
AA's bracketed third-person telemetry note with the maximum-effect natural-
language framing: first-person voice, an interpretable percent, and an
explicit score-conditional action rule, injected at early, late, or think-
final position. None of the three V1 cells clears its effect gate; the dial-
side instrument that AA also relied on turns out to be saturated (a
retroactive correction to AA's dial-side reading), and the one live-instrument
gate-side delta is real but five times too small to count as opening the
channel. This is scoped to the CoT text-injection write-form on the gate/dial
trust axis on Qwen3.5-4B; it is one more instance of the general pattern that
an accurate, causally-connectable self-report does not by itself get used
([[high-probe-accuracy-does-not-imply-causal-use]]), and it stands in contrast
to Amendment AC's successful activation-level erase-and-write
([[doubt-regulated-caution-coupling-actuates-selective-refusal-release]]) on a
different axis and write-form.
