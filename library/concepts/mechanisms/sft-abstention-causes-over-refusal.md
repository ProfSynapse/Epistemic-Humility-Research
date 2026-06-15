---
aliases:
- SFT abstention training causes over-refusal of known questions
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:sft-abstention-causes-over-refusal
  type: mechanism
  status: canonical
cause: '[[supervised-finetuning]] on the [[idk-dataset]] to teach [[abstention]]'
effect: Model becomes overly conservative, incorrectly refusing questions it actually knows (increased Idk-Ik rate, decreased Ik-Ik rate)
polarity: increases
related:
- '[[2401.13275--can-ai-assistants-know-what-they-dont-know]]'
- '[[supervised-finetuning]]'
- '[[idk-dataset]]'
- '[[abstention]]'
relationships:
- type: supported_by
  target: '[[2401.13275--can-ai-assistants-know-what-they-dont-know]]'
  target_id: paper:2401.13275
  confidence: high
- type: related_to
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
- type: related_to
  target: '[[idk-dataset]]'
  target_id: dataset:idk-dataset
- type: related_to
  target: '[[abstention]]'
  target_id: term:abstention
---

SFT on abstention examples trains the model to recognize uncertainty signals, but without a contrastive signal for questions the model does know, the model generalizes the abstention behavior too broadly. The result is a calibration failure in the direction of [[over-abstention]]: the model refuses answerable questions at elevated rates. The can-ai-assistants paper (arXiv:2401.13275) quantifies this as an increased Idk-Ik rate and motivates preference optimization as a corrective stage after SFT warming.
