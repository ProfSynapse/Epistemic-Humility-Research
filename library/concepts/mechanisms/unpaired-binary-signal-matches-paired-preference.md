---
aliases:
- Binary desirability signal matches paired-preference performance
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:unpaired-binary-signal-matches-paired-preference
  type: mechanism
  status: canonical
cause: Training with [[kahneman-tversky-optimization]] on unpaired binary desirability labels (good/bad) instead of [[preference-pair-data]]
effect: Alignment quality equal to or exceeding [[direct-preference-optimization]] at scales from 1B to 30B parameters, despite learning from a weaker signal
polarity: enables
related:
- '[[2402.01306--kto-prospect-theoretic]]'
- '[[kahneman-tversky-optimization]]'
- '[[preference-pair-data]]'
- '[[direct-preference-optimization]]'
relationships:
- type: supported_by
  target: '[[2402.01306--kto-prospect-theoretic]]'
  target_id: paper:2402.01306
  confidence: high
- type: related_to
  target: '[[kahneman-tversky-optimization]]'
  target_id: method:kahneman-tversky-optimization
- type: related_to
  target: '[[preference-pair-data]]'
  target_id: dataset:preference-pair-data
- type: related_to
  target: '[[direct-preference-optimization]]'
  target_id: method:direct-preference-optimization
---

KTO frames alignment as a prospect-theoretic utility maximization over individual (response, label) pairs, so it does not require contrastive preference pairs at all. Because it matches or exceeds DPO without paired data, data collection pipelines can use simpler binary annotations rather than pairwise comparisons. The KTO paper (arXiv:2402.01306) validates this across 1B to 30B parameter models on instruction-following benchmarks.
