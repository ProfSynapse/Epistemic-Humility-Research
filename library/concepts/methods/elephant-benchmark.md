---
aliases:
- ELEPHANT framework
- Evaluation of LLMs as Excessive sycoPHANTs
- social sycophancy benchmark
tags:
- kg/method
- concept
- method
kg:
  id: method:elephant-benchmark
  type: method
  status: canonical
area: methods
related:
- '[[2505.13995--elephant-social-sycophancy]]'
- '[[sycophancy]]'
- '[[llm-as-judge]]'
- '[[preference-pair-data]]'
- '[[social-sycophancy]]'
- '[[gricean-maxims]]'
relationships:
- type: proposed_by
  target: '[[2505.13995--elephant-social-sycophancy]]'
  target_id: paper:2505.13995
  confidence: high
- type: related_to
  target: '[[sycophancy]]'
  target_id: term:sycophancy
  confidence: medium
- type: related_to
  target: '[[llm-as-judge]]'
  target_id: method:llm-as-judge
  confidence: medium
- type: related_to
  target: '[[preference-pair-data]]'
  target_id: dataset:preference-pair-data
  confidence: medium
- type: related_to
  target: '[[social-sycophancy]]'
  target_id: term:social-sycophancy
  confidence: medium
- type: related_to
  target: '[[gricean-maxims]]'
  target_id: term:gricean-maxims
  confidence: medium
---

A framework for automatically measuring social sycophancy in LLMs by scoring five face-preserving behaviors (emotional validation, moral endorsement, indirect language, indirect action, accepting framing) on two datasets: OEQ (open-ended advice queries compared against human responses) and AITA (Reddit r/AmITheAsshole posts with crowdsourced ground-truth labels). An LLM judge (GPT-4o) assigns binary labels per behavior; validation against human annotators achieves Fleiss kappa >= 0.63 and Cohen kappa >= 0.65 on all five metrics.

**Why it matters here:** Provides the first multi-dimensional behavioral benchmark for social sycophancy in personal-advice contexts, enabling researchers to audit whether post-training arms suppress or amplify face-preserving behaviors beyond what propositional benchmarks detect.

**Lineage:** Proposed by Cheng et al. (2505.13995); draws on the sociological face theory of Goffman (1955) and the LLM-as-judge paradigm.
