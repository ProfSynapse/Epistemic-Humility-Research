---
aliases:
- Intransitive preference noise degrades DPO more than KTO
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:preference-data-intransitivity-hurts-dpo
  type: mechanism
  status: canonical
cause: Noisy, intransitive preference annotations from multiple human annotators in public datasets (SHP, OpenAssistant, [[ultrafeedback]])
effect: '[[kahneman-tversky-optimization]] matches or exceeds [[direct-preference-optimization]] because KTO''s binary signal is more robust to label noise and contradictory preferences than DPO''s paired comparisons'
polarity: decreases
related:
- '[[2402.01306--kto-prospect-theoretic]]'
- '[[ultrafeedback]]'
- '[[kahneman-tversky-optimization]]'
- '[[direct-preference-optimization]]'
relationships:
- type: supported_by
  target: '[[2402.01306--kto-prospect-theoretic]]'
  target_id: paper:2402.01306
  confidence: high
- type: related_to
  target: '[[ultrafeedback]]'
  target_id: dataset:ultrafeedback
- type: related_to
  target: '[[kahneman-tversky-optimization]]'
  target_id: method:kahneman-tversky-optimization
- type: related_to
  target: '[[direct-preference-optimization]]'
  target_id: method:direct-preference-optimization
---

DPO requires that preference pairs be consistent and transitive; when they are not, the contrastive loss receives contradictory gradient signal. KTO sidesteps this because it conditions only on whether an individual response is desirable or not, making the loss insensitive to the relative ranking of two responses. The KTO paper (arXiv:2402.01306) identifies intransitivity in SHP, OpenAssistant, and UltraFeedback as a practical explanation for why KTO outperforms DPO on those corpora.
