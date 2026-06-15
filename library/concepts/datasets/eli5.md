---
aliases:
- ELI5 dataset
- Explain Like I'm 5
- Long Form Question Answering
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:eli5
  type: dataset
  status: canonical
area: datasets-benchmarks
---

ELI5 (Explain Like I'm 5) is a long-form question answering dataset collected from the Reddit community r/explainlikeimfive, consisting of questions that have clear, definitive answers accompanied by detailed natural-language explanations. Questions are open-domain but answerable, making them a natural "known question" baseline. In the KUQ study it serves as the foil corpus against which semantically unknown questions are contrasted, establishing the expected linguistic register of a model that is confident and correct.

**Why it matters here:** As the "known" half of the [[known-unknown-questions]] evaluation design, ELI5 anchors the [[answer-uncertainty-disparity]] calculation, providing the upper reference distribution for model confidence when the answer is within reach.

**Lineage:** used by [[2305.13712--kuq-knowledge-of-knowledge]] as the known-question baseline in the KUQ benchmark construction.
