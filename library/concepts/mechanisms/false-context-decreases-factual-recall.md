---
aliases:
- False Context Decreases Probability of Correct Attribute
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:false-context-decreases-factual-recall
  type: mechanism
  status: canonical
cause: "Preceding a target sentence with false sentences in context (FF condition), activating the [[truth-co-occurrence-hypothesis|TCH mechanism]] and shifting the LM's latent truth estimate toward false"
effect: "The probability assigned to the correct attribute for the target sentence decreases by 4.55x relative to a true-sentence context (TT condition)"
polarity: decreases
related:
- '[[2510.15804--emergence-linear-truth-encodings-language-models]]'
- '[[truth-direction]]'
- '[[truth-co-occurrence-hypothesis]]'
- '[[factual-recall-localization]]'
relationships:
- type: supported_by
  target: '[[2510.15804--emergence-linear-truth-encodings-language-models]]'
  target_id: paper:2510.15804
  confidence: high
- type: related_to
  target: '[[truth-direction]]'
  target_id: term:truth-direction
- type: related_to
  target: '[[truth-co-occurrence-hypothesis]]'
  target_id: term:truth-co-occurrence-hypothesis
- type: related_to
  target: '[[factual-recall-localization]]'
  target_id: term:factual-recall-localization
---

The truth co-occurrence hypothesis predicts that a model conditioned on false context will lower its probability for true completions because the in-context truth statistics shift the model's latent truth estimate. The truth-encodings paper (arXiv:2510.15804) confirms this by comparing FF (false-false context) to TT (true-true context) conditions and observing a 4.55-fold reduction in the probability of the correct attribute in FF. This effect is mediated by the linear truth encoding: interventions that clamp the truth direction to its TT value partially restore correct-attribute probability in the FF condition, providing causal evidence that the latent truth variable drives factual recall probability.
