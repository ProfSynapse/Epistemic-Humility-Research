---
aliases:
- Generation-Time Computation Loads Off the Epistemic Plane
- off-plane generation trajectory on confabulating rows
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:generation-time-computation-loads-off-the-epistemic-plane
  type: mechanism
  status: canonical
cause: "Autoregressive generation of an answer to an unanswerable question on a clean-SFT to GRPO-v2 checkpoint, measured as the hidden-state displacement from the pre-generation anchor at six positions (anchor, first-visible, mid25/50/75, answer-end) against the L35 doubt and caution_perp axes."
effect: "Roughly 99 percent of the displacement at every position lies outside the doubt / caution_perp plane (in-plane fraction 0.10-0.16, residual fraction 0.986-0.994); mean-displacement absolute cosine stays at or below 0.17 against every axis, per-axis variance fraction stays 0.3-2.7 percent, and the delta profile oscillates in sign with no monotone growth and no answer-end or think-close crystallization, even though displacement norms are large (370-560)."
polarity: mediates
related:
- '[[internal--diag-item20-gentime-displacement]]'
- '[[answerability-and-correctness-are-orthogonal-readout-axes]]'
- '[[post-generation-veto-is-rederived-not-carried]]'
- '[[pre-generation-commitment-signal-predicts-confabulation]]'
- '[[activation-addition]]'
- '[[known-unknown-direction]]'
- '[[residual-stream]]'
relationships:
- type: supported_by
  target: '[[internal--diag-item20-gentime-displacement]]'
  target_id: paper:internal-diag-item20
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
  target: '[[known-unknown-direction]]'
  target_id: term:known-unknown-direction
  confidence: high
---

Internal lab-notebook diagnostics (item 20) decomposed the generation-time hidden-state
trajectory on confabulating rows against the epistemic axes. The state moves a great
deal (displacement norms 370-560) but almost none of that movement loads onto the
doubt / caution_perp plane: the epistemic loading stays small and flat across the whole
mid-generation trajectory with no crystallization at the answer end. This extends the
earlier anchor-only observation that priming writes almost entirely off the readable
epistemic axes to the full trajectory: generation-time computation is dominated by
content machinery while the epistemic plane loading remains negligible. Caveat: the
extractor captures states only on answered rows over an all-unknown pool, so n=41 and
all rows are confabulations, giving no answered-versus-refused contrast.
