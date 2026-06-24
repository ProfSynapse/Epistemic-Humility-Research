---
aliases:
- composite reward installs output format
- GRPO reward teaches ignorance structure
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:grpo-composite-reward-installs-epistemic-output-schema
  type: mechanism
  status: canonical
cause: "GRPO fine-tuning with a decomposed composite reward (retrieval utility + concept specificity + format validity) on cross-domain unknown-unknown queries"
effect: "The model learns to produce structured JSON declarations of ignorance (SICs) with high format validity (99.46%) and concept specificity (0.967 CSS) instead of hallucinating fluent answers"
polarity: enables
related:
- '[[2606.08571--structured-ignorance-certificates]]'
- '[[grpo-eliminates-critic-reduces-memory]]'
- '[[sic-composite-reward]]'
- '[[structured-ignorance-certificates]]'
- '[[abstention-generalization-failure]]'
- '[[rule-based-verifier-causes-training-collapse]]'
relationships:
- type: supported_by
  target: '[[2606.08571--structured-ignorance-certificates]]'
  target_id: paper:2606.08571
  confidence: high
- type: related_to
  target: '[[grpo-eliminates-critic-reduces-memory]]'
  target_id: mechanism:grpo-eliminates-critic-reduces-memory
  confidence: high
- type: related_to
  target: '[[sic-composite-reward]]'
  target_id: method:sic-composite-reward
  confidence: high
- type: related_to
  target: '[[structured-ignorance-certificates]]'
  target_id: method:structured-ignorance-certificates
  confidence: high
- type: related_to
  target: '[[abstention-generalization-failure]]'
  target_id: mechanism:abstention-generalization-failure
  confidence: high
- type: related_to
  target: '[[rule-based-verifier-causes-training-collapse]]'
  target_id: mechanism:rule-based-verifier-causes-training-collapse
  confidence: high
---

The composite reward decomposes the quality of a structured ignorance declaration into three measurable sub-signals. GRPO optimizes each component jointly, producing a model that generates syntactically valid, informationally specific ignorance certificates on held-out cross-domain queries. The paraphrase-divergence probe confirms that the behavior reflects genuine unknown-unknown probability rather than surface pattern imitation.
