---
aliases:
- IARC dataset
- IARC Monographs classification dataset
- carcinogenicity confidence dataset
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:iarc-carcinogenicity
  type: dataset
  status: canonical
area: datasets
related:
- '[[2508.15050--dont-think-twice]]'
- '[[climatex]]'
- '[[masked-label-calibration-probe]]'
- '[[calibration]]'
- '[[overconfidence]]'
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
  target: '[[masked-label-calibration-probe]]'
  target_id: method:masked-label-calibration-probe
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

A dataset of 1,053 agents and exposure types classified by IARC scientist experts for carcinogenic hazard to humans, drawn from the IARC Monographs series since 1971. Classification follows a 5-level confidence scale (Group 1: carcinogenic to humans; 2A: probably carcinogenic; 2B: possibly carcinogenic; 3: not classifiable; 4: probably not carcinogenic). Used as a masked-label calibration benchmark for the public health domain.

**Why it matters here:** Provides an out-of-domain generalization test for LLM confidence calibration beyond climate science, covering oncology, epidemiology, and toxicology. Results confirm that over-reasoning degrades calibration (66.9% to 62.2% at maximum thinking budget) outside the climate domain.

**Lineage:** Derived from IARC Monographs (2025). Introduced as a calibration benchmark in arXiv:2508.15050.
