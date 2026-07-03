---
aliases:
- SmolLM2 training data
- SmolTalk Dataset
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:smoltalk
  type: dataset
  status: canonical
area: datasets
related: []
relationships: []
---

SmolTalk is an instruction-labeled dialog dataset released under the Apache 2.0 license as part of the SmolLM2 model family (Allal et al. 2025). In multi-behavior steering research it serves as a large pool of diverse natural prompts: 50k prompts per behavior are drawn from it to generate training trajectories (answered by a capable instruction-tuned model), and 1,000 held-out prompts per composition are reserved for evaluation, yielding over one million evaluations per model across all behavior combinations and orderings. Its breadth and permissive license make it well suited as a neutral prompt source that is unlikely to overlap with the fine-tuning data of the models under study.

**Why it matters here:** As a generic instruction prompt pool, SmolTalk allows steering experiments to be evaluated on the full distribution of natural user requests rather than narrow task-specific datasets, making generalization claims more credible.

**Lineage:** a standalone dataset; no direct methodological lineage.
