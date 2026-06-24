---
aliases:
- automated feature interpretability scoring
- LLM-based interpretability evaluation
tags:
- kg/method
- concept
- method
kg:
  id: method:automated-interpretability
  type: method
  status: canonical
area: mechanistic-interpretability
related:
- '[[tc2023--towards-monosemanticity]]'
- '[[sparse-autoencoder]]'
- '[[llm-as-judge]]'
relationships:
- type: proposed_by
  target: '[[tc2023--towards-monosemanticity]]'
  target_id: paper:tc2023
  confidence: high
- type: related_to
  target: '[[sparse-autoencoder]]'
  target_id: method:sparse-autoencoder
- type: related_to
  target: '[[llm-as-judge]]'
  target_id: method:llm-as-judge
---

Automated interpretability is a scalable evaluation pipeline in which a large language model generates natural-language explanations for each sparse autoencoder feature's activation pattern, then predicts activations or logit effects on held-out examples without access to actual activation values. The accuracy of these predictions serves as a proxy metric for how interpretable a feature is. In the work that introduced this pipeline, it yielded 74% prediction accuracy for SAE features versus 58% for raw neurons on logit-weight prediction tasks, quantifying the interpretability gain from dictionary learning.

**Why it matters here:** Automated interpretability offers a path toward scalable auditing of what internal features a model relies on when it expresses confidence or abstains, without requiring costly human annotation of every feature at scale.

**Lineage:** introduced in [[tc2023--towards-monosemanticity]] as an evaluation companion to the [[sparse-autoencoder]] pipeline; related to [[llm-as-judge]] frameworks more broadly used in alignment evaluation.
