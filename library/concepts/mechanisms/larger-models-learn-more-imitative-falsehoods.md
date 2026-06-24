---
aliases:
- inverse scaling on truthfulness
- imitative falsehood inverse scaling
- scale increases imitative falsehoods
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:larger-models-learn-more-imitative-falsehoods
  type: mechanism
  status: canonical
cause: "Increasing model scale improves learning of the training distribution, including its embedded misconceptions and false beliefs."
effect: "Larger models produce more imitative falsehoods, so truthfulness on adversarially constructed benchmarks like TruthfulQA decreases as model size increases within a family."
polarity: decreases
related:
- '[[2109.07958--truthfulqa]]'
- '[[imitative-falsehood]]'
- '[[truthfulqa]]'
- '[[high-capacity-training-degrades-calibration]]'
- '[[dominant-uncertainty-source-shifts-with-model-scale]]'
- '[[model-scale-improves-self-knowledge]]'
relationships:
- type: supported_by
  target: '[[2109.07958--truthfulqa]]'
  target_id: paper:2109.07958
  confidence: high
- type: related_to
  target: '[[imitative-falsehood]]'
  target_id: term:imitative-falsehood
  confidence: high
- type: related_to
  target: '[[truthfulqa]]'
  target_id: dataset:truthfulqa
  confidence: high
- type: related_to
  target: '[[high-capacity-training-degrades-calibration]]'
  target_id: mechanism:high-capacity-training-degrades-calibration
  confidence: high
- type: related_to
  target: '[[dominant-uncertainty-source-shifts-with-model-scale]]'
  target_id: mechanism:dominant-uncertainty-source-shifts-with-model-scale
  confidence: high
- type: related_to
  target: '[[model-scale-improves-self-knowledge]]'
  target_id: mechanism:model-scale-improves-self-knowledge
  confidence: high
---

Lin et al. demonstrate across GPT-3, GPT-Neo/J, and GPT-2 families that larger models are generally less truthful on TruthfulQA than smaller models in the same family. The proposed explanation is that scaling laws cause larger models to better fit the training distribution, and since human text contains many popular misconceptions, better distribution-fitting means more imitative falsehoods. Control experiments (matched questions with 1-3 word edits that convert TruthfulQA items into ordinary trivia) show that larger models improve on controls while worsening on originals, which is inconsistent with a non-imitative syntactic-artifact explanation. The mechanism also transfers across model families: the GPT-Neo/J family shows the same inverse scaling trend despite adversarial filtering being done only with GPT-3.
