---
aliases:
- Probe-regularized SFT
- Probe-based supervised fine-tuning
- Training model weights with a hidden-state probe signal
tags:
- kg/method
- concept
- method
kg:
  id: method:probe-regularized-supervised-finetuning
  type: method
  status: canonical
area: methods
related:
- '[[2510.21531--probe-based-fine-tuning-reducing-toxicity]]'
- '[[supervised-finetuning]]'
- '[[linear-probe]]'
relationships:
- type: proposed_by
  target: '[[2510.21531--probe-based-fine-tuning-reducing-toxicity]]'
  target_id: paper:2510.21531
  confidence: high
- type: derived_from
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
  confidence: high
- type: related_to
  target: '[[linear-probe]]'
  target_id: method:linear-probe
  confidence: high
---

Probe-regularized supervised fine-tuning adds a frozen probe's predicted
toxicity probability to the language-modeling loss. Gradients pass through the
probe into the model's layer-20 representations while the probe stays fixed.

**Why it matters here:** It is a direct example of training model weights
against an internal scalar readout.

**Lineage:** It extends [[supervised-finetuning]] with a differentiable penalty
from a [[linear-probe]].
