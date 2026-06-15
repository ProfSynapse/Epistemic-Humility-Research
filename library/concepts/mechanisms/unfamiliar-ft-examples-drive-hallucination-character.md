---
aliases:
- Unfamiliar finetuning examples shape hallucination character
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:unfamiliar-ft-examples-drive-hallucination-character
  type: mechanism
  status: canonical
cause: Supervising [[unfamiliar-finetuning-examples]] with ground-truth labels in [[supervised-finetuning]]
effect: Model's default [[hedged-prediction]] mirrors ground-truth label distribution, causing hallucinated plausible-sounding answers on unfamiliar test queries
polarity: increases
related:
- '[[2403.05612--unfamiliar-finetuning-examples]]'
- '[[unfamiliar-finetuning-examples]]'
- '[[supervised-finetuning]]'
- '[[hedged-prediction]]'
relationships:
- type: supported_by
  target: '[[2403.05612--unfamiliar-finetuning-examples]]'
  target_id: paper:2403.05612
  confidence: high
- type: related_to
  target: '[[unfamiliar-finetuning-examples]]'
  target_id: term:unfamiliar-finetuning-examples
- type: related_to
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
- type: related_to
  target: '[[hedged-prediction]]'
  target_id: term:hedged-prediction
---

When a model is trained on unfamiliar examples with ground-truth answer labels, it learns to associate the surface features of unfamiliar questions with the distribution of those training labels. At inference time on unfamiliar test queries, the model's default output mimics this learned distribution, producing confident-sounding answers that reflect training data statistics rather than genuine knowledge. The unfamiliar-finetuning paper (arXiv:2403.05612) demonstrates this by showing that the character of hallucinated answers tracks the label distribution of unfamiliar training examples.
