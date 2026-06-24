---
aliases:
- MCQ answer uncertainty
- choice-conditional uncertainty
tags:
- kg/term
- concept
- term
kg:
  id: term:answer-uncertainty
  type: term
  status: canonical
area: terms
related:
- '[[2310.11732--calibration-aligned-multiple-choice]]'
- '[[format-uncertainty]]'
- '[[overconfidence]]'
- '[[calibration]]'
- '[[direct-preference-optimization]]'
- '[[supervised-finetuning]]'
- '[[expected-calibration-error]]'
relationships:
- type: proposed_by
  target: '[[2310.11732--calibration-aligned-multiple-choice]]'
  target_id: paper:2310.11732
  confidence: high
- type: related_to
  target: '[[format-uncertainty]]'
  target_id: term:format-uncertainty
  confidence: medium
- type: related_to
  target: '[[overconfidence]]'
  target_id: term:overconfidence
  confidence: medium
- type: related_to
  target: '[[calibration]]'
  target_id: term:calibration
  confidence: medium
- type: related_to
  target: '[[direct-preference-optimization]]'
  target_id: method:direct-preference-optimization
  confidence: medium
- type: related_to
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
  confidence: medium
- type: related_to
  target: '[[expected-calibration-error]]'
  target_id: metric:expected-calibration-error
  confidence: medium
---

In the MCQ setting, the component of a language model's predictive probability that reflects how the model ranks candidate answers given that it will respond in the direct-choice format. Formally, p_LM(choice_i | prompt, F_c) in the He et al. 2023 decomposition (Equation 2). Alignment processes that optimize on answer tokens (SFT-Choice, DPO-Choice) shift this distribution and cause overconfidence.

**Why it matters here:** Alignment that inadvertently corrupts answer uncertainty is the mechanism this paper identifies as the root cause of aligned-LM overconfidence on MCQs, and the reason ICL cannot restore calibration post-alignment.

**Lineage:** Introduced alongside format-uncertainty in He et al. 2023 (arXiv:2310.11732).
