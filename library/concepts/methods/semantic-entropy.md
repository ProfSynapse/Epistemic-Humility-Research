---
aliases:
- SE
- semantic uncertainty estimation
- entropy over meanings
tags:
- kg/method
- concept
- method
kg:
  id: method:semantic-entropy
  type: method
  status: canonical
area: methods
related:
- '[[2302.09664--semantic-uncertainty-kuhn]]'
- '[[bidirectional-entailment-clustering]]'
- '[[semantic-equivalence]]'
- '[[p-true]]'
- '[[auroc]]'
- '[[aleatoric-uncertainty]]'
- '[[decoding-randomness]]'
- '[[triviaqa]]'
- '[[coqa]]'
relationships:
- type: proposed_by
  target: '[[2302.09664--semantic-uncertainty-kuhn]]'
  target_id: paper:2302.09664
  confidence: high
- type: related_to
  target: '[[bidirectional-entailment-clustering]]'
  target_id: method:bidirectional-entailment-clustering
  confidence: medium
- type: related_to
  target: '[[semantic-equivalence]]'
  target_id: term:semantic-equivalence
  confidence: medium
- type: related_to
  target: '[[p-true]]'
  target_id: method:p-true
  confidence: medium
- type: related_to
  target: '[[auroc]]'
  target_id: metric:auroc
  confidence: medium
- type: related_to
  target: '[[aleatoric-uncertainty]]'
  target_id: term:aleatoric-uncertainty
  confidence: medium
- type: related_to
  target: '[[decoding-randomness]]'
  target_id: term:decoding-randomness
  confidence: medium
- type: related_to
  target: '[[triviaqa]]'
  target_id: dataset:triviaqa
  confidence: medium
- type: related_to
  target: '[[coqa]]'
  target_id: dataset:coqa
  confidence: medium
---

An unsupervised uncertainty measure for free-form NLG that clusters sampled model outputs into semantic equivalence classes via bidirectional entailment, sums sequence likelihoods within each class to obtain meaning-level probabilities, and computes entropy over the resulting distribution of meanings rather than token sequences. Requires no model modification and runs off the shelf with any autoregressive LLM.

**Why it matters here:** Removes lexical paraphrase inflation from entropy-based uncertainty, yielding AUROC gains over token-level entropy that widen with model scale and sample count. Directly relevant to evaluating calibration in Phase 1 arms where training may shift paraphrase diversity independently of semantic uncertainty.

**Lineage:** Proposed by Kuhn, Gal, and Farquhar (arXiv:2302.09664, ICLR 2023) as a fix for the semantic equivalence problem in NLG uncertainty. Extends standard predictive entropy (Malinin and Gales 2020) by converting the event space from token sequences to meaning classes. Compared against p-true (Kadavath et al. 2022) and lexical similarity baselines.
