---
aliases:
- Low-Rank Representation Adaptation
- representation engineering adapter
- LoRRA intervention
tags:
- kg/method
- concept
- method
kg:
  id: method:lorra
  type: method
  status: canonical
area: methods
related:
- '[[2503.03750--mask-benchmark-honesty]]'
- '[[representation-engineering]]'
- '[[inference-time-intervention]]'
- '[[contrastive-activation-addition]]'
- '[[mask-benchmark]]'
- '[[truth-direction]]'
- '[[low-rank-adaptation]]'
relationships:
- type: proposed_by
  target: '[[2503.03750--mask-benchmark-honesty]]'
  target_id: paper:2503.03750
  confidence: high
- type: related_to
  target: '[[representation-engineering]]'
  target_id: method:representation-engineering
  confidence: medium
- type: related_to
  target: '[[inference-time-intervention]]'
  target_id: method:inference-time-intervention
  confidence: medium
- type: related_to
  target: '[[contrastive-activation-addition]]'
  target_id: method:contrastive-activation-addition
  confidence: medium
- type: related_to
  target: '[[mask-benchmark]]'
  target_id: dataset:mask-benchmark
  confidence: medium
- type: related_to
  target: '[[truth-direction]]'
  target_id: term:truth-direction
  confidence: medium
- type: related_to
  target: '[[low-rank-adaptation]]'
  target_id: method:low-rank-adaptation
  confidence: medium
---

A representation-engineering technique that trains low-rank LoRA adapters on earlier editable layers to align later target-layer activations with a contrast vector computed as the difference between honest-prompted and dishonest-prompted representations. The contrast vector is added at a strength hyperparameter alpha to guide the model toward honest internal states during inference.

**Why it matters here:** Demonstrates that internal activation steering toward honest representations can improve commission honesty by 6-13 percentage points in small Llama models, providing a proof-of-concept and effect-size prior for Phase 3 activation-steering experiments targeting honesty rather than abstention.

**Lineage:** Applied in the MASK paper (2503.03750) as a baseline intervention, derived from the representation-engineering framework of Zou et al. (2023). Closely related to inference-time-intervention and contrastive-activation-addition.
