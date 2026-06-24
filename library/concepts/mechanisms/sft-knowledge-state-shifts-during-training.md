---
aliases:
- dynamic conflict in RAIT
- knowledge flow during SFT
- RAIT dynamic conflict
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:sft-knowledge-state-shifts-during-training
  type: mechanism
  status: canonical
cause: "Supervised fine-tuning causes the model's internal knowledge state to evolve, turning some initially-unknown questions into answerable ones"
effect: "Training targets constructed from the initial knowledge state remain as IdK labels for now-answerable samples, creating contradictory supervision that increases over-refusal"
polarity: increases
related:
- '[[2410.06913--craft]]'
- '[[sft-abstention-causes-over-refusal]]'
- '[[craft]]'
- '[[rehearsal-training]]'
- '[[refusal-aware-instruction-tuning]]'
- '[[supervised-finetuning]]'
- '[[over-abstention]]'
relationships:
- type: supported_by
  target: '[[2410.06913--craft]]'
  target_id: paper:2410.06913
  confidence: high
- type: related_to
  target: '[[sft-abstention-causes-over-refusal]]'
  target_id: mechanism:sft-abstention-causes-over-refusal
  confidence: high
- type: related_to
  target: '[[craft]]'
  target_id: method:craft
  confidence: high
- type: related_to
  target: '[[rehearsal-training]]'
  target_id: method:rehearsal-training
  confidence: high
- type: related_to
  target: '[[refusal-aware-instruction-tuning]]'
  target_id: method:refusal-aware-instruction-tuning
  confidence: high
- type: related_to
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
  confidence: high
- type: related_to
  target: '[[over-abstention]]'
  target_id: term:over-abstention
  confidence: high
---

RAIT data construction stamps each sample's label based on the initial model's correctness at the time of dataset creation. During subsequent SFT, the model's knowledge state is not static: Ren et al. (2024) and related work show that questions shift between known and unknown categories as weights update. When a previously-unknown sample becomes answerable mid-training but still carries an IdK target label, the model receives conflicting gradients that push it toward refusing a question it can now answer correctly. CRaFT quantifies this via rehearsal training and finds that 69% of initially-below-0.5-correctness MMLU samples improve during the rehearsal pass, directly validating the mechanism.
