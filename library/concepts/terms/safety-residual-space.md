---
aliases:
- residual space of safety fine-tuning
tags:
- kg/term
- concept
- term
kg:
  id: term:safety-residual-space
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[2502.09674--hidden-dimensions-llm-alignment-multi-dimensional-analysis]]'
- '[[linear-representation-hypothesis]]'
relationships:
- type: proposed_by
  target: '[[2502.09674--hidden-dimensions-llm-alignment-multi-dimensional-analysis]]'
  target_id: paper:2502.09674
  confidence: high
- type: related_to
  target: '[[linear-representation-hypothesis]]'
  target_id: term:linear-representation-hypothesis
---

The safety residual space is the vector subspace of activation differences
induced by safety fine-tuning, formally defined as the column space of the
matrix (W - I), where W is the linear map that takes pre-training hidden
states to their post-safety-fine-tuning counterparts. Principal components are
extracted via singular value decomposition; the resulting orthogonal singular
vectors capture distinct directions of change introduced by safety training.
The top singular vector corresponds to the [[dominant-refusal-direction]], while
lower-ranked vectors encode interpretable secondary features such as
hypothetical-narrative framing, role-playing context, and harm-topic
recognition.

**Why it matters here:** Decomposing safety fine-tuning into its principal
directions reveals which aspects of the training shift encode refusal
versus other safety-adjacent behaviors (including over-caution), enabling
targeted interventions that preserve epistemic calibration while maintaining
safety.

**Lineage:** assumes the [[linear-representation-hypothesis]]; the singular
vectors produced by SVD of the safety residual space are the building blocks
of the [[dominant-refusal-direction]] framework.
