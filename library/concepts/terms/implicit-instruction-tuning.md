---
aliases:
- Implicit instruction tuning
tags:
- kg/term
- concept
- term
kg:
  id: term:implicit-instruction-tuning
  type: term
  status: canonical
area: terms
related:
- '[[2409.14254--instruction-following-without-instruction-tuning]]'
- '[[response-tuning]]'
- '[[single-task-finetuning]]'
- '[[instruction-tuning]]'
relationships:
- type: proposed_by
  target: '[[2409.14254--instruction-following-without-instruction-tuning]]'
  target_id: paper:2409.14254
  confidence: high
- type: related_to
  target: '[[response-tuning]]'
  target_id: method:response-tuning
  confidence: high
- type: related_to
  target: '[[single-task-finetuning]]'
  target_id: method:single-task-finetuning
  confidence: high
- type: related_to
  target: '[[instruction-tuning]]'
  target_id: method:instruction-tuning
  confidence: high
---

Hewitt et al. (2024) name "implicit instruction tuning" the finding that forms of adaptation deficient compared to standard instruction tuning (no paired instructions, or fine-tuning only on a single narrow task) nonetheless yield broad instruction-following behavior. This happens without the adaptation being designed to teach instruction following at all.

**Why it matters here:** implicit instruction tuning shows that broad instruction-following capability can emerge as a side effect of narrow or even instruction-free fine-tuning, which cautions against attributing a trained model's general behavioral shift specifically to the training objective's intended target; the same caution applies to interpreting abstention-specific training (SFT/DPO/KTO) as necessarily teaching abstention in particular, rather than surfacing a broader latent capability via any sufficiently strong distributional nudge.
