---
aliases:
- LoRA prevents capability collapse during noncompliance training
- LoRA preserves general capabilities under noncompliance SFT
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:lora-limits-catastrophic-forgetting-under-noncompliance-sft
  type: mechanism
  status: canonical
cause: "Continued LoRA finetuning of an instruction-tuned model on noncompliance data (CoCoNot)"
effect: "General capabilities (MMLU, AlpacaEval) are preserved at near-baseline levels while noncompliance compliance rates decrease substantially across categories, and contrast-set compliance remains above 88%"
polarity: enables
related:
- '[[2407.12043--coconot-art-of-saying-no]]'
- '[[low-rank-adaptation]]'
- '[[supervised-finetuning]]'
- '[[coconot]]'
- '[[contextual-noncompliance-taxonomy]]'
- '[[over-abstention]]'
- '[[sft-abstention-causes-over-refusal]]'
- '[[lora-regularizes-calibration]]'
relationships:
- type: supported_by
  target: '[[2407.12043--coconot-art-of-saying-no]]'
  target_id: paper:2407.12043
  confidence: high
- type: related_to
  target: '[[low-rank-adaptation]]'
  target_id: method:low-rank-adaptation
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
  target: '[[lora-regularizes-calibration]]'
  target_id: mechanism:lora-regularizes-calibration
  confidence: high
---

When an instruction-tuned model (Tulu-2 7B) is continued-finetuned with full parameter updates on noncompliance data alone, AlpacaEval win-rate collapses from 73.9% to 18.7% and contrast-set compliance drops to 31.4%. LoRA confines updates to low-rank parameter subspaces, which empirically limits catastrophic forgetting: the LoRA-tuned model reaches MMLU 50.0 and AlpacaEval 74.2% (versus the baseline 50.4 / 73.9), while reducing Incomplete compliance from 25.8% to 17.8%. The finding is consistent with the general LoRA result that low-rank adaptation learns less but forgets less. The merged-adapter variant (LoRA trained on Tulu-2-no-refusal, merged with Tulu-2 weights) achieves contrast-set compliance 88.9%, outperforming GPT-4's baseline compliance rates on CoCoNot.
