---
aliases:
- selected-layer latent optimization is less sensitive to learning rate than output-side latent optimization
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:intermediate-latent-optimization-reduces-step-size-sensitivity
  type: mechanism
  status: canonical
cause: "Latents are optimized within an intermediate hidden-state space that retains downstream Transformer computation."
effect: "Test-time accuracy varies less across learning-rate choices than with the evaluated output-side latent interface."
polarity: decreases
related:
- '[[2608.02585--gradcuit-credit-assigned-gradient-flow-enables-robust]]'
- '[[gradcuit]]'
relationships:
- type: supported_by
  target: '[[2608.02585--gradcuit-credit-assigned-gradient-flow-enables-robust]]'
  target_id: paper:2608.02585
  confidence: high
- type: related_to
  target: '[[gradcuit]]'
  target_id: method:gradcuit
  confidence: high
---

Across seven learning-rate settings in Section 3.3 and Figure 2, GradCuit
reports a standard deviation of 0.82 accuracy points compared with 1.53 for
LatentSeek, while also retaining a higher mean. The evidence is limited to
LLaMA-3.2-3B-Instruct on MATH-500 with one answer format.
