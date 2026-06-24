---
aliases:
- retrieval gap in calibration
- knowledge access bottleneck for calibration
- search-augmentation solves calibration ceiling
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:evidence-access-bottlenecks-expert-calibration
  type: mechanism
  status: canonical
cause: "Providing a reasoning model with retrieved evidence passages from web search for each statement in a knowledge-intensive calibration task (retrieval-augmented generation)"
effect: "Accuracy on expert confidence classification jumps from 48.7% to 89.3% (Cohen's kappa from 31.6% to 85.7%) for Gemini 2.5 Pro, nearly saturating the benchmark, a gain far larger than any achieved by increasing reasoning depth or model scale"
polarity: increases
related:
- '[[2508.15050--dont-think-twice]]'
- '[[over-reasoning-worsens-confidence-calibration]]'
- '[[calibration]]'
- '[[climatex]]'
- '[[overconfidence]]'
relationships:
- type: supported_by
  target: '[[2508.15050--dont-think-twice]]'
  target_id: paper:2508.15050
  confidence: high
- type: related_to
  target: '[[over-reasoning-worsens-confidence-calibration]]'
  target_id: mechanism:over-reasoning-worsens-confidence-calibration
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
  target: '[[overconfidence]]'
  target_id: term:overconfidence
  confidence: high
---

When a model lacks access to the specific evidence passage that informed the expert label, no amount of internal reasoning can reliably reconstruct the expert's confidence assessment. Once retrieval surfaces the salient passage, the model assigns the correct categorical confidence almost every time. This suggests that the gap between current LLM calibration performance and expert agreement is primarily an evidence-access failure rather than a reasoning-capacity failure, with implications for how knowledge-intensive calibration benchmarks should be interpreted and how practitioners should invest resources.
