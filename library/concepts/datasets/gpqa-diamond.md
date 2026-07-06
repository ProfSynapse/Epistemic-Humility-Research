---
aliases:
- GPQA-D
- GPQA-Diamond
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:gpqa-diamond
  type: dataset
  status: canonical
area: benchmarks
related: []
relationships: []
---

GPQA-Diamond is a hard subset of the Graduate-Level Google-Proof Q&A benchmark containing 198 multiple-choice questions in biology, chemistry, and physics that require genuine graduate-level expertise to answer correctly. Its questions are designed so that domain experts write items only other field specialists can reliably solve, and even non-experts with full web access score near chance. The Diamond tier selects the hardest items from the full [[gpqa]] collection, making it a reliable test of substantive multi-hop reasoning rather than surface recall. Each question therefore functions as a probe of whether a model has deeply structured knowledge versus pattern-matched familiarity.

**Why it matters here:** Because GPQA-Diamond demands authentic reasoning under genuine uncertainty, it reveals miscalibrated confidence more starkly than easier benchmarks: a model that produces fluent but wrong reasoning chains on graduate-level questions is exhibiting the overconfident hallucination pattern central to epistemic humility research.

**Lineage:** none.
