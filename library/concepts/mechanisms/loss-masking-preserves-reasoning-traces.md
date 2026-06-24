---
aliases:
- masked-think strategy
- response-only masking
- reasoning-aware loss masking
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:loss-masking-preserves-reasoning-traces
  type: mechanism
  status: canonical
cause: "Excluding empty reasoning regions (masked-think) or both prompt and reasoning (response-only) from the supervised fine-tuning loss signal on instruction-response data without explicit traces"
effect: "Substantially preserved valid reasoning rate (VR) during fine-tuning, without requiring teacher-generated reasoning traces, while still allowing task adaptation"
polarity: prevents
related:
- '[[2605.21127--silent-reasoning-trace-suppression]]'
- '[[reasoning-trace-collapse]]'
- '[[valid-reasoning-rate]]'
- '[[format-induced-reasoning-trace-collapse]]'
- '[[supervised-finetuning]]'
- '[[low-rank-adaptation]]'
relationships:
- type: supported_by
  target: '[[2605.21127--silent-reasoning-trace-suppression]]'
  target_id: paper:2605.21127
  confidence: high
- type: related_to
  target: '[[reasoning-trace-collapse]]'
  target_id: term:reasoning-trace-collapse
  confidence: high
- type: related_to
  target: '[[valid-reasoning-rate]]'
  target_id: metric:valid-reasoning-rate
  confidence: high
- type: related_to
  target: '[[format-induced-reasoning-trace-collapse]]'
  target_id: mechanism:format-induced-reasoning-trace-collapse
  confidence: high
- type: related_to
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
  confidence: high
- type: related_to
  target: '[[low-rank-adaptation]]'
  target_id: method:low-rank-adaptation
  confidence: high
---

By removing the loss gradient from regions where reasoning is absent, masking prevents the model from being directly rewarded for omitting reasoning. For Qwen3-8B, Nemotron-7B, and Llama-R1-8B, both masked-think and response-only maintain high out-of-domain VR and substantially more in-domain Chemistry VR than standard fine-tuning. For OLMo-3-7B, masking helps but cannot fully overcome a tendency toward truncated reasoning. Masking changes the failure profile: remaining invalid traces shift toward truncation rather than empty or missing reasoning. Teacher distillation outperforms masking on VR for Qwen3-8B and Llama-R1-8B but fails for OLMo-3-7B, so masking is the more reliable lightweight mitigation when trace generation is costly.
