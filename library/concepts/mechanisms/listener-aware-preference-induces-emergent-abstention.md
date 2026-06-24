---
aliases:
- emergent abstention from calibration DPO
- conservative preference function emergent abstention
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:listener-aware-preference-induces-emergent-abstention
  type: mechanism
  status: canonical
cause: "DPO preference function with conservative utility ordering (false rejection preferred over false acceptance) applied to answer-only training data with no abstention examples"
effect: "Models produce abstaining outputs at 25-35% rates, correctly targeting low-accuracy items; accuracy on non-abstained examples remains comparable to the base model"
polarity: enables
related:
- '[[2405.21028--lacie-listener-aware-calibration]]'
- '[[lacie]]'
- '[[direct-preference-optimization]]'
- '[[abstention]]'
- '[[over-abstention]]'
- '[[dpo-reduces-over-abstention]]'
- '[[ternary-reward-enables-abstention-over-hallucination]]'
- '[[answer-relabeling-enables-abstention]]'
relationships:
- type: supported_by
  target: '[[2405.21028--lacie-listener-aware-calibration]]'
  target_id: paper:2405.21028
  confidence: high
- type: related_to
  target: '[[lacie]]'
  target_id: method:lacie
  confidence: high
- type: related_to
  target: '[[direct-preference-optimization]]'
  target_id: method:direct-preference-optimization
  confidence: high
- type: related_to
  target: '[[abstention]]'
  target_id: term:abstention
  confidence: high
- type: related_to
  target: '[[over-abstention]]'
  target_id: term:over-abstention
  confidence: high
- type: related_to
  target: '[[dpo-reduces-over-abstention]]'
  target_id: mechanism:dpo-reduces-over-abstention
  confidence: high
- type: related_to
  target: '[[ternary-reward-enables-abstention-over-hallucination]]'
  target_id: mechanism:ternary-reward-enables-abstention-over-hallucination
  confidence: high
- type: related_to
  target: '[[answer-relabeling-enables-abstention]]'
  target_id: mechanism:answer-relabeling-enables-abstention
  confidence: high
---

The LACIE preference function sets true-accept = true-reject > false-accept > false-reject (Eq. 1). This conservative ordering makes hedging and abstention the low-risk policy for uncertain items, even though no abstention examples appear in training. Mistral-7B abstention rises from 0.80% to 25.27%, Llama3-8B from 13.20% to 35.37%, Llama3-70B from 12.87% to 32.77%. Abstention correctly correlates with items the base model would have answered incorrectly (Appendix C). The mechanism generalizes the ternary-reward insight to the DPO setting: reward asymmetry between error types, not explicit abstention supervision, is the proximal cause. (Table 1, Section 4.2, Appendix C)
