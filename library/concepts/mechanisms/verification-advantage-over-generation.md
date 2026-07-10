---
aliases:
- Verification Scales Faster than Generation
- conditional accuracy gap grows with model size
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:verification-advantage-over-generation
  type: mechanism
  status: canonical
cause: Increasing language model parameter count (800M to 52B) while evaluating P(True) self-evaluation on sampling-based tasks at unit temperature
effect: The gap between conditional accuracy (responses where P(True) > 0.5) and base unconditional accuracy grows with model size, indicating that the benefit of self-evaluation screening increases as models scale
polarity: increases
related:
- '[[2207.05221--lms-mostly-know-what-they-know]]'
- '[[p-true]]'
- '[[brier-score]]'
- '[[self-knowledge]]'
relationships:
- type: supported_by
  target: '[[2207.05221--lms-mostly-know-what-they-know]]'
  target_id: paper:2207.05221
  confidence: high
- type: related_to
  target: '[[p-true]]'
  target_id: method:p-true
- type: related_to
  target: '[[brier-score]]'
  target_id: metric:brier-score
- type: related_to
  target: '[[self-knowledge]]'
  target_id: term:self-knowledge
---

At small scales, models generate poor answers and are also poor at evaluating them, so
P(True) filtering provides limited marginal accuracy gain. As model size increases, both
generation quality and self-evaluation quality improve, but the paper (arXiv:2207.05221,
§4.2, Figure 11, bottom) shows that self-evaluation quality improves relatively faster:
the conditional accuracy among P(True)-selected responses grows more rapidly than the base
unconditional accuracy. This creates an expanding gap with scale, consistent with the
informal intuition that checking an answer is computationally easier than generating it
correctly.

The observation parallels arguments about using models as verifiers in scalable oversight.
If verification quality scales better than generation quality, larger models become
increasingly useful as critics of smaller models' outputs, even before they become
reliable generators themselves. This asymmetry is a favorable property for abstention
training: at scale, a model capable of identifying its own errors may be teachable to
express appropriate uncertainty rather than hallucinate confidently.

**Why it matters here:** For mechinterp, this mechanism predicts that the
internal representations encoding answer correctness should be more separable at larger
scale, making probing easier and activation steering more reliable. For Phase 1,
it motivates comparing SFT/DPO/KTO abstention improvement against the pretrained
P(True) baseline, asking whether training closes the remaining gap or merely recapitulates
the same size-dependent advantage.
