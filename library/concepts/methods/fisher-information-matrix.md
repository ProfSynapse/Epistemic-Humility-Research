---
aliases:
- FIM
- diagonal FIM
- Fisher Information Matrix (FIM)
tags:
- kg/method
- concept
- method
kg:
  id: method:fisher-information-matrix
  type: method
  status: canonical
area: methods
---

The Fisher Information Matrix (FIM) is a second-order curvature measure from classical statistics that quantifies how much each parameter of a model influences the likelihood of the observed data. In the context of [[honesty-critical-neurons-restoration]], diagonal FIM entries are used to approximate the expected impact of SFT-induced parameter perturbations on the honesty loss, providing an unbiased per-neuron importance score under an isotropic perturbation assumption.

**Why it matters here:** FIM-based importance scoring is the mechanism HCNR uses to separate neurons that are critical for honesty from those that are critical for downstream task performance, enabling surgical parameter restoration without a full retrain. This is a practical tool for understanding how SFT shifts the honesty-capability tradeoff at the parameter level.

**Lineage:** FIM is a foundational statistical concept; its application here connects to [[honesty-critical-neurons-restoration]] as the core scoring method.
