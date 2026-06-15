---
aliases:
- HH
- Anthropic HH-RLHF
- HH-RLHF
- Anthropic HH (Helpfulness and Harmlessness dataset)
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:anthropic-hh
  type: dataset
  status: canonical
area: datasets
---

The Anthropic HH-RLHF dataset contains human-annotated [[preference-pair-data]] collected through conversations with Claude, covering both helpfulness and harmlessness dimensions. Annotators chose the better of two assistant responses for each prompt, producing chosen/rejected pairs used for reward modelling and policy training.

**Why it matters here:** The KTO paper uses Anthropic HH as one of three training sets (alongside OpenAssistant and SHP) to evaluate [[human-aware-loss-functions]] methods, so it anchors empirical comparisons between [[kahneman-tversky-optimization]] and [[direct-preference-optimization]] on helpfulness/harmlessness tasks adjacent to abstention and honesty.

**Lineage:** provides [[preference-pair-data]] for [[reinforcement-learning-from-human-feedback]] and downstream contrastive methods.
