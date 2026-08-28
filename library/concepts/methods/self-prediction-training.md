---
aliases:
- Self-prediction training
- Behavioral self-prediction fine-tuning
- Hypothetical self-prediction training
tags:
- kg/method
- concept
- method
kg:
  id: method:self-prediction-training
  type: method
  status: canonical
area: methods
related:
- '[[2410.13787--looking-inward-language-models-can-learn-about]]'
- '[[supervised-finetuning]]'
- '[[introspection-fine-tuning]]'
- '[[behavioral-introspection]]'
relationships:
- type: proposed_by
  target: '[[2410.13787--looking-inward-language-models-can-learn-about]]'
  target_id: paper:2410.13787
  confidence: high
- type: derived_from
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
  confidence: high
- type: related_to
  target: '[[introspection-fine-tuning]]'
  target_id: method:introspection-fine-tuning
  confidence: medium
- type: related_to
  target: '[[behavioral-introspection]]'
  target_id: term:behavioral-introspection
  confidence: high
---

Self-prediction training fine-tunes a model to predict simple properties of the
response it would produce for a hypothetical prompt. Labels come from separate
object-level runs of the same model, and evaluation uses datasets held out from
fine-tuning.

**Why it matters here:** The method trains a verbal self-report about future
behavior. It does not expose hidden activations or install a direct
readout-to-generation gate.

**Lineage:** It is supervised fine-tuning on model-specific behavioral labels.
It differs from activation-injection [[introspection-fine-tuning]], which uses
controlled residual-stream perturbations as ground truth.
