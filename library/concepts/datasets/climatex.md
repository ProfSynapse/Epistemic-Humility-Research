---
aliases:
- Expert Confidence in Climate Statements
- ClimateX dataset
- IPCC AR6 confidence corpus
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:climatex
  type: dataset
  status: canonical
area: datasets
related:
- '[[2508.15050--dont-think-twice]]'
- '[[iarc-carcinogenicity]]'
- '[[masked-label-calibration-probe]]'
- '[[cohens-kappa]]'
- '[[calibration]]'
- '[[overconfidence]]'
relationships:
- type: proposed_by
  target: '[[2508.15050--dont-think-twice]]'
  target_id: paper:2508.15050
  confidence: high
- type: related_to
  target: '[[iarc-carcinogenicity]]'
  target_id: dataset:iarc-carcinogenicity
  confidence: medium
- type: related_to
  target: '[[masked-label-calibration-probe]]'
  target_id: method:masked-label-calibration-probe
  confidence: medium
- type: related_to
  target: '[[cohens-kappa]]'
  target_id: metric:cohens-kappa
  confidence: medium
- type: related_to
  target: '[[calibration]]'
  target_id: term:calibration
  confidence: medium
- type: related_to
  target: '[[overconfidence]]'
  target_id: term:overconfidence
  confidence: medium
---

A curated expert-labeled natural language dataset of 8,094 statements drawn from the three most recent IPCC AR6 volumes (Working Groups I, II, III), each annotated with the consensus human expert confidence level on a 5-level categorical scale (very low through very high confidence). The dataset provides a masked-label classification benchmark for evaluating LLM calibration to human expert confidence. The test split contains 300 randomly selected statements; the remaining 7,794 form the train split.

**Why it matters here:** ClimateX is one of the few benchmarks where the ground-truth labels represent a consensus of domain scientists rather than crowd workers or model outputs. It provides an externally valid, training-contamination-free calibration probe for knowledge-intensive tasks, and the gap between fine-tuned encoder (53.7%) and frontier LLM (48.7%) performance shows the task remains genuinely open.

**Lineage:** Introduced by Lacombe et al. (2023b, HuggingFace: rlacombe/ClimateX). Extended in this paper (arXiv:2508.15050) to benchmark reasoning models and test-time scaling.
