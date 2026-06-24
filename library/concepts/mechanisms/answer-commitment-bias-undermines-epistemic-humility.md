---
aliases:
- Answer-Commitment Bias Undermines Epistemic Humility
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:answer-commitment-bias-undermines-epistemic-humility
  type: mechanism
  status: canonical
cause: A learned bias toward always selecting one of the presented answer options, reinforced by training and evaluation regimes that reward picking a listed choice
effect: Failure to select "None of the above" when no option is correct, with accuracy on NOTA-only and pure-noise-image items collapsing below the random-guess baseline
polarity: decreases
related:
- '[[2509.09658--humblebench-epistemic-humility-multimodal]]'
- '[[epistemic-humility]]'
- '[[multimodal-large-language-model]]'
- '[[hallucination]]'
relationships:
- type: supported_by
  target: '[[2509.09658--humblebench-epistemic-humility-multimodal]]'
  target_id: paper:2509.09658
  confidence: high
- type: related_to
  target: '[[epistemic-humility]]'
  target_id: term:epistemic-humility
- type: related_to
  target: '[[multimodal-large-language-model]]'
  target_id: term:multimodal-large-language-model
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
---

MLLMs trained and evaluated on standard multiple-choice recognition learn that a
listed option is essentially always correct, so they develop a strong prior to
commit to one of the presented answers. When HumbleBench
(arXiv:2509.09658) inserts a "None of the above" option and constructs items where
every listed answer is wrong, this commitment bias surfaces: models keep selecting
a plausible but unsupported choice and their accuracy on NOTA-only items, and on
pure-noise images that carry no supporting evidence, drops sharply, in several
cases below random chance. The failure is one of [[epistemic-humility]] rather
than recognition: the visual signal is absent or contradictory, yet the model
still overcommits.
