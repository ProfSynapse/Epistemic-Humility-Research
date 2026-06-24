---
aliases:
- masked confidence label prediction
- label-masked classification task
- masked expert confidence prediction
tags:
- kg/method
- concept
- method
kg:
  id: method:masked-label-calibration-probe
  type: method
  status: canonical
area: methods
related:
- '[[2508.15050--dont-think-twice]]'
- '[[climatex]]'
- '[[iarc-carcinogenicity]]'
- '[[cohens-kappa]]'
- '[[verbalized-confidence]]'
- '[[calibration]]'
relationships:
- type: proposed_by
  target: '[[2508.15050--dont-think-twice]]'
  target_id: paper:2508.15050
  confidence: high
- type: related_to
  target: '[[climatex]]'
  target_id: dataset:climatex
  confidence: medium
- type: related_to
  target: '[[iarc-carcinogenicity]]'
  target_id: dataset:iarc-carcinogenicity
  confidence: medium
- type: related_to
  target: '[[cohens-kappa]]'
  target_id: metric:cohens-kappa
  confidence: medium
- type: related_to
  target: '[[verbalized-confidence]]'
  target_id: method:verbalized-confidence
  confidence: medium
- type: related_to
  target: '[[calibration]]'
  target_id: term:calibration
  confidence: medium
---

An evaluation method for LLM calibration in which a statement is presented with its expert-assigned confidence label removed, and the model is asked to reconstruct the correct label. The framing tests whether the model has internalized the same confidence distribution that domain experts applied, without the model being able to copy the label verbatim. Performance is measured by accuracy and Cohen's kappa against the held-out ground-truth labels.

**Why it matters here:** Unlike prompting a model to verbalize its own uncertainty about a generated answer, the masked-label probe tests calibration to an externally defined expert consensus. It sidesteps the conflation of knowledge recall with confidence expression and can be applied to any dataset with systematic expert labels (climate confidence, carcinogenicity hazard, etc.).

**Lineage:** Applied by Lacombe et al. (2023a) on ClimateX; extended to reasoning and search-augmented models in arXiv:2508.15050.
