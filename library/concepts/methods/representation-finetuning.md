---
aliases:
- ReFT
- Representation Finetuning
tags:
- kg/method
- concept
- method
kg:
  id: method:representation-finetuning
  type: method
  status: canonical
area: methods
related:
- '[[2404.03592--reft-representation-finetuning-language-models]]'
- '[[activation-intervention]]'
- '[[representation-control]]'
relationships:
- type: proposed_by
  target: '[[2404.03592--reft-representation-finetuning-language-models]]'
  target_id: paper:2404.03592
  confidence: high
- type: related_to
  target: '[[activation-intervention]]'
  target_id: method:activation-intervention
  confidence: high
- type: related_to
  target: '[[representation-control]]'
  target_id: method:representation-control
  confidence: high
---

Representation Finetuning is a family of methods that freezes a pretrained
language model and learns task-specific functions that modify selected hidden
representations during the forward pass. Each intervention specifies a learned
function, a set of token positions, and a layer.

**Why it matters here:** ReFT provides a trainable representation-control
surface for testing whether a learned internal-state intervention can govern
generation across tasks.

**Lineage:** ReFT generalizes representation editing and is motivated by causal
abstraction and interchange-intervention methods.
