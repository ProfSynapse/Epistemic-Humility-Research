---
aliases:
- Doubt-regulated caution coupling actuates selective refusal release
- the standing write-side win (Amendment AC)
- erase-and-write on caution_perp beats permuted and constant-ablate controls
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:doubt-regulated-caution-coupling-actuates-selective-refusal-release
  type: mechanism
  status: canonical
cause: "On clean-SFT -> GRPO-v2 seed1, erasing the caution_perp projection from the L35 residual stream at every position and writing a doubt-proportional setpoint in its place (h' = h - (h . c_hat) c_hat + g_i * sigma_c * c_hat, g_i = -alpha * z_i from the frozen L35 doubt readout, alpha = 1, clipped to [-2, +2]), compared against a permuted-gain control (same gain distribution, doubt information shuffled across rows) and a constant-ablate control (g == 0), on known_refused (n=168), known_correct_answered (n=373), and unknown_refused (n=676) rows."
effect: "The coupled arm's known-vs-unknown selectivity gap (de-refusal on known_refused minus de-refusal on unknown_refused) beats the permuted control by +8.7 points, 10k-resample bootstrap 95% CI [+5.6, +12.0] (AC-G1 PASS), and beats constant ablate by +10.7 points, CI [+7.1, +14.5] (AC-G2). The coupled arm preserves unknown_refused refusal (0.580) where both controls release it indiscriminately (0.504 / 0.503) while matching their known_refused release (0.506 vs 0.518 / 0.536); de-refused correctness stays flat across arms (0.675 vs 0.704 / 0.705), so the doubt signal selects WHICH rows get released rather than how well released rows are answered. The specificity guard passes (known_correct_answered refusal rise -0.3pt, correctness drop 2.4pt). This is the first use-the-signal win in the research program, after Amendments M, N, R, and AA's activation arm returned nulls."
polarity: enables
related:
- '[[internal-ac-doubt-regulated-caution--coupled-write]]'
- '[[caution-residual-ablation-relaxes-overrefusal-asymmetrically]]'
- '[[trust-axis-injection-does-not-move-answer-abstain-revise-behavior]]'
- '[[first-person-framed-probe-score-injection-does-not-open-text-channel]]'
- '[[propensity-direction-reads-but-does-not-actuate-fabrication]]'
- '[[probe-agreement-reward-does-not-couple-policy-to-its-own-readout]]'
- '[[activation-steering]]'
relationships:
- type: supported_by
  target: '[[internal-ac-doubt-regulated-caution--coupled-write]]'
  target_id: paper:internal-ac-doubt-regulated-caution
  confidence: high
- type: related_to
  target: '[[caution-residual-ablation-relaxes-overrefusal-asymmetrically]]'
  target_id: mechanism:caution-residual-ablation-relaxes-overrefusal-asymmetrically
  confidence: medium
- type: related_to
  target: '[[trust-axis-injection-does-not-move-answer-abstain-revise-behavior]]'
  target_id: mechanism:trust-axis-injection-does-not-move-answer-abstain-revise-behavior
  confidence: high
- type: related_to
  target: '[[first-person-framed-probe-score-injection-does-not-open-text-channel]]'
  target_id: mechanism:first-person-framed-probe-score-injection-does-not-open-text-channel
  confidence: high
- type: related_to
  target: '[[propensity-direction-reads-but-does-not-actuate-fabrication]]'
  target_id: mechanism:propensity-direction-reads-but-does-not-actuate-fabrication
  confidence: high
- type: related_to
  target: '[[probe-agreement-reward-does-not-couple-policy-to-its-own-readout]]'
  target_id: mechanism:probe-agreement-reward-does-not-couple-policy-to-its-own-readout
  confidence: high
- type: related_to
  target: '[[activation-steering]]'
  target_id: method:activation-steering
  confidence: high
---

Amendment AC (experiment/protocol/AMENDMENT-AC-doubt-regulated-caution.md,
RQ4 Stage 1) is the first use-the-signal win in the research program: a
closed-loop erase-and-write on the caution_perp direction, driven by the
model's own frozen doubt readout, causally shifts the fabricate-vs-refuse
choice in a way that neither a permuted-gain control nor a constant-ablate
control reproduces. This is the standing write-side counterexample: it shows
activation-level writes are not uniformly null on this program's checkpoints,
so every later injection null in the family (the trust-axis probe-direction
add and CoT text injection of Amendment AA, the first-person text injection of
Amendment AB, the radial anti-propensity push of Amendment AL, and the reward-
channel coupling of Amendment AI) must be read as scoped to its own
entry-point, axis, write-form, and population, never generalized into a claim
that write-side activation edits fail as a class.
