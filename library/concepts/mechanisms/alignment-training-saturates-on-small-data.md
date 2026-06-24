---
aliases:
- Preference alignment data saturation
- Small-data saturation in alignment
- Alignment optimal at 1K-10K examples
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:alignment-training-saturates-on-small-data
  type: mechanism
  status: canonical
cause: "Applying RL-free alignment methods (DPO, KTO, IPO, CPO) to an SFT-warmed model across increasing training-set sizes from hundreds to tens of thousands of preference pairs"
effect: "Peak task performance is achieved at 1K to 10K preference pairs and does not improve, and may degrade, with larger training sets, because the SFT phase absorbs most of the model's capacity for alignment and the preference stage only needs to make incremental corrections"
polarity: decreases
related:
- '[[2404.14723--insights-into-alignment-dpo-variants]]'
- '[[direct-preference-optimization]]'
- '[[kahneman-tversky-optimization]]'
- '[[identity-preference-optimization]]'
- '[[contrastive-preference-optimization]]'
- '[[supervised-finetuning]]'
- '[[preference-pair-data]]'
- '[[ultrafeedback]]'
relationships:
- type: supported_by
  target: '[[2404.14723--insights-into-alignment-dpo-variants]]'
  target_id: paper:2404.14723
  confidence: high
- type: related_to
  target: '[[direct-preference-optimization]]'
  target_id: method:direct-preference-optimization
  confidence: high
- type: related_to
  target: '[[kahneman-tversky-optimization]]'
  target_id: method:kahneman-tversky-optimization
  confidence: high
- type: related_to
  target: '[[identity-preference-optimization]]'
  target_id: method:identity-preference-optimization
  confidence: high
- type: related_to
  target: '[[contrastive-preference-optimization]]'
  target_id: method:contrastive-preference-optimization
  confidence: high
- type: related_to
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
  confidence: high
- type: related_to
  target: '[[preference-pair-data]]'
  target_id: dataset:preference-pair-data
  confidence: high
- type: related_to
  target: '[[ultrafeedback]]'
  target_id: dataset:ultrafeedback
  confidence: high
---

Saeidi et al. (2024, Figure 3) show that across all four alignment methods in Scenario 1, MT-Bench performance peaks within training sets of 1K--10K data points. The authors attribute the saturation to a division of labor: the SFT stage already instills the core behavioral patterns, leaving the preference stage to refine a model that has little residual room to improve with more paired examples. This mechanism is directly relevant to Phase 1 experiment design: Phase 1 runs do not require large preference datasets and may benefit from deliberately small budgets that avoid the degradation zone.
