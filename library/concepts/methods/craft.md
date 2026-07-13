---
aliases:
- Certainty Represented Knowledge Flow for Refusal-Aware Instructions Construction
- CRaFT
- CorCer-RAIT
tags:
- kg/method
- concept
- method
kg:
  id: method:craft
  type: method
  status: canonical
area: methods
related:
- '[[2410.06913--craft]]'
- '[[refusal-aware-instruction-tuning]]'
- '[[supervised-finetuning]]'
- '[[sft-abstention-causes-over-refusal]]'
- '[[over-abstention]]'
- '[[consistency-based-confidence]]'
- '[[truthful-helpfulness-score]]'
relationships:
- type: proposed_by
  target: '[[2410.06913--craft]]'
  target_id: paper:2410.06913
  confidence: high
- type: related_to
  target: '[[refusal-aware-instruction-tuning]]'
  target_id: method:refusal-aware-instruction-tuning
  confidence: medium
- type: related_to
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
  confidence: medium
- type: related_to
  target: '[[sft-abstention-causes-over-refusal]]'
  target_id: mechanism:sft-abstention-causes-over-refusal
  confidence: medium
- type: related_to
  target: '[[over-abstention]]'
  target_id: term:over-abstention
  confidence: medium
- type: related_to
  target: '[[consistency-based-confidence]]'
  target_id: method:consistency-based-confidence
  confidence: medium
- type: related_to
  target: '[[truthful-helpfulness-score]]'
  target_id: metric:truthful-helpfulness-score
  confidence: medium
---

A two-stage RAIT data-construction method that reduces over-refusal by (1) filtering training samples using both response correctness and certainty jointly to reduce static conflict, and (2) running a rehearsal training pass on high-certainty samples to characterize knowledge flow and correct stale IdK labels before the final fine-tune.

**Why it matters here:** CRaFT is a drop-in replacement for Cor-RAIT that does not require preference pairs or a reward model and addresses the two root causes of over-refusal identified in the paper. Its rehearsal training component is directly applicable inside the locked training-regimen SFT arm to reduce the over-abstention cost documented in sft-abstention-causes-over-refusal.

**Lineage:** extends refusal-aware-instruction-tuning; builds on supervised-finetuning; addresses sft-abstention-causes-over-refusal
