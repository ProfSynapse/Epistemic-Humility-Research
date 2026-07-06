---
aliases:
- Amendment AA channel-stays-shut null
- writing the gate/dial probe directions back in does not move answer/abstain/revise behavior
- FALSIFIER-1 (causal confidence steering)
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:trust-axis-injection-does-not-move-answer-abstain-revise-behavior
  type: mechanism
  status: canonical
cause: "On Qwen3.5-4B (Amendment AA Stage 1), writing the gate (answerability, L14 probe AUROC 0.998) and dial (correctness, L16 probe AUROC 0.827) directions back into generation on the SelfAware known/unknown pool (gate cells) and the PopQA+TriviaQA answerable pool (dial cells): Arm A activation steering (h <- h + alpha * d, alpha swept -4..+4) at the anchor (initial pass) and end (revision pass) positions, and Arm B CoT text injection of a third-person telemetry note carrying the true probe score against a within-batch shuffled-score placebo, at early and late positions in the reasoning trace."
effect: "No effect gate passed in any of the 8 registered cells at any alpha meeting the 5% coherence floor. Activation steering: gate@anchor and gate@end FLAT (no qualifying alpha*); dial@end and dial@anchor FLAT (adequacy 351 wrong / 149 correct). Text injection: gate@early real-vs-placebo abstention delta +0.33pt, 95% CI [0.00, 1.04], five times below the +10pt gate; gate@late FLAT; dial@late and dial@early appropriate-revision discrimination exactly 0.000 in BOTH real and placebo arms. AA-G5 (position asymmetry, primary) had zero eligible passing combinations. FALSIFIER-1 registered: near-perfect latent answerability and usable correctness information do not translate into answer/abstain/revise behavior under either the sub-symbolic or the symbolic write channel on this checkpoint."
polarity: prevents
related:
- '[[internal-aa-causal-confidence-steering-null--qwen3.5-4b]]'
- '[[answerability-and-correctness-are-orthogonal-readout-axes]]'
- '[[high-probe-accuracy-does-not-imply-causal-use]]'
- '[[first-person-framed-probe-score-injection-does-not-open-text-channel]]'
- '[[doubt-regulated-caution-coupling-actuates-selective-refusal-release]]'
- '[[activation-steering]]'
- '[[chain-of-thought-prompting]]'
relationships:
- type: supported_by
  target: '[[internal-aa-causal-confidence-steering-null--qwen3.5-4b]]'
  target_id: paper:internal-aa-causal-confidence-steering-null
  confidence: high
- type: related_to
  target: '[[answerability-and-correctness-are-orthogonal-readout-axes]]'
  target_id: mechanism:answerability-and-correctness-are-orthogonal-readout-axes
  confidence: high
- type: related_to
  target: '[[high-probe-accuracy-does-not-imply-causal-use]]'
  target_id: mechanism:high-probe-accuracy-does-not-imply-causal-use
  confidence: medium
- type: related_to
  target: '[[first-person-framed-probe-score-injection-does-not-open-text-channel]]'
  target_id: mechanism:first-person-framed-probe-score-injection-does-not-open-text-channel
  confidence: high
- type: related_to
  target: '[[doubt-regulated-caution-coupling-actuates-selective-refusal-release]]'
  target_id: mechanism:doubt-regulated-caution-coupling-actuates-selective-refusal-release
  confidence: high
- type: related_to
  target: '[[activation-steering]]'
  target_id: method:activation-steering
  confidence: high
- type: related_to
  target: '[[chain-of-thought-prompting]]'
  target_id: method:chain-of-thought-prompting
  confidence: high
---

Amendment AA (experiment/protocol/AMENDMENT-AA-causal-confidence-steering.md,
Stage-1 verdict 2026-07-02) turned the two-signal readout
([[answerability-and-correctness-are-orthogonal-readout-axes]]) around: it
wrote the gate and dial probe directions back into Qwen3.5-4B's generation
through activation steering and through CoT text injection, and asked whether
answer/abstain/revise behavior moved, and whether it moved position-
specifically. It did not move on either write-form at any operating point
meeting the coherence floor, so FALSIFIER-1 fired and the position-asymmetry
gate (AA-G5) had nothing to test. This is scoped to the gate/dial trust axis
on Qwen3.5-4B specifically; it does not generalize to every write-side
activation edit, since Amendment AC's doubt-regulated caution coupling
([[doubt-regulated-caution-coupling-actuates-selective-refusal-release]]), on
a different axis and checkpoint, does actuate behavior. The direct follow-up,
Amendment AB, tests whether AA's text channel specifically was shut by a
framing artifact rather than genuine channel absence
([[first-person-framed-probe-score-injection-does-not-open-text-channel]]).
