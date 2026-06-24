---
aliases:
- noncompliance SFT causes over-refusal
- continued SFT on noncompliance data collapses contrast compliance
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:full-sft-on-noncompliance-data-causes-over-refusal
  type: mechanism
  status: canonical
cause: "Full continued SFT of an instruction-tuned model on a noncompliance-only dataset (CoCoNot) without a contrastive compliance signal"
effect: "Model over-generalizes noncompliance behavior, incorrectly refusing benign requests that should be answered (contrast-set compliance collapses from ~92% to ~31%)"
polarity: enables
related:
- '[[2407.12043--coconot-art-of-saying-no]]'
- '[[supervised-finetuning]]'
- '[[coconot]]'
- '[[contextual-noncompliance-taxonomy]]'
- '[[over-abstention]]'
- '[[sft-abstention-causes-over-refusal]]'
- '[[sft-abstention-overfits-indomain]]'
- '[[direct-preference-optimization]]'
- '[[narrow-sft-data-collapses-output-diversity]]'
relationships:
- type: supported_by
  target: '[[2407.12043--coconot-art-of-saying-no]]'
  target_id: paper:2407.12043
  confidence: high
- type: related_to
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
  confidence: high
- type: related_to
  target: '[[coconot]]'
  target_id: dataset:coconot
  confidence: high
- type: related_to
  target: '[[contextual-noncompliance-taxonomy]]'
  target_id: term:contextual-noncompliance-taxonomy
  confidence: high
- type: related_to
  target: '[[over-abstention]]'
  target_id: term:over-abstention
  confidence: high
- type: related_to
  target: '[[sft-abstention-causes-over-refusal]]'
  target_id: mechanism:sft-abstention-causes-over-refusal
  confidence: high
- type: related_to
  target: '[[sft-abstention-overfits-indomain]]'
  target_id: mechanism:sft-abstention-overfits-indomain
  confidence: high
- type: related_to
  target: '[[direct-preference-optimization]]'
  target_id: method:direct-preference-optimization
  confidence: high
- type: related_to
  target: '[[narrow-sft-data-collapses-output-diversity]]'
  target_id: mechanism:narrow-sft-data-collapses-output-diversity
  confidence: high
---

Continued SFT of Tulu-2 7B on CoCoNot alone reduces Incomplete compliance to 1.3% and achieves near-zero Safety and Humanizing compliance; but contrast-set compliance drops catastrophically from 92.4% (SFT baseline) to 31.4%. Including a matched-sized subset of Tulu2Mix recovers some general capability (AlpacaEval to 65.7%) but contrast-set compliance recovers only to 54.9%, still far below baseline. SFT from scratch on T2M(all)+CoCoNot also shows this pattern: near-zero noncompliance compliance rates but contrast-set at 74.9%. The mechanism parallels the pattern in the idk-dataset literature: without a contrastive compliant-response signal, the model generalizes refusal too broadly. CoCoNot addresses this with CoCoNot-Pref (DPO) as a corrective stage.
