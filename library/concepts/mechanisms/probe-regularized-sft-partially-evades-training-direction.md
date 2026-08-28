---
aliases:
- Probe-regularized SFT partially evades its training probes
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:probe-regularized-sft-partially-evades-training-direction
  type: mechanism
  status: canonical
cause: "[[probe-regularized-supervised-finetuning]] directly backpropagates through a fixed toxicity probe."
effect: "The trained model lowers detectability along the specific probe direction while toxicity remains linearly separable to held-out or retrained probes."
polarity: redistributes
related:
- '[[2510.21531--probe-based-fine-tuning-reducing-toxicity]]'
- '[[probe-regularized-supervised-finetuning]]'
- '[[linear-probe]]'
relationships:
- type: supported_by
  target: '[[2510.21531--probe-based-fine-tuning-reducing-toxicity]]'
  target_id: paper:2510.21531
  confidence: high
- type: related_to
  target: '[[probe-regularized-supervised-finetuning]]'
  target_id: method:probe-regularized-supervised-finetuning
  confidence: high
- type: related_to
  target: '[[linear-probe]]'
  target_id: method:linear-probe
  confidence: high
---

Probe-regularized SFT reduced training-probe AUC modestly, while held-out and
retrained probes stayed accurate. This indicates a shift in the usable linear
direction rather than removal of linearly detectable toxicity information.
