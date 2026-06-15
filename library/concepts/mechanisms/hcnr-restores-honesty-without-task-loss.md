---
aliases:
- Reverting honesty-critical neurons with Hessian compensation restores honesty while preserving task accuracy
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:hcnr-restores-honesty-without-task-loss
  type: mechanism
  status: canonical
cause: Selectively restoring neurons identified as high-honesty-importance / low-task-importance to their pre-trained states and applying a [[fisher-information-matrix]]-guided compensation vector to re-align them with downstream task neurons
effect: '[[honesty-score]] (F1 and [[refusal-delta]]) recovers to or above data-intensive retraining baselines while downstream task accuracy remains comparable, with only 20% of parameters modified and 256 total samples'
polarity: enables
related:
- '[[2511.12991--finetuned-llms-know-they-dont-know]]'
- '[[fisher-information-matrix]]'
- '[[honesty-score]]'
- '[[refusal-delta]]'
relationships:
- type: supported_by
  target: '[[2511.12991--finetuned-llms-know-they-dont-know]]'
  target_id: paper:2511.12991
  confidence: high
- type: related_to
  target: '[[fisher-information-matrix]]'
  target_id: method:fisher-information-matrix
- type: related_to
  target: '[[honesty-score]]'
  target_id: metric:honesty-score
- type: related_to
  target: '[[refusal-delta]]'
  target_id: metric:refusal-delta
---

[[honesty-critical-neurons-restoration]] exploits the dissociation between honesty-expression neurons and task-execution neurons identified via importance scoring. By reverting only the honesty-critical subset and compensating with a Hessian-weighted correction, the method avoids the task degradation that naive rollback would cause. The finetuned-LLMs paper (arXiv:2511.12991) shows that HCNR with only 256 samples matches or exceeds full retraining baselines on honesty metrics, making it a parameter-efficient corrective for SFT-induced honesty suppression.
