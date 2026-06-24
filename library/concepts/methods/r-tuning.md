---
aliases:
- R-Tuning-U
- Refusal Tuning
- uncertainty-based refusal tuning
tags:
- kg/method
- concept
- method
kg:
  id: method:r-tuning
  type: method
  status: canonical
area: methods
related:
- '[[2410.17234--semantic-entropy-abstention]]'
- '[[supervised-finetuning]]'
- '[[semantic-entropy]]'
- '[[idk-sft]]'
- '[[answer-relabeling]]'
- '[[lexical-entropy-overestimates-uncertainty-under-paraphrase]]'
relationships:
- type: proposed_by
  target: '[[2410.17234--semantic-entropy-abstention]]'
  target_id: paper:2410.17234
  confidence: high
- type: related_to
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
  confidence: medium
- type: related_to
  target: '[[semantic-entropy]]'
  target_id: method:semantic-entropy
  confidence: medium
- type: related_to
  target: '[[idk-sft]]'
  target_id: method:idk-sft
  confidence: medium
- type: related_to
  target: '[[answer-relabeling]]'
  target_id: method:answer-relabeling
  confidence: medium
- type: related_to
  target: '[[lexical-entropy-overestimates-uncertainty-under-paraphrase]]'
  target_id: mechanism:lexical-entropy-overestimates-uncertainty-under-paraphrase
  confidence: medium
---

A family of supervised fine-tuning methods for abstention (Zhang et al. 2024). R-Tuning uses ground-truth correctness labels to partition training questions into known (answer) and unknown (abstain) sets, then fine-tunes the model with the abstention phrase replacing labels for incorrect questions. R-Tuning-U is the label-free variant: it samples M responses, estimates classical conditional entropy over the token-sequence distribution, and partitions questions by entropy into the top-50% uncertain (abstain) and bottom-50% confident (answer) sets. Both use supervised fine-tuning with cross-entropy loss and the phrase 'I don't know' as the abstention label.

**Why it matters here:** The primary baseline for SE-based abstention fine-tuning. R-Tuning-U's reliance on token-level entropy makes it sensitive to lexical/syntactic variation and limits it to short-form generation settings; SE overcomes this. R-Tuning requires ground-truth labels unavailable in many deployment settings.

**Lineage:** Proposed by Zhang et al. (arXiv:2311.09677, 2024). R-Tuning-U is the label-free variant in the same paper, extending R-Tuning to uncertainty-based partitioning.
