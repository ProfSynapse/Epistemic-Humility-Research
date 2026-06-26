---
aliases:
- DPO beta sensitivity depends on pair quality
- heterogeneous preference pairs need dynamic beta
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:dpo-beta-should-follow-pair-quality
  type: mechanism
  status: canonical
cause: "Preference-pair datasets mix closely matched informative pairs, easy high-gap pairs, and outliers under one static DPO beta."
effect: "The same beta can under-update high-quality pairs or overfit/noise-follow low-quality pairs, producing weaker alignment behavior."
polarity: causes
related:
- '[[2407.08639--dpo-direct-preference-optimization-dynamic]]'
- '[[beta-dpo]]'
- '[[direct-preference-optimization]]'
- '[[preference-pair-data]]'
relationships:
- type: supported_by
  target: '[[2407.08639--dpo-direct-preference-optimization-dynamic]]'
  target_id: paper:2407.08639
  confidence: high
- type: related_to
  target: '[[beta-dpo]]'
  target_id: method:beta-dpo
  confidence: high
- type: related_to
  target: '[[direct-preference-optimization]]'
  target_id: method:direct-preference-optimization
  confidence: high
- type: related_to
  target: '[[preference-pair-data]]'
  target_id: dataset:preference-pair-data
  confidence: high
---

Wu et al. report that low-gap and high-gap preference pairs favor different
beta settings. Their dynamic-beta method treats pair quality as a control signal
for how aggressively DPO should move from the reference policy.
