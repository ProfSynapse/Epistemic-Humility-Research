---
aliases:
- Ablating the global workspace hurts deliberate reasoning but spares automatic processing
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:global-workspace-ablation-impairs-flexible-cognition
  type: mechanism
  status: canonical
cause: "Ablating the J-space component of a model's activations"
effect: "flexible, deliberate tasks (multi-hop reasoning, translation, summarization, sonnet-writing, no-chain-of-thought math) degrade sharply, while automatic tasks (sentiment classification, MMLU, CoLA, extractive QA) stay at or near the unablated baseline, and chain-of-thought math answers are far more robust to the ablation than direct answers"
polarity: decreases
related:
- '[[tc-2026-workspace--verbalizable-representations-global-workspace]]'
- '[[global-workspace]]'
- '[[jacobian-lens]]'
- '[[mmlu]]'
relationships:
- type: supported_by
  target: '[[tc-2026-workspace--verbalizable-representations-global-workspace]]'
  target_id: paper:tc-2026-workspace
  confidence: high
- type: related_to
  target: '[[global-workspace]]'
  target_id: term:global-workspace
  confidence: high
- type: related_to
  target: '[[jacobian-lens]]'
  target_id: method:jacobian-lens
  confidence: high
- type: related_to
  target: '[[mmlu]]'
  target_id: dataset:mmlu
  confidence: medium
---

Ablating the J-space component of a model's activations selectively harms
tasks that require flexible, deliberate computation while leaving automatic,
routine processing largely intact. In a language-identification experiment,
J-lens vector swaps redirect explicit-report and flexible-computation tasks on
essentially every trial, while continuation and anomaly-detection tasks built
from the same prompts stay largely unmoved even though the target concept
appears in the [[jacobian-lens]] readout at comparable rates across all four
tasks (Figure 20). In a broader ablation, automatic tasks (sentiment
classification, [[mmlu]], CoLA, extractive QA) remain at or near the unablated
baseline, while multi-hop reasoning drops to near zero and translation,
summarization, and sonnet-writing fall well below the unablated baseline
(Figure 21); chain-of-thought math answers are substantially more robust to
the ablation than direct (no-CoT) math answers (Figure 24). This selectivity
is the paper's primary evidence that the [[global-workspace]] is necessary for
flexible cognition specifically, not for processing in general.
