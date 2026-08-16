---
aliases:
- Probe-as-reward GRPO training does not couple the policy to its own readout
- Amendment AI reward-channel null, congruence inverted
- reward-is-the-readout training makes the policy LESS congruent than a random reward
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:probe-agreement-reward-does-not-couple-policy-to-its-own-readout
  type: mechanism
  status: canonical
cause: "Training a Qwen3-4B clean-SFT policy with GRPO using a probe-agreement reward (R_agree = p if abstained else 1-p, p = P(unanswerable) read at the pre-generation anchor by an L24 linear probe refit on the training-start checkpoint, held-out OOF AUROC 0.9945), on a divergent-row-enriched pool, TRUE-sensor arm vs a PERMUTED-sensor control (same reward statistics, sensor score permuted within gold class), both arms run the full 2,934 steps with no tripwire halts."
effect: "On the 400-row held-out divergent eval, own-readout congruence (measured per arm against that arm's own fresh eval probe) is 59.75% for the TRUE arm vs 76.75% for the PERMUTED arm, a -17.0 point differential, 10k paired bootstrap 95% CI [-21.5, -12.5] (seed 0) -- the required gate was >= +10 points with CI excluding 0, and the CI excludes 0 on the opposite side; every descriptive stratum (fresh-divergent, D-over, D-under, union origin, mining origin) points the same direction. The TRUE arm nonetheless preserves the refusal boundary better than the control (abstain-when-unanswerable +0.49pt vs the GRPO-v2 reference, 40% fewer hallucinations on unknowns than PERMUTED, higher precision among answered), consistent with the reward teaching semantic correlates of what the sensor fires on rather than readout consultation."
polarity: prevents
related:
- '[[internal-ai-probe-as-reward-null--true-vs-permuted]]'
- '[[propensity-direction-reads-but-does-not-actuate-fabrication]]'
- '[[ku-readout-coupling-actuates-selective-refusal-release]]'
- '[[high-probe-accuracy-does-not-imply-causal-use]]'
- '[[trust-axis-injection-does-not-move-answer-abstain-revise-behavior]]'
- '[[group-relative-policy-optimization]]'
relationships:
- type: supported_by
  target: '[[internal-ai-probe-as-reward-null--true-vs-permuted]]'
  target_id: paper:internal-ai-probe-as-reward-null
  confidence: high
- type: related_to
  target: '[[group-relative-policy-optimization]]'
  target_id: method:group-relative-policy-optimization
  confidence: high
- type: related_to
  target: '[[propensity-direction-reads-but-does-not-actuate-fabrication]]'
  target_id: mechanism:propensity-direction-reads-but-does-not-actuate-fabrication
  confidence: high
- type: related_to
  target: '[[ku-readout-coupling-actuates-selective-refusal-release]]'
  target_id: mechanism:ku-readout-coupling-actuates-selective-refusal-release
  confidence: high
- type: related_to
  target: '[[high-probe-accuracy-does-not-imply-causal-use]]'
  target_id: mechanism:high-probe-accuracy-does-not-imply-causal-use
  confidence: medium
- type: related_to
  target: '[[trust-axis-injection-does-not-move-answer-abstain-revise-behavior]]'
  target_id: mechanism:trust-axis-injection-does-not-move-answer-abstain-revise-behavior
  confidence: medium
---

Amendment AI (experiments/probe-as-reward/AMENDMENT.md, adjudicated
NULL 2026-07-05) tried the most direct incentive design available for
readout-consultation: make the RL reward equal to the policy's own pre-
generation probe score. The trained policy ends up significantly LESS
congruent with its own readout than a random-reward control, not merely flat,
so the reward channel does not couple the policy to its readout on this
checkpoint and pool. This is the training-side sibling of
[[propensity-direction-reads-but-does-not-actuate-fabrication]] (the
injection-side null on a different axis) and, together with the trust-axis
and text-injection nulls, must be read against Amendment AC's activation-
coupling win
([[ku-readout-coupling-actuates-selective-refusal-release]]) as
evidence that this program's negative results are specific to the channel and
axis tested, not a general claim that internal readouts are behaviorally
inert.
