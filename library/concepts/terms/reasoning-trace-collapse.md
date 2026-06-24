---
aliases:
- trace collapse
- explicit reasoning collapse
- VR collapse
tags:
- kg/term
- concept
- term
kg:
  id: term:reasoning-trace-collapse
  type: term
  status: canonical
area: terms
related:
- '[[2605.21127--silent-reasoning-trace-suppression]]'
- '[[valid-reasoning-rate]]'
- '[[supervised-finetuning]]'
- '[[instruction-tuning]]'
- '[[reasoning-fine-tuning]]'
- '[[sft-suppresses-honesty-expression]]'
relationships:
- type: proposed_by
  target: '[[2605.21127--silent-reasoning-trace-suppression]]'
  target_id: paper:2605.21127
  confidence: high
- type: related_to
  target: '[[valid-reasoning-rate]]'
  target_id: metric:valid-reasoning-rate
  confidence: medium
- type: related_to
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
  confidence: medium
- type: related_to
  target: '[[instruction-tuning]]'
  target_id: method:instruction-tuning
  confidence: medium
- type: related_to
  target: '[[reasoning-fine-tuning]]'
  target_id: method:reasoning-fine-tuning
  confidence: medium
- type: related_to
  target: '[[sft-suppresses-honesty-expression]]'
  target_id: mechanism:sft-suppresses-honesty-expression
  confidence: medium
---

The progressive loss of a model's ability to produce structurally valid, complete, non-empty reasoning traces during fine-tuning, even when final-answer performance is maintained or improves. Formally: given output y=(r,a), collapse occurs when r is no longer reliably present in valid form even if a remains correct.

**Why it matters here:** Reasoning-trace collapse is invisible to answer-only metrics (pass@1, accuracy) and creates a false impression that the model remains a functioning reasoning model after adaptation. Detecting it requires structural metrics like VR and Rpass@1.

**Lineage:** Defined and formalized in Twist et al. 2026 (arXiv:2605.21127), Section 3.
