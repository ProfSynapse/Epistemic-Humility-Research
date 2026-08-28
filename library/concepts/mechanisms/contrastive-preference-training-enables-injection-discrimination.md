---
aliases:
- Preference contrast installs injection-control discrimination
- DPO elicits concept-injection detection
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:contrastive-preference-training-enables-injection-discrimination
  type: mechanism
  status: canonical
cause: "Applying a contrastive preference objective such as [[direct-preference-optimization]] during post-training."
effect: "A chat model acquires positive true-minus-false discrimination in the [[concept-injection-introspection-test]], unlike matched non-contrastive supervised training."
polarity: enables
related:
- '[[2603.21396--mechanisms-introspective-awareness]]'
- '[[direct-preference-optimization]]'
- '[[supervised-finetuning]]'
- '[[concept-injection-introspection-test]]'
- '[[evidence-carriers-suppress-default-negative-gates]]'
relationships:
- type: supported_by
  target: '[[2603.21396--mechanisms-introspective-awareness]]'
  target_id: paper:2603.21396
  confidence: high
- type: related_to
  target: '[[direct-preference-optimization]]'
  target_id: method:direct-preference-optimization
  confidence: high
- type: different_from
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
  confidence: high
  note: "Matched SFT conditions do not produce positive injection-control discrimination in the tested checkpoints."
- type: related_to
  target: '[[concept-injection-introspection-test]]'
  target_id: method:concept-injection-introspection-test
  confidence: high
- type: related_to
  target: '[[evidence-carriers-suppress-default-negative-gates]]'
  target_id: mechanism:evidence-carriers-suppress-default-negative-gates
  confidence: medium
---

Across OLMo-3.1-32B training stages, the base and SFT checkpoints do not
discriminate injections from controls, while the DPO checkpoint does. LoRA
replications preserve the effect without a reference model and with a margin
contrastive loss, but not with chosen-only SFT, chosen-only SFT plus KL, or
shuffled preferences. The data-domain ablations indicate that no single content
domain is necessary.
