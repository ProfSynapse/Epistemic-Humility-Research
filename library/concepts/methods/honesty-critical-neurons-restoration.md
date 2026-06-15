---
aliases:
- HCNR
- Honesty-Critical Neurons Restoration
- Honesty-Critical Neurons Restoration (HCNR)
tags:
- kg/method
- concept
- method
kg:
  id: method:honesty-critical-neurons-restoration
  type: method
  status: canonical
area: methods
related:
- '[[2511.12991--finetuned-llms-know-they-dont-know]]'
- '[[refusal-aware-instruction-tuning]]'
- '[[fisher-information-matrix]]'
relationships:
- type: proposed_by
  target: '[[2511.12991--finetuned-llms-know-they-dont-know]]'
  target_id: paper:2511.12991
  confidence: high
- type: related_to
  target: '[[refusal-aware-instruction-tuning]]'
  target_id: method:refusal-aware-instruction-tuning
- type: related_to
  target: '[[fisher-information-matrix]]'
  target_id: method:fisher-information-matrix
---

Honesty-Critical Neurons Restoration (HCNR) is a training-free, parameter-efficient framework that recovers post-SFT honesty by identifying neurons whose Fisher-based importance scores are high for honesty but low for downstream task performance, and reverting those neurons to their pre-trained states. A Hessian-guided compensation vector is then applied to the restored neurons to re-align them with the remaining task-oriented parameters, avoiding task degradation while recovering honest self-expression.

**Why it matters here:** HCNR operationalizes the [[spurious-dishonesty]] diagnosis: if SFT suppresses expression rather than erasing knowledge, then selectively reverting a small subset of parameters should restore honest abstention without retraining. This is directly relevant to the SFT-vs-DPO-vs-KTO abstention study because it offers a surgical alternative to full preference-optimization for recovering calibrated uncertainty expression.

**Lineage:** related to [[refusal-aware-instruction-tuning]] (another post-hoc SFT correction approach) and relies on [[fisher-information-matrix]] for neuron importance scoring.
