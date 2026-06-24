---
aliases:
- Gap 4
- probe-transfer gap
- representations vs behavior gap
tags:
- kg/gap
- concept
- gap
kg:
  id: gap:4-probe-transfer
  type: gap
  status: canonical
area: mechanism
related:
- '[[2304.13734--internal-state-knows-lying]]'
- '[[2212.03827--ccs-discovering-latent-knowledge]]'
- '[[2310.06824--geometry-of-truth]]'
- '[[2306.03341--inference-time-intervention]]'
- '[[2207.05221--lms-mostly-know-what-they-know]]'
- '[[2511.12991--finetuned-llms-know-they-dont-know]]'
- '[[2510.09033--probes-read-recall-not-truth]]'
- '[[2407.08582--generalizable-truth-probes]]'
relationships:
- type: related_to
  target: '[[2304.13734--internal-state-knows-lying]]'
  target_id: paper:2304.13734
  confidence: high
- type: related_to
  target: '[[2207.05221--lms-mostly-know-what-they-know]]'
  target_id: paper:2207.05221
  confidence: high
- type: related_to
  target: '[[2511.12991--finetuned-llms-know-they-dont-know]]'
  target_id: paper:2511.12991
  confidence: high
- type: related_to
  target: '[[2510.09033--probes-read-recall-not-truth]]'
  target_id: paper:2510.09033
  confidence: medium
---

**Gap 4 (meta-analysis draft-v0 §6.3): no probe-transfer study tests whether
humility fine-tuning changes representations or only behavior.** No paper trains
epistemic probes on a base model, applies honesty-targeted fine-tuning, and
re-reads the probes to ask whether the internal signal moved with the behavior.

**Why it matters:** the corpus is almost entirely behavioral. It shows training
changes what a model *says* about its knowledge, and is silent on whether the
representations underneath changed too. The two are known to come apart, which is
the difference between training humility and training the performance of humility.
Probes are the instrument that can tell them apart.

**Nearest existing evidence:** the probing toolkit is mature (internal-state
probes [[2304.13734--internal-state-knows-lying]], CCS
[[2212.03827--ccs-discovering-latent-knowledge]], mass-mean truth probes
[[2310.06824--geometry-of-truth]], ITI
[[2306.03341--inference-time-intervention]], P(IK)
[[2207.05221--lms-mostly-know-what-they-know]]), and the closest prior art
[[2511.12991--finetuned-llms-know-they-dont-know]] shows base-trained probes
surviving ordinary-task SFT. None runs the test across honesty-targeted
fine-tuning, let alone across method families.

**Cautions any test inherits:** probes may read knowledge-recall rather than
truth ([[2510.09033--probes-read-recall-not-truth]]), and cross-dataset transfer
fails on negation-style shifts unless probes train on diverse data
([[2407.08582--generalizable-truth-probes]]). A credible experiment needs recall
controls and diverse probe-training data.

Tested by [[gradient-probe-coherence]] (the gradient-probe modality) and the
Phase 3 mechanism program.
