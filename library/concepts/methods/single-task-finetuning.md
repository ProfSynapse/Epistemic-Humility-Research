---
aliases:
- Narrow-domain fine-tuning
- Single-task finetuning
tags:
- kg/method
- concept
- method
kg:
  id: method:single-task-finetuning
  type: method
  status: canonical
area: methods
related:
- '[[2409.14254--instruction-following-without-instruction-tuning]]'
- '[[implicit-instruction-tuning]]'
- '[[supervised-finetuning]]'
relationships:
- type: proposed_by
  target: '[[2409.14254--instruction-following-without-instruction-tuning]]'
  target_id: paper:2409.14254
  confidence: high
- type: related_to
  target: '[[implicit-instruction-tuning]]'
  target_id: term:implicit-instruction-tuning
  confidence: high
- type: related_to
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
  confidence: high
---

Fine-tuning a base model on a single narrow task's input-output distribution (e.g. only Python code from short requests, only math-word-problem derivations, only poems from titles, only recipes from dish names, only chess games from Elo ratings), using the same instruction-tuning-style formatting but with a task-restricted data distribution rather than a broad, diverse instruction set.

**Why it matters here:** single-task finetuning is a stricter test than [[response-tuning]] of whether narrow, non-instruction-following-targeted adaptation nonetheless produces broad instruction-following behavior (see [[narrow-domain-finetuning-yields-broad-instruction-following]]). It bears on how much credit any specific training recipe (SFT, DPO, KTO on abstention data) deserves for the general behavioral changes it produces, versus a broader "any strong enough fine-tuning nudge does this" explanation.
