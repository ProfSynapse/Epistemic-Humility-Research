---
aliases:
- Unanswerable Math Word Problem
- UMWP dataset
- Unanswerable MWP benchmark
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:umwp
  type: dataset
  status: canonical
area: datasets
related:
- '[[2403.03558--umwp-unanswerable-math]]'
- '[[gsm8k]]'
- '[[selfaware]]'
- '[[hallucination]]'
- '[[abstention]]'
- '[[self-knowledge-f1]]'
- '[[unanswerable-questions]]'
- '[[uncertainty-detection-simcse]]'
relationships:
- type: proposed_by
  target: '[[2403.03558--umwp-unanswerable-math]]'
  target_id: paper:2403.03558
  confidence: high
- type: related_to
  target: '[[gsm8k]]'
  target_id: dataset:gsm8k
  confidence: medium
- type: related_to
  target: '[[selfaware]]'
  target_id: dataset:selfaware
  confidence: medium
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
  confidence: medium
- type: related_to
  target: '[[abstention]]'
  target_id: term:abstention
  confidence: medium
- type: related_to
  target: '[[self-knowledge-f1]]'
  target_id: metric:self-knowledge-f1
  confidence: medium
- type: related_to
  target: '[[unanswerable-questions]]'
  target_id: term:unanswerable-questions
  confidence: medium
- type: related_to
  target: '[[uncertainty-detection-simcse]]'
  target_id: method:uncertainty-detection-simcse
  confidence: medium
---

A 5,200-question benchmark for evaluating hallucination in LLMs via mathematical unanswerability. Questions are split evenly between 2,600 answerable problems (from GSM8K, SVAMP, MultiArith, and ASDiv) and 2,600 unanswerable modifications annotated by human annotators and validated by three volunteers. Unanswerable questions span five categories: Key Information Missing (32%), Ambiguous Key Information (49%), Unrealistic Conditions (11%), Unrelated Object (4%), and Question Missing (5%). Evaluation uses a combined SimCSE template-similarity and variable-expression detection pipeline scored by F1 treating unanswerable as positive.

**Why it matters here:** UMWP provides a knowledge-independent abstention signal: because math problems require computation rather than fact recall, hallucination cannot be attributed to memorized world knowledge. It also yields the finding that RLHF is the dominant driver of abstention quality over scale, directly bearing on Phase 1 training comparison.

**Lineage:** Built on top of gsm8k, selfaware (for evaluator design), and the SelfAware similarity threshold (Yin et al. 2023); introduced in arXiv:2403.03558.
