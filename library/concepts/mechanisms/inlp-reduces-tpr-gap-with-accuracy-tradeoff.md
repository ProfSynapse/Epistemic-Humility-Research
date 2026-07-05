---
aliases:
- INLP reduces TPR-Gap at moderate accuracy cost
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:inlp-reduces-tpr-gap-with-accuracy-tradeoff
  type: mechanism
  status: canonical
cause: Application of [[inlp]] guarding function on encoder representations before final linear layer retraining
effect: TPR-Gap (RMS) drops 39-52% across BOW, FastText, and BERT representations; main-task accuracy changes modestly (+1.9% to -5.5%)
polarity: decreases
related:
- '[[2004.07667--null-it-out-guarding-protected-attributes-iterative]]'
- '[[inlp]]'
- '[[tpr-gap]]'
- '[[bias-in-bios]]'
relationships:
- type: supported_by
  target: '[[2004.07667--null-it-out-guarding-protected-attributes-iterative]]'
  target_id: paper:2004.07667
  confidence: high
- type: related_to
  target: '[[inlp]]'
  target_id: method:inlp
- type: related_to
  target: '[[tpr-gap]]'
  target_id: metric:tpr-gap
contradicted-by: []
---

Iterative Nullspace Projection applied to encoder representations systematically removes the linear subspace that encodes gender, causing the true-positive-rate gap across professions to drop by 39-52% on the [[bias-in-bios]] benchmark. The accuracy loss on the main profession-classification task is modest (within a few percentage points), indicating that gender signal and occupational signal occupy partially separable subspaces. These results, reported in arXiv:2004.07667, establish [[inlp]] as an effective but not cost-free debiasing intervention.
