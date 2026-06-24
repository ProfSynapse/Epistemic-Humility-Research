---
aliases:
- precision-recall AUC
- PR-AUC for claim scoring
- claim-level PR-AUC
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:pr-auc-claim-filtering
  type: metric
  status: canonical
area: metrics
related:
- '[[2604.13991--adaptive-conformal-factuality]]'
- '[[claim-conditioned-probability]]'
- '[[adaptive-conformal-factuality]]'
- '[[auroc]]'
- '[[factscore]]'
- '[[hallucination]]'
relationships:
- type: proposed_by
  target: '[[2604.13991--adaptive-conformal-factuality]]'
  target_id: paper:2604.13991
  confidence: high
- type: related_to
  target: '[[claim-conditioned-probability]]'
  target_id: method:claim-conditioned-probability
  confidence: medium
- type: related_to
  target: '[[adaptive-conformal-factuality]]'
  target_id: method:adaptive-conformal-factuality
  confidence: medium
- type: related_to
  target: '[[auroc]]'
  target_id: metric:auroc
  confidence: medium
- type: related_to
  target: '[[factscore]]'
  target_id: metric:factscore
  confidence: medium
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
  confidence: medium
---

Area under the precision-recall curve for the binary task of distinguishing factually correct from incorrect atomic claims using a continuous uncertainty score. More informative than AUROC in the class-imbalanced setting typical of long-form generation, where correct claims outnumber incorrect ones.

**Why it matters here:** PR-AUC directly quantifies how well a claim-level scorer supports selective prediction: a higher PR-AUC means fewer incorrect claims are retained at a given recall. It is the primary metric used in this paper to select the CCP scorer for conformal factuality pipelines.

**Lineage:** Standard information-retrieval metric adapted to the claim-filtering setting. Related to auroc but prioritizes precision at each recall level rather than overall discrimination.
