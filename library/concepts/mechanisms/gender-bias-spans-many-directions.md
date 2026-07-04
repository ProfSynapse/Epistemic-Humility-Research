---
aliases:
- Gender bias occupies dozens of orthogonal directions in embedding space
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:gender-bias-spans-many-directions
  type: mechanism
  status: canonical
cause: Gender information encoded in [[glove-word-embeddings]]
effect: Single-direction projection (e.g. he-she) leaves substantial residual linear gender signal; full removal requires dozens to hundreds of orthogonal directions
polarity: enables
related:
- '[[2004.07667--null-it-out-guarding-protected-attributes-iterative]]'
- '[[glove-word-embeddings]]'
- '[[inlp]]'
relationships:
- type: supported_by
  target: '[[2004.07667--null-it-out-guarding-protected-attributes-iterative]]'
  target_id: paper:2004.07667
  confidence: high
- type: related_to
  target: '[[glove-word-embeddings]]'
  target_id: model:glove-word-embeddings
- type: related_to
  target: '[[inlp]]'
  target_id: method:inlp
contradicted-by: []
---

Gender is not encoded as a single linear direction in word embeddings: after projecting out the canonical he-she axis, linear classifiers trained with [[inlp]] continue to recover gender signal, requiring iterative removal of dozens to hundreds of orthogonal directions before accuracy approaches chance. This high-dimensional structure means naive single-direction debiasing methods leave most of the bias intact. The finding is evidenced in arXiv:2004.07667, where repeated rounds of INLP projection are needed to substantially reduce TPR-Gap.
