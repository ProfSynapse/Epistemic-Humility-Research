---
aliases:
- R-Tuning
- Refusal-Aware Instruction Tuning
- refusal-aware finetuning
- R-Tuning (Refusal-Aware Instruction Tuning)
- Refusal-aware Tuning
- refusal-aware dataset finetuning
- r tuning
- RAIT
- Refusal-Aware Instruction Tuning (RAIT)
tags:
- kg/method
- concept
- method
kg:
  id: method:refusal-aware-instruction-tuning
  type: method
  status: canonical
area: methods
related:
- '[[2311.09677--r-tuning-say-i-dont-know]]'
- '[[supervised-finetuning]]'
- '[[knowledge-boundary]]'
relationships:
- type: proposed_by
  target: '[[2311.09677--r-tuning-say-i-dont-know]]'
  target_id: paper:2311.09677
  confidence: high
- type: derived_from
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
- type: related_to
  target: '[[knowledge-boundary]]'
  target_id: term:knowledge-boundary
---

Refusal-Aware Instruction Tuning (R-Tuning / RAIT) is a supervised fine-tuning method that calibrates a model's abstention to its parametric knowledge. It works in two steps: first, run inference on the training set and compare predictions to labels to split examples into a certain subset (D1, where the model already answers correctly) and an uncertain subset (D0, where it does not); second, append explicit uncertainty expressions to D0 answers so the fine-tuned model learns to say "I don't know" precisely where its knowledge is insufficient.

**Why it matters here:** RAIT is a strong SFT baseline for knowledge-boundary-aware abstention and anchors the knowledge-gap framing that the locked training-regimen SFT arm builds on; its one-pass knowledge-gap detection procedure is directly comparable to how the experiment identifies training examples to label as "unknown."

**Lineage:** extends [[supervised-finetuning]]; tightly coupled to [[knowledge-boundary]] as the concept it operationalizes.
