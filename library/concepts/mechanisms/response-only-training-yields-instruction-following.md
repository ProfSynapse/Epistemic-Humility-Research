---
aliases:
- Response tuning yields instruction following
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:response-only-training-yields-instruction-following
  type: mechanism
  status: canonical
cause: "Applying [[response-tuning]] (fine-tuning on responses alone, with every paired instruction stripped to the empty string) to a base LLM using the 1,030-example LIMA dataset"
effect: "The response-tuned model wins against the same base model's instruction-tuned counterpart on AlpacaEval roughly 43% of the time, far above the base model's own single-digit win rate, despite never seeing an instruction during training"
polarity: enables
related:
- '[[2409.14254--instruction-following-without-instruction-tuning]]'
- '[[response-tuning]]'
- '[[implicit-instruction-tuning]]'
- '[[lima]]'
relationships:
- type: supported_by
  target: '[[2409.14254--instruction-following-without-instruction-tuning]]'
  target_id: paper:2409.14254
  confidence: high
- type: related_to
  target: '[[response-tuning]]'
  target_id: method:response-tuning
  confidence: high
- type: related_to
  target: '[[implicit-instruction-tuning]]'
  target_id: term:implicit-instruction-tuning
  confidence: high
- type: related_to
  target: '[[lima]]'
  target_id: dataset:lima
  confidence: medium
---

Hewitt et al. (2024) fine-tune Llama-2-7B and OLMo-7B-Feb2024 on the 1,030-example LIMA dataset with instructions stripped to the empty string (response tuning) and measure AlpacaEval length-controlled win rate against the same base model instruction-tuned normally. Base models win in the single digits (Llama-2-7B: 2.4% +/- 0.14%; OLMo-7B: 4.7% +/- 0.57%), but response-tuned models win roughly 43% of the time (Llama-2-7B: 43.3% +/- 1.1%; OLMo-7B: 43.7% +/- 1.7%), approaching the 50% mark that would denote equal quality to full instruction tuning (Section 4.1, Table 1). Since response tuning never pairs any response with its instruction during training, this shows most of what instruction tuning does for AlpacaEval-style quality is teachable by shifting the model's marginal output distribution toward "desirable response" style, without any signal that ties specific responses to specific instructions.
