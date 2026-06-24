---
aliases:
- SFT degrades ECE
- instruction tuning harms calibration
- alignment-degrades-calibration
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:instruction-tuning-degrades-logit-calibration
  type: mechanism
  status: canonical
cause: "Fine-tuning a pretrained language model with instruction-response pairs ([[instruction-tuning]]), especially on small or homogeneous datasets"
effect: "ECE increases (calibration worsens) across CLM, factual entity prediction, and multiple-choice tasks; degradation grows with additional training epochs"
polarity: increases
related:
- '[[2311.13240--calibration-of-llms-and-alignment]]'
- '[[instruction-tuning]]'
- '[[expected-calibration-error]]'
- '[[calibration]]'
- '[[supervised-finetuning]]'
- '[[alpaca-dataset]]'
- '[[synthetic-data-concentration-amplifies-calibration-harm]]'
- '[[lora-regularizes-calibration]]'
relationships:
- type: supported_by
  target: '[[2311.13240--calibration-of-llms-and-alignment]]'
  target_id: paper:2311.13240
  confidence: high
- type: related_to
  target: '[[instruction-tuning]]'
  target_id: method:instruction-tuning
  confidence: high
- type: related_to
  target: '[[expected-calibration-error]]'
  target_id: metric:expected-calibration-error
  confidence: high
- type: related_to
  target: '[[calibration]]'
  target_id: term:calibration
  confidence: high
- type: related_to
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
  confidence: high
- type: related_to
  target: '[[alpaca-dataset]]'
  target_id: dataset:alpaca-dataset
  confidence: high
- type: related_to
  target: '[[synthetic-data-concentration-amplifies-calibration-harm]]'
  target_id: mechanism:synthetic-data-concentration-amplifies-calibration-harm
  confidence: high
- type: related_to
  target: '[[lora-regularizes-calibration]]'
  target_id: mechanism:lora-regularizes-calibration
  confidence: high
---

Instruction tuning on small instruction datasets shifts the model's token probability distribution toward confident, instruction-formatted outputs, decoupling predicted probability from empirical accuracy. The calibration harm grows with more epochs because the model increasingly overfits the narrow distribution of the instruction corpus. This is distinct from the over-abstention mechanism (which requires refusal-focused training data): general-purpose instruction tuning on any small dataset causes this ECE increase. Zhu et al. (2311.13240) document it across all three evaluation tasks for LLaMA-7B fine-tuned on Alpaca and OA, with Alpaca causing more harm due to lower semantic diversity.
