---
aliases:
- Factuality Tuning MC
- model-confidence factuality tuning
- reference-free factuality tuning via DPO
tags:
- kg/method
- concept
- method
kg:
  id: method:facttune-mc
  type: method
  status: canonical
area: methods
related:
- '[[2311.08401--finetuning-for-factuality]]'
- '[[direct-preference-optimization]]'
- '[[consistency-based-confidence]]'
- '[[max-confidence-scoring]]'
- '[[facttune-fs]]'
- '[[hallucination]]'
- '[[factscore]]'
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
  target: '[[consistency-based-confidence]]'
  target_id: method:consistency-based-confidence
  confidence: medium
- type: related_to
  target: '[[max-confidence-scoring]]'
  target_id: method:max-confidence-scoring
  confidence: medium
- type: related_to
  target: '[[facttune-fs]]'
  target_id: method:facttune-fs
  confidence: medium
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
  confidence: medium
- type: related_to
  target: '[[factscore]]'
  target_id: metric:factscore
  confidence: medium
---

A two-stage pipeline that constructs factuality preference pairs without any external knowledge source: atomic claims are extracted from completions, rephrased as minimally ambiguous questions, and answered 20 times by sampling from Llama-1-7B (fixed as the confidence oracle regardless of the target model being tuned). Answers are binned by heuristic string equivalence and the fraction in the largest bin (max-confidence) is used as the per-fact truthfulness score. Preference pairs are fed to DPO. The method is fully reference-free at both training and test time.

**Why it matters here:** Proves that self-consistency-based confidence (max-confidence over resampled answers) is a sufficient signal for DPO-based factuality fine-tuning, removing the retrieval dependency of FactTune-FS. The fixed Llama-1-7B oracle detail is mechanistically important for interpreting what signal the trained model internalizes.

**Lineage:** Builds on direct-preference-optimization and consistency-based-confidence; inspired by Kuhn et al. 2023 (semantic entropy); counterpart to facttune-fs.
