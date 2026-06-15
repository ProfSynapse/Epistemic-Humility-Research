---
aliases:
- SFT suppresses honesty expression without destroying knowledge-boundary representations
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:sft-suppresses-honesty-expression
  type: mechanism
  status: canonical
cause: Domain-specific [[supervised-finetuning]] perturbs neurons that govern the expression of [[knowledge-boundary]] awareness
effect: The model produces confident fabrications on out-of-scope questions even though internal representations still linearly encode answerable vs. unanswerable distinctions at high [[auroc]]
polarity: prevents
related:
- '[[2511.12991--finetuned-llms-know-they-dont-know]]'
- '[[supervised-finetuning]]'
- '[[knowledge-boundary]]'
- '[[auroc]]'
relationships:
- type: supported_by
  target: '[[2511.12991--finetuned-llms-know-they-dont-know]]'
  target_id: paper:2511.12991
  confidence: high
- type: related_to
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
- type: related_to
  target: '[[knowledge-boundary]]'
  target_id: term:knowledge-boundary
- type: related_to
  target: '[[auroc]]'
  target_id: metric:auroc
---

Domain SFT shifts model weights to optimize task-specific outputs, inadvertently suppressing the neurons responsible for expressing epistemic uncertainty without erasing the underlying knowledge-boundary encodings. A linear probe on post-SFT representations still achieves high AUROC for distinguishing answerable from unanswerable questions, confirming the latent structure persists. The finetuned-LLMs paper (arXiv:2511.12991) uses this dissociation to motivate targeted neuron-level intervention ([[honesty-critical-neurons-restoration]]) rather than retraining from scratch.
