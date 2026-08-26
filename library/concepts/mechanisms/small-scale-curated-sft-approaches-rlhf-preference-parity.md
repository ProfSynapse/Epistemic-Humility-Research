---
aliases:
- 1,000-example SFT approaches RLHF quality
- LIMA human preference parity
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:small-scale-curated-sft-approaches-rlhf-preference-parity
  type: mechanism
  status: canonical
cause: "Fine-tuning a pretrained LLM via [[lima]] on only 1,000 stylistically-consistent, diverse-prompt SFT examples, with no RL or additional human-feedback stage"
effect: "Responses are judged equivalent to or better than larger RLHF-trained systems in a controlled human preference study, at rates that scale with how much additional training the baseline received"
polarity: enables
related:
- '[[2305.11206--lima-less-more-alignment]]'
- '[[lima]]'
- '[[superficial-alignment-hypothesis]]'
- '[[alignment-training-saturates-on-small-data]]'
relationships:
- type: supported_by
  target: '[[2305.11206--lima-less-more-alignment]]'
  target_id: paper:2305.11206
  confidence: high
- type: related_to
  target: '[[lima]]'
  target_id: dataset:lima
  confidence: high
- type: related_to
  target: '[[superficial-alignment-hypothesis]]'
  target_id: term:superficial-alignment-hypothesis
  confidence: high
- type: related_to
  target: '[[alignment-training-saturates-on-small-data]]'
  target_id: mechanism:alignment-training-saturates-on-small-data
  confidence: medium
---

In a controlled human preference study over 300 test prompts, LIMA's outputs were judged equivalent to or strictly preferred over GPT-4 in 43% of comparisons, over Bard in 58% of comparisons, and over DaVinci003 (trained with human feedback via RLHF) in 65% of comparisons (Zhou et al. 2023, Section 1, Figure 1). The preference rate against each baseline tracks roughly with how much extra alignment training that baseline received, consistent with the Superficial Alignment Hypothesis: most of the response quality already exists in the pretrained weights, and a small curated SFT set is enough to surface it in the right format.
