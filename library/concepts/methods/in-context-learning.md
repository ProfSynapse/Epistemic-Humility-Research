---
aliases:
- ICL
- few-shot prompting
- in-context examples
- In-Context Learning
tags:
- kg/method
- concept
- method
kg:
  id: method:in-context-learning
  type: method
  status: canonical
area: methods
related:
- '[[instruction-tuning]]'
relationships:
- type: related_to
  target: '[[instruction-tuning]]'
  target_id: method:instruction-tuning
---

In-context learning is a prompting technique in which a small number of labeled input-output examples are prepended to a query at inference time, enabling the model to adapt its behavior without any weight updates. The model generalizes from the pattern demonstrated in the examples to produce an appropriate response for the new query, using only its pretrained parameters.

**Why it matters here:** Several self-knowledge studies use ICL as a lightweight baseline for eliciting uncertainty expressions and abstention behavior, providing a contrast point against finetuning-based methods like [[idk-sft]]. The finding that [[icl-improves-self-knowledge]] but is outperformed by weight-level training motivates the SFT-vs-DPO-vs-KTO comparison.

**Lineage:** related to [[instruction-tuning]], which is the weight-update analogue; contrasted with [[supervised-finetuning]] for self-knowledge elicitation.
