---
aliases:
- Probe-LR
- Probe-MM
- diverse-dataset truthfulness probe
tags:
- kg/method
- concept
- method
kg:
  id: method:universal-truthfulness-probe
  type: method
  status: canonical
area: methods
related:
- '[[2407.08582--generalizable-truth-probes]]'
- '[[linear-probe]]'
- '[[mass-mean-probing]]'
- '[[truth-direction]]'
- '[[generation-discrimination-gap]]'
- '[[universal-truthfulness-hyperplane]]'
relationships:
- type: proposed_by
  target: '[[2407.08582--generalizable-truth-probes]]'
  target_id: paper:2407.08582
  confidence: high
- type: related_to
  target: '[[linear-probe]]'
  target_id: method:linear-probe
  confidence: medium
- type: related_to
  target: '[[mass-mean-probing]]'
  target_id: method:mass-mean-probing
  confidence: medium
- type: related_to
  target: '[[truth-direction]]'
  target_id: term:truth-direction
  confidence: medium
- type: related_to
  target: '[[generation-discrimination-gap]]'
  target_id: term:generation-discrimination-gap
  confidence: medium
- type: related_to
  target: '[[universal-truthfulness-hyperplane]]'
  target_id: term:universal-truthfulness-hyperplane
  confidence: medium
---

A family of lightweight linear classifiers (logistic regression or mass mean direction) trained on concatenated attention-head outputs drawn from a sparse selection of positions across a diverse collection of datasets, designed to classify whether an LLM's output is factually correct or incorrect in a way that generalizes across tasks and domains.

**Why it matters here:** Provides a minimal, weight-frozen route to hallucination detection that generalizes OOD when trained on diverse datasets, avoiding the OOD collapse seen in single-dataset probes. Achieves approximately 70% cross-task accuracy with as few as 10 samples per dataset, making it practically cheap to deploy.

**Lineage:** Builds on linear-probe and mass-mean-probing traditions; extends them by scaling training diversity rather than model capacity or annotation volume.
