---
aliases:
- Relabeling unfamiliar examples enables abstention
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:answer-relabeling-enables-abstention
  type: mechanism
  status: canonical
cause: Relabeling [[unfamiliar-finetuning-examples]] with 'I don't know' before [[supervised-finetuning]] ([[answer-relabeling]])
effect: Model's default [[hedged-prediction]] becomes an abstaining response, increasing [[selective-classification-auc|selective accuracy]] on unfamiliar queries
polarity: enables
related:
- '[[2403.05612--unfamiliar-finetuning-examples]]'
- '[[unfamiliar-finetuning-examples]]'
- '[[supervised-finetuning]]'
- '[[answer-relabeling]]'
- '[[hedged-prediction]]'
- '[[selective-classification-auc]]'
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
  target: '[[answer-relabeling]]'
  target_id: method:answer-relabeling
- type: related_to
  target: '[[hedged-prediction]]'
  target_id: term:hedged-prediction
- type: related_to
  target: '[[selective-classification-auc]]'
  target_id: metric:selective-classification-auc
---

Because the model learns to mimic the label distribution of unfamiliar training examples, relabeling those examples with abstention responses redirects the default output for unfamiliar queries from hallucinated answers to appropriate uncertainty expressions. This is a lightweight data-curation intervention that does not require changing the training objective or adding a preference optimization stage. The unfamiliar-finetuning paper (arXiv:2403.05612) shows answer relabeling consistently improves selective accuracy on unfamiliar test queries across multiple evaluation settings.
