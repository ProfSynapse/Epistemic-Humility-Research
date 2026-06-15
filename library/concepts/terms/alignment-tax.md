---
aliases:
- performance regression from alignment
- honesty tax
- helpfulness cost of alignment
tags:
- kg/term
- concept
- term
kg:
  id: term:alignment-tax
  type: term
  status: canonical
area: terms
---

The alignment tax is the performance degradation on public NLP benchmarks (e.g., SQuAD, DROP, HellaSwag, WMT) that results from RLHF fine-tuning on a task-specific prompt distribution. The model becomes better at following instructions and producing helpful responses on the target distribution but loses breadth on benchmarks outside that distribution, because RLHF updates push the policy away from the broad pretraining distribution.

**Why it matters here:** InstructGPT shows the alignment tax can be largely mitigated by mixing pretraining gradients into PPO updates (the PPO-ptx variant), and the alignment-for-honesty literature studies an analogous trade-off: teaching models to abstain or express uncertainty may degrade general task performance, making the tax a key practical concern for the SFT-vs-DPO-vs-KTO abstention study.

**Lineage:** closely related to [[over-hedging]] (one specific tax symptom) and studied in [[reinforcement-learning-from-human-feedback]] pipelines.
