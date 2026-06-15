---
aliases:
- preference pairs
- pairwise preference data
- chosen-rejected pairs
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:preference-pair-data
  type: dataset
  status: canonical
area: datasets
---

A preference-pair dataset consists of (prompt, chosen response, rejected response) triples, where the ranking between the two responses is supplied by human annotators or an AI oracle. The triples are used to train a reward model in the standard RLHF pipeline, or to directly optimize a policy with contrastive objectives like [[direct-preference-optimization]].

**Why it matters here:** [[direct-preference-optimization]] and related contrastive methods require paired signals, while [[kahneman-tversky-optimization]] was designed to drop this requirement and work from unpaired binary feedback. That distinction is central to comparing the three training arms (SFT vs DPO vs KTO) in the abstention study.

**Lineage:** consumed by [[direct-preference-optimization]] and implicitly by [[reinforcement-learning-from-human-feedback]]; [[kahneman-tversky-optimization]] relaxes the paired-signal constraint.
