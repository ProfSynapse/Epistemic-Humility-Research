---
aliases:
- OOD r-squared
- out-of-distribution R2
- zero-shot OOD R2
- OOD R²
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:ood-coefficient-of-determination
  type: metric
  status: canonical
area: metrics
---

The OOD coefficient of determination (OOD R²) is the standard R² statistic computed between a [[linear-probe]]'s predictions for latent ground-truth factors x* and the actual held-out ground-truth values drawn from a distribution not seen during training. The probe is fit on a set of training tasks and then evaluated cold on new tasks without any additional tuning, so the score directly quantifies zero-shot out-of-distribution generalization of the underlying representation. High OOD R² (close to 1) is achievable when the number of training tasks N_task is at least as large as the intrinsic dimensionality D of the latent space, because the probe then has sufficient supervision to capture the full [[disentangled-representation]] structure.

**Why it matters here:** A model's epistemic-humility signal (such as an uncertainty or answerability axis) is only useful in deployment if it holds up on inputs outside the training distribution. OOD R² makes that transfer property concrete and measurable, separating representations that generalize from those that merely fit training-task probes.

**Lineage:** a domain application of the classical coefficient of determination to representation evaluation under distribution shift; no dedicated predecessor in this vocabulary.
