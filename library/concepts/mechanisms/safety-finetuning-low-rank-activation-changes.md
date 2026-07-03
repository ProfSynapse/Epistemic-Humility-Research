---
aliases:
- Safety fine-tuning produces low-rank activation changes
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:safety-finetuning-low-rank-activation-changes
  type: mechanism
  status: canonical
cause: "Supervised safety fine-tuning (SSFT) on harmful vs. harmless prompt pairs updating model weights to distinguish safe from unsafe requests"
effect: "Low effective rank of the activation shift matrix (the difference between post- and pre-SSFT residual-stream activations), indicating that safety learning concentrates in a small subspace"
polarity: decreases
related:
- '[[2502.09674--hidden-dimensions-llm-alignment-multi-dimensional-analysis]]'
- '[[safety-residual-space]]'
- '[[refusal-direction]]'
relationships:
- type: supported_by
  target: '[[2502.09674--hidden-dimensions-llm-alignment-multi-dimensional-analysis]]'
  target_id: paper:2502.09674
  confidence: high
- type: related_to
  target: '[[safety-residual-space]]'
  target_id: term:safety-residual-space
- type: related_to
  target: '[[refusal-direction]]'
  target_id: term:refusal-direction
---

Despite large datasets and many gradient steps, safety fine-tuning changes the model's residual-stream activations along only a handful of dominant directions, as evidenced by the rapidly decaying singular-value spectrum of the activation-shift matrix (arXiv:2502.09674). This low-rank structure is precisely the [[safety-residual-space]] used to extract refusal directions via PCA or difference-in-means, and it explains why single-direction ablations achieve high jailbreak success rates. The concentration also implies that safety is a thin overlay on the base model rather than a pervasive rewiring of the internal representation.
