---
aliases:
- inference-time compute amplifies overconfidence
- reasoning depth worsens calibration on wrong answers
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:deeper-reasoning-increases-overconfidence
  type: mechanism
  status: canonical
cause: "Increasing the reasoning token budget (from RE-Low to RE-High) allocated to chain-of-thought generation before the final answer"
effect: "Higher ECE on wrongly-answered questions, with the proportion of high-confidence predictions (85%-100% bins) increasing even when accuracy does not, because extended reasoning traces reinforce the model's commitment to an incorrect answer"
polarity: increases
related:
- '[[2506.18183--reasoning-models-dont-know]]'
- '[[test-time-scaling-worsens-abstention]]'
- '[[reasoning-finetuning-degrades-abstention]]'
- '[[overconfidence]]'
- '[[expected-calibration-error]]'
- '[[reasoning-fine-tuning]]'
- '[[verbalized-confidence]]'
- '[[introspective-uncertainty-quantification]]'
relationships:
- type: supported_by
  target: '[[2506.18183--reasoning-models-dont-know]]'
  target_id: paper:2506.18183
  confidence: high
- type: related_to
  target: '[[test-time-scaling-worsens-abstention]]'
  target_id: mechanism:test-time-scaling-worsens-abstention
  confidence: high
- type: related_to
  target: '[[reasoning-finetuning-degrades-abstention]]'
  target_id: mechanism:reasoning-finetuning-degrades-abstention
  confidence: high
- type: related_to
  target: '[[overconfidence]]'
  target_id: term:overconfidence
  confidence: high
- type: related_to
  target: '[[expected-calibration-error]]'
  target_id: metric:expected-calibration-error
  confidence: high
- type: related_to
  target: '[[reasoning-fine-tuning]]'
  target_id: method:reasoning-fine-tuning
  confidence: high
- type: related_to
  target: '[[verbalized-confidence]]'
  target_id: method:verbalized-confidence
  confidence: high
- type: related_to
  target: '[[introspective-uncertainty-quantification]]'
  target_id: method:introspective-uncertainty-quantification
  confidence: high
---

When a reasoning model arrives at an incorrect answer, allocating more thinking tokens allows the model to construct a more elaborate and internally consistent chain-of-thought that justifies that wrong answer. This reinforcement inflates the model's expressed confidence without changing the underlying correctness of the response. Mei et al. (arXiv:2506.18183) document this across Claude 3.7 Sonnet and o3-Mini: on wrongly-answered questions, o3-Mini's ECE rises by 7 percentage points from RE-Low to RE-High, and Claude's rises by 2 percentage points. The mechanism is analogous to a documented human cognitive bias: humans also report higher confidence when given more time to think, even when their answers do not change. The effect is moderated by accuracy: when deeper reasoning actually raises accuracy (e.g., on GPQA), ECE can improve. The worsening only dominates when accuracy saturates. Distinct from test-time-scaling-worsens-abstention, which concerns abstention recall on unanswerable questions rather than calibration on questions the model attempts to answer.
