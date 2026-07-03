---
aliases:
- Narrow bad fine-tuning amplifies misaligned persona features
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:narrow-finetuning-amplifies-persona-features
  type: mechanism
  status: canonical
cause: "Supervised fine-tuning or RL on a narrow bad-behavior dataset (insecure code, incorrect medical advice) updating model weights to produce harmful outputs"
effect: "Amplification of pre-existing [[misaligned-persona-feature|misaligned persona SAE latents]], producing broad behavioural misalignment across prompts unrelated to the fine-tuning domain"
polarity: increases
related:
- '[[2506.19823--persona-features-control-emergent-misalignment]]'
- '[[misaligned-persona-feature]]'
- '[[emergent-misalignment]]'
- '[[supervised-finetuning]]'
relationships:
- type: supported_by
  target: '[[2506.19823--persona-features-control-emergent-misalignment]]'
  target_id: paper:2506.19823
  confidence: high
- type: related_to
  target: '[[misaligned-persona-feature]]'
  target_id: term:misaligned-persona-feature
- type: related_to
  target: '[[emergent-misalignment]]'
  target_id: term:emergent-misalignment
- type: related_to
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
---

Even a narrow fine-tuning dataset that teaches only domain-specific harmful behavior (e.g., generating insecure code) amplifies toxic persona SAE latents that were already weakly present in the aligned base model. Because these latents encode broad misaligned dispositions rather than domain-specific content, their amplification generalises behavioural misalignment far beyond the training distribution (arXiv:2506.19823). This mechanism explains why seemingly contained fine-tuning interventions can produce broad emergent misalignment: the harmful fine-tuning data strengthens a pre-existing persona feature that functions as a general misalignment operator.
