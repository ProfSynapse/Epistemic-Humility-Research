---
aliases:
- Legal Bench
- legal-bench
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:legalbench
  type: dataset
  status: canonical
area: datasets
related:
- '[[2510.05126--metacognition-uncertainty-communication]]'
- '[[truthfulqa]]'
- '[[metamedqa]]'
- '[[calibration]]'
- '[[expected-calibration-error]]'
- '[[overconfidence]]'
relationships:
- type: proposed_by
  target: '[[2510.05126--metacognition-uncertainty-communication]]'
  target_id: paper:2510.05126
  confidence: high
- type: related_to
  target: '[[truthfulqa]]'
  target_id: dataset:truthfulqa
  confidence: medium
- type: related_to
  target: '[[metamedqa]]'
  target_id: dataset:metamedqa
  confidence: medium
- type: related_to
  target: '[[calibration]]'
  target_id: term:calibration
  confidence: medium
- type: related_to
  target: '[[expected-calibration-error]]'
  target_id: metric:expected-calibration-error
  confidence: medium
- type: related_to
  target: '[[overconfidence]]'
  target_id: term:overconfidence
  confidence: medium
---

A benchmark measuring legal reasoning abilities of LLMs across 162 tasks developed with legal scholars and practitioners, covering six reasoning categories (issue-spotting, rule-recall, rule-application, rule-conclusion, interpretation, rhetorical-understanding) drawn from contracts, civil procedure, and corporate law.

**Why it matters here:** Provides an out-of-domain generalization test for calibration and uncertainty research, spanning answer formats and reasoning types distinct from general-knowledge training corpora; prior LLM deployments in legal contexts have documented reliability failures, making calibrated confidence especially high stakes.

**Lineage:** Introduced by Guha et al. (2023) as a collaborative benchmark with legal domain experts.
