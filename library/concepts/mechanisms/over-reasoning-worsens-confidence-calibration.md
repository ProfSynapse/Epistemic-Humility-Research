---
aliases:
- thinking-budget calibration degradation
- extended chain-of-thought impairs calibration
- over-reasoning overconfidence spiral
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:over-reasoning-worsens-confidence-calibration
  type: mechanism
  status: canonical
cause: "Increasing the reasoning token budget allocated to chain-of-thought deliberation in a reasoning model (e.g., Gemini 2.5 Flash thinking budget swept from 0 to 24,576 tokens)"
effect: "Accuracy on expert confidence classification peaks briefly at modest budgets (64-192 tokens) then collapses, while overconfidence grows monotonically, from +6% to +21.3% on climate statements and from +15.6% to +35.6% on carcinogenicity statements, producing diminishing and eventually negative returns on both accuracy and calibration quality"
polarity: decreases
related:
- '[[2508.15050--dont-think-twice]]'
- '[[test-time-scaling-worsens-abstention]]'
- '[[overconfidence]]'
- '[[calibration]]'
- '[[climatex]]'
- '[[iarc-carcinogenicity]]'
relationships:
- type: supported_by
  target: '[[2508.15050--dont-think-twice]]'
  target_id: paper:2508.15050
  confidence: high
- type: related_to
  target: '[[test-time-scaling-worsens-abstention]]'
  target_id: mechanism:test-time-scaling-worsens-abstention
  confidence: high
- type: related_to
  target: '[[overconfidence]]'
  target_id: term:overconfidence
  confidence: high
- type: related_to
  target: '[[calibration]]'
  target_id: term:calibration
  confidence: high
- type: related_to
  target: '[[climatex]]'
  target_id: dataset:climatex
  confidence: high
- type: related_to
  target: '[[iarc-carcinogenicity]]'
  target_id: dataset:iarc-carcinogenicity
  confidence: high
---

Extended chain-of-thought appears to introduce spurious rationales and circular reasoning patterns that push models toward high-confidence predictions regardless of the ground-truth label distribution. The effect is non-monotonic on accuracy (a small peak then collapse then partial recovery) but monotonic on overconfidence (higher budgets always inflate predicted confidence relative to ground truth). The pattern holds across two distinct expert-labeled domains (IPCC climate and IARC carcinogenicity), suggesting it reflects a general property of extended deliberation rather than a domain-specific artifact.
