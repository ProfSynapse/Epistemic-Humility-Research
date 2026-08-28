---
aliases:
- Semantic separability improves domain-constraint steering
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:semantic-separability-improves-domain-constraint-steering
  type: mechanism
  status: canonical
cause: "A target prompt category is more semantically distant from non-target categories in sentence-embedding space."
effect: "A complement condition vector more effectively constrains model responses to the target domain."
polarity: increases
related:
- '[[2409.05907--programming-refusal-conditional-activation-steering]]'
- '[[conditional-activation-steering]]'
- '[[condition-vector]]'
relationships:
- type: supported_by
  target: '[[2409.05907--programming-refusal-conditional-activation-steering]]'
  target_id: paper:2409.05907
  confidence: high
- type: related_to
  target: '[[conditional-activation-steering]]'
  target_id: method:conditional-activation-steering
  confidence: high
- type: related_to
  target: '[[condition-vector]]'
  target_id: term:condition-vector
  confidence: high
---

The paper reports a positive relation between a category's semantic distance from other categories and the increase in refusal on those other categories. The relation is observational within the tested category set.
