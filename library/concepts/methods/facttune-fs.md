---
aliases:
- Factuality Tuning FS
- FactScore-based factuality tuning
- reference-based factuality tuning via DPO
tags:
- kg/method
- concept
- method
kg:
  id: method:facttune-fs
  type: method
  status: canonical
area: methods
related:
- '[[2311.08401--finetuning-for-factuality]]'
- '[[direct-preference-optimization]]'
- '[[factscore]]'
- '[[supervised-finetuning]]'
- '[[reinforcement-learning-from-human-feedback]]'
- '[[facttune-mc]]'
- '[[hallucination]]'
relationships:
- type: proposed_by
  target: '[[2311.08401--finetuning-for-factuality]]'
  target_id: paper:2311.08401
  confidence: high
- type: related_to
  target: '[[direct-preference-optimization]]'
  target_id: method:direct-preference-optimization
  confidence: medium
- type: related_to
  target: '[[factscore]]'
  target_id: metric:factscore
  confidence: medium
- type: related_to
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
  confidence: medium
- type: related_to
  target: '[[reinforcement-learning-from-human-feedback]]'
  target_id: method:reinforcement-learning-from-human-feedback
  confidence: medium
- type: related_to
  target: '[[facttune-mc]]'
  target_id: method:facttune-mc
  confidence: medium
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
  confidence: medium
---

A two-stage pipeline that (1) scores sampled completions using FactScore (atomic claim decomposition followed by Wikipedia-grounded verification) to construct ranked preference pairs, then (2) fine-tunes the language model on those pairs with DPO. No human annotation is required; the only external dependency is a retrieval corpus (Wikipedia) and an atomic-claim checker. FactTune-FS is the reference-based variant of the FactTune family.

**Why it matters here:** Establishes the strongest factuality gains in the paper (58% error-rate reduction on biographies vs Llama-2-Chat), serves as the primary empirical comparator for the reference-free FactTune-MC, and is the method closest in spirit to using automated preference construction for epistemic alignment in the locked training-regimen study.

**Lineage:** Builds on direct-preference-optimization (Rafailov et al. 2023) and factscore (Min et al. 2023); counterpart to facttune-mc.
