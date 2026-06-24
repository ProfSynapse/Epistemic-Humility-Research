---
aliases:
- CRC
- CRC (TPC)
- CRC (BSS)
- Top Principal Component clustering
- Bimodal Salience Search
tags:
- kg/method
- concept
- method
kg:
  id: method:contrastive-representation-clustering
  type: method
  status: canonical
area: methods
related:
- '[[2212.03827--ccs-discovering-latent-knowledge]]'
- '[[contrast-consistent-search]]'
- '[[linear-probe]]'
- '[[truth-direction]]'
relationships:
- type: proposed_by
  target: '[[2212.03827--ccs-discovering-latent-knowledge]]'
  target_id: paper:2212.03827
  confidence: high
- type: related_to
  target: '[[contrast-consistent-search]]'
  target_id: method:contrast-consistent-search
  confidence: medium
- type: related_to
  target: '[[linear-probe]]'
  target_id: method:linear-probe
  confidence: medium
- type: related_to
  target: '[[truth-direction]]'
  target_id: term:truth-direction
  confidence: medium
---

A parameter-free companion to CCS that clusters the differences of normalized hidden states for contrast pairs (positive minus negative) either via the top principal component (TPC) or a bimodal salience search (BSS), without any optimization. Reaches 69.2% (TPC) and 69.8% (BSS) mean accuracy.

**Why it matters here:** Confirms that truth is a salient, high-variance direction in the contrastive activation difference space even without gradient-based learning, strengthening the case that latent truth representations are structurally prominent.

**Lineage:** Introduced alongside CCS in Burns et al. (2022) as a check on the claim that truth is a salient feature; related to PCA-based probing and unsupervised clustering.
