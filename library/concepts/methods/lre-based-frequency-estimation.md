---
aliases:
- frequency regression from LRE features
- LRE frequency regression
- pretraining data frequency estimation
- LRE-Based Pretraining Frequency Estimation
tags:
- kg/method
- concept
- method
kg:
  id: method:lre-based-frequency-estimation
  type: method
  status: canonical
area: mechanistic-interpretability
related:
- '[[2504.12459--linear-representations-pretraining-data-frequency-language-models]]'
- '[[linear-relation-embedding]]'
- '[[lre-faithfulness]]'
- '[[lre-causality]]'
- '[[within-magnitude-accuracy]]'
relationships:
- type: proposed_by
  target: '[[2504.12459--linear-representations-pretraining-data-frequency-language-models]]'
  target_id: paper:2504.12459
  confidence: high
- type: derived_from
  target: '[[linear-relation-embedding]]'
  target_id: method:linear-relation-embedding
---

LRE-based frequency estimation is a random-forest regression method that takes LRE quality features (causality, faithfulness, faith probability, and hard causality) extracted from one language model and trains a regressor to predict how often a subject-object pair appeared in the pretraining corpus of a separate, closed-data language model. The method enables non-invasive probing of otherwise-unknown training data composition by treating the linear geometry of a model's factual representations as an indirect readout of its data diet. Because LRE features generalize across models, the regressor trained on one model can transfer partial signal to another.

**Why it matters here:** Estimating pretraining frequency without direct corpus access is one route to measuring a model's knowledge boundary from the outside, which is a prerequisite for externally auditing whether a model's epistemic humility (abstention rate, confidence calibration) is calibrated to its actual knowledge gaps.

**Lineage:** derives from [[linear-relation-embedding]]; uses [[lre-faithfulness]] and [[lre-causality]] as input features; evaluated via [[within-magnitude-accuracy]].
