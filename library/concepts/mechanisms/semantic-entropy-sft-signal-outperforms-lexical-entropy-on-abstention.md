---
aliases:
- SE-based abstention SFT advantage
- semantic entropy abstention training advantage
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:semantic-entropy-sft-signal-outperforms-lexical-entropy-on-abstention
  type: mechanism
  status: canonical
cause: "Using semantic entropy (computed via bidirectional entailment clustering over M=10 high-temperature samples) as the partitioning signal for abstention SFT, replacing either ground-truth correctness labels (R-Tuning) or classical token-level entropy (R-Tuning-U)"
effect: "Fine-tuned models achieve lower Accuracy-Engagement Distance in both in-distribution and out-of-distribution evaluation, particularly for Long-QA where the advantage is up to 30.1% AED reduction, and form a Pareto frontier over competing methods at all uncertainty thresholds in the Long-QA adaptation plot"
polarity: decreases
related:
- '[[2410.17234--semantic-entropy-abstention]]'
- '[[semantic-entropy]]'
- '[[r-tuning]]'
- '[[bidirectional-entailment-clustering]]'
- '[[lexical-entropy-overestimates-uncertainty-under-paraphrase]]'
- '[[sft-abstention-overfits-indomain]]'
- '[[accuracy-engagement-distance]]'
- '[[low-rank-adaptation]]'
relationships:
- type: supported_by
  target: '[[2410.17234--semantic-entropy-abstention]]'
  target_id: paper:2410.17234
  confidence: high
- type: related_to
  target: '[[semantic-entropy]]'
  target_id: method:semantic-entropy
  confidence: high
- type: related_to
  target: '[[r-tuning]]'
  target_id: method:r-tuning
  confidence: high
- type: related_to
  target: '[[bidirectional-entailment-clustering]]'
  target_id: method:bidirectional-entailment-clustering
  confidence: high
- type: related_to
  target: '[[lexical-entropy-overestimates-uncertainty-under-paraphrase]]'
  target_id: mechanism:lexical-entropy-overestimates-uncertainty-under-paraphrase
  confidence: high
- type: related_to
  target: '[[sft-abstention-overfits-indomain]]'
  target_id: mechanism:sft-abstention-overfits-indomain
  confidence: high
- type: related_to
  target: '[[accuracy-engagement-distance]]'
  target_id: metric:accuracy-engagement-distance
  confidence: high
- type: related_to
  target: '[[low-rank-adaptation]]'
  target_id: method:low-rank-adaptation
  confidence: high
---

Semantic entropy clusters sampled responses by meaning rather than token sequence, making the abstain/answer partition invariant to lexical and syntactic paraphrasing. This cleaner uncertainty signal produces a finer-grained split of training data: questions the model genuinely does not know (high semantic entropy) are relabeled to abstain, while questions with consistent meaning across samples (low semantic entropy) are answered normally. The resulting SFT target is more aligned with the model's actual knowledge boundary than either correctness labels (which require external ground truth) or token-level entropy (which conflates semantic uncertainty with paraphrase diversity). The advantage is larger in Long-QA than Short-QA because short answers have less paraphrase variation, so classical entropy and semantic entropy give more similar signals in that setting. R-Tuning-U's Long-QA in-distribution AED of 0.521 is worse than the unfine-tuned model (0.380), showing that token-level entropy as an abstention signal can actively harm Long-QA performance. SE (Llama), using a stronger entailment model, outperforms SE (DeBERTa) in most Long-QA settings, indicating that entailment model quality is a secondary lever.
