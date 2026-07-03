---
aliases:
- LRE features improve pretraining frequency estimation over log-prob baselines
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:lre-features-improve-frequency-estimation
  type: mechanism
  status: canonical
cause: "Including [[linear-relation-embedding|LRE quality metrics]] (causality, [[lre-faithfulness|faithfulness]]) as regression features alongside log-probability baselines when estimating pretraining co-occurrence frequency"
effect: "Increased [[within-magnitude-accuracy]] of pretraining frequency estimates across multiple model families compared to log-probability-only baselines"
polarity: increases
related:
- '[[2504.12459--linear-representations-pretraining-data-frequency-language-models]]'
- '[[linear-relation-embedding]]'
- '[[lre-faithfulness]]'
- '[[lre-based-frequency-estimation]]'
- '[[within-magnitude-accuracy]]'
relationships:
- type: supported_by
  target: '[[2504.12459--linear-representations-pretraining-data-frequency-language-models]]'
  target_id: paper:2504.12459
  confidence: high
- type: related_to
  target: '[[linear-relation-embedding]]'
  target_id: method:linear-relation-embedding
- type: related_to
  target: '[[lre-faithfulness]]'
  target_id: metric:lre-faithfulness
- type: related_to
  target: '[[lre-based-frequency-estimation]]'
  target_id: method:lre-based-frequency-estimation
---

Log-probabilities provide noisy proxies for pretraining frequency because they conflate the frequency of a fact with its linguistic salience and the model's generalisation. LRE quality metrics capture a distinct signal: whether the model has internalised the subject-to-object mapping as a reliable linear transformation. Combining LRE causality and faithfulness scores with log-probability features in a regression model improves within-magnitude accuracy of frequency estimation across model families (arXiv:2504.12459). This demonstrates that the structural properties of internal representations carry information about training data frequency that surface probabilities do not fully encode.
