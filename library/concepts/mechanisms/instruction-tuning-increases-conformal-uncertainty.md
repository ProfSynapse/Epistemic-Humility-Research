---
aliases:
- instruction fine-tuning uncertainty increase
- chat model set size inflation
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:instruction-tuning-increases-conformal-uncertainty
  type: mechanism
  status: canonical
cause: "Instruction fine-tuning of a pretrained LLM (either Chat-V1 instruction-format or Chat-V2 base-format prompting on the chat checkpoint)"
effect: "Average conformal prediction set size (SS) increases and UAcc decreases relative to the base model across multiple model sizes and tasks"
polarity: increases
related:
- '[[2401.12794--llm-uncertainty-bench-conformal]]'
- '[[conformal-prediction-for-llm-uncertainty]]'
- '[[uncertainty-aware-accuracy]]'
- '[[instruction-tuning]]'
- '[[supervised-finetuning]]'
- '[[instruction-tuning-causes-over-abstention]]'
relationships:
- type: supported_by
  target: '[[2401.12794--llm-uncertainty-bench-conformal]]'
  target_id: paper:2401.12794
  confidence: high
- type: related_to
  target: '[[conformal-prediction-for-llm-uncertainty]]'
  target_id: method:conformal-prediction-for-llm-uncertainty
  confidence: high
- type: related_to
  target: '[[uncertainty-aware-accuracy]]'
  target_id: metric:uncertainty-aware-accuracy
  confidence: high
- type: related_to
  target: '[[instruction-tuning]]'
  target_id: method:instruction-tuning
  confidence: high
- type: related_to
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
  confidence: high
- type: related_to
  target: '[[instruction-tuning-causes-over-abstention]]'
  target_id: mechanism:instruction-tuning-causes-over-abstention
  confidence: high
---

Across all three sizes of the Llama-2 series (7B, 13B, 70B), both prompting variants of the instruction-tuned chat model show higher conformal SS than the corresponding base model. Chat-V1 also reduces accuracy; Chat-V2 can preserve or increase accuracy for smaller sizes (7B, 13B) while still inflating SS. The finding generalizes to Yi, DeepSeek, and Falcon series per Appendix C.3. The mechanism is consistent with instruction tuning diffusing the softmax distribution over answer options relative to the base model, making the conformal set larger to meet the coverage guarantee. Observed in 2401.12794 §6.5.
