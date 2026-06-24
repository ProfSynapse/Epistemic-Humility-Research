---
aliases:
- CRAG
- Comprehensive RAG Benchmark
- Comprehensive Retrieval-Augmented Generation benchmark
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:crag
  type: dataset
  status: canonical
area: datasets
related:
- '[[2509.25760--truthrl-incentivizing-truthful-llms]]'
- '[[truthrl]]'
- '[[knowledge-boundary]]'
- '[[hallucination]]'
- '[[abstention]]'
relationships:
- type: proposed_by
  target: '[[2509.25760--truthrl-incentivizing-truthful-llms]]'
  target_id: paper:2509.25760
  confidence: high
- type: related_to
  target: '[[truthrl]]'
  target_id: method:truthrl
  confidence: medium
- type: related_to
  target: '[[knowledge-boundary]]'
  target_id: term:knowledge-boundary
  confidence: medium
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
  confidence: medium
- type: related_to
  target: '[[abstention]]'
  target_id: term:abstention
  confidence: medium
---

A knowledge-intensive question-answering benchmark covering multiple domains, designed to evaluate models under both retrieval-augmented and closed-book settings; includes comparison-type (hallucination-baiting) and difficult (out-of-knowledge) question subsets. Training data is drawn from CRAG and evaluation covers CRAG plus three held-out benchmarks.

**Why it matters here:** The primary training and evaluation benchmark for TruthRL; its comparison-type questions specifically stress-test robustness to hallucination-baiting, and its difficulty-stratified subsets enable analysis of knowledge-boundary recognition.

**Lineage:** Introduced by Yang et al. 2024a; adopted as primary benchmark for TruthRL; truthfulness metric weights (w1=1, w2=0, w3=1) follow this paper's protocol.
