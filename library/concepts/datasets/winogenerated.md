---
aliases:
- Winogenerated gender bias dataset
- human-AI Winogender extension
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:winogenerated
  type: dataset
  status: canonical
area: datasets
related:
- '[[2212.09251--model-written-evals]]'
- '[[winobias]]'
- '[[reinforcement-learning-from-human-feedback]]'
- '[[model-written-evals]]'
relationships:
- type: proposed_by
  target: '[[2212.09251--model-written-evals]]'
  target_id: paper:2212.09251
  confidence: high
- type: related_to
  target: '[[winobias]]'
  target_id: dataset:winobias
  confidence: medium
- type: related_to
  target: '[[reinforcement-learning-from-human-feedback]]'
  target_id: method:reinforcement-learning-from-human-feedback
  confidence: medium
- type: related_to
  target: '[[model-written-evals]]'
  target_id: method:model-written-evals
  confidence: medium
---

A 3000-example gender bias evaluation dataset created through a hybrid human-AI pipeline by Perez et al. (2022). Each example is a Winogender-style sentence with a masked pronoun referring to a person in an occupation. The dataset is 50 times larger than the original 60-example Winogender set, covers nearly all Bureau of Labor Statistics occupations, and meets five structural validity criteria at 96-100% per crowdworker evaluation.

**Why it matters here:** Provides tighter confidence intervals than Winogender when measuring model gender-occupation stereotype correlation, enabling detection of scaling trends (RLHF reduces stereotype correlation) that Winogender's error bars obscure. Directly used to show RLHF has a measurable positive effect on one dimension of societal bias reinforcement.

**Lineage:** Created by Perez et al. (arXiv 2212.09251) as an extension of Winogender (Rudinger et al., 2018).
