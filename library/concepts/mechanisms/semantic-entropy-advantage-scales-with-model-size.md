---
aliases:
- semantic entropy scaling advantage
- scale-dependent uncertainty gap
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:semantic-entropy-advantage-scales-with-model-size
  type: mechanism
  status: canonical
cause: "Larger autoregressive language models generate more fluent and semantically diverse paraphrases of the same correct meaning when sampled at a given temperature"
effect: "The AUROC gap between semantic entropy and token-level entropy baselines widens monotonically with model size, because larger models suffer more from paraphrase inflation relative to their actual semantic uncertainty"
polarity: increases
related:
- '[[2302.09664--semantic-uncertainty-kuhn]]'
- '[[semantic-entropy]]'
- '[[lexical-entropy-overestimates-uncertainty-under-paraphrase]]'
- '[[model-size-improves-calibration]]'
relationships:
- type: supported_by
  target: '[[2302.09664--semantic-uncertainty-kuhn]]'
  target_id: paper:2302.09664
  confidence: high
- type: related_to
  target: '[[semantic-entropy]]'
  target_id: method:semantic-entropy
  confidence: high
- type: related_to
  target: '[[lexical-entropy-overestimates-uncertainty-under-paraphrase]]'
  target_id: mechanism:lexical-entropy-overestimates-uncertainty-under-paraphrase
  confidence: high
- type: related_to
  target: '[[model-size-improves-calibration]]'
  target_id: mechanism:model-size-improves-calibration
  confidence: high
---

Across 2.7B to 30B OPT models on TriviaQA and CoQA, the advantage of semantic entropy over length-normalised entropy increases steadily with scale (Figure 1b, Figure 2). Larger models generate more confident and syntactically varied paraphrases, so more of the entropy in token-sequence space is paraphrase variation rather than semantic uncertainty. Semantic entropy's clustering step removes this variation, recovering the true uncertainty signal. This implies that calibration metrics relying on token-level entropy will become increasingly biased as models scale, making semantic entropy more important at larger scales.
