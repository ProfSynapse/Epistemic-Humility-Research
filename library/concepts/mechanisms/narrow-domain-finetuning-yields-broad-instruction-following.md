---
aliases:
- Single-task finetuning yields instruction following
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:narrow-domain-finetuning-yields-broad-instruction-following
  type: mechanism
  status: canonical
cause: "Fine-tuning a base LLM via [[single-task-finetuning]] on a single narrow-domain input-output distribution (code, math derivations, poetry, recipes, or chess games) that has no resemblance to general instruction-following data"
effect: "The model gains substantial AlpacaEval win rate against instruction-tuned models on broad, out-of-domain instructions, far above the un-tuned base model's win rate, even though the fine-tuning data never targeted instruction following"
polarity: enables
related:
- '[[2409.14254--instruction-following-without-instruction-tuning]]'
- '[[single-task-finetuning]]'
- '[[implicit-instruction-tuning]]'
- '[[response-only-training-yields-instruction-following]]'
relationships:
- type: supported_by
  target: '[[2409.14254--instruction-following-without-instruction-tuning]]'
  target_id: paper:2409.14254
  confidence: high
- type: related_to
  target: '[[single-task-finetuning]]'
  target_id: method:single-task-finetuning
  confidence: high
- type: related_to
  target: '[[implicit-instruction-tuning]]'
  target_id: term:implicit-instruction-tuning
  confidence: high
- type: related_to
  target: '[[response-only-training-yields-instruction-following]]'
  target_id: mechanism:response-only-training-yields-instruction-following
  confidence: high
---

Hewitt et al. (2024) fine-tune Llama-2-7B and OLMo-7B-Feb2024 separately on five narrow single-task datasets (MBPP code generation, n=374; GSM8K math derivations, n=1000; Poetry, n=571; Recipes, n=1000; Chess PGN games, n=1000) and measure AlpacaEval win rate against fully instruction-tuned versions of the same base models on broad, out-of-domain instructions. Against a base-model win rate of 2.4% (Llama-2-7B) / 4.7% (OLMo-7B), single-task finetuning raises the win rate substantially on every dataset: MBPP 16.9%/10.4%, GSM 23.7%/30.3%, Poetry 22.9%/21.9%, Recipes 14.6%/21.5%, Chess 2.1%/6.3% (Section 5, Table 3). Even chess-game fine-tuning, the narrowest and most stylistically distant domain, meaningfully raises the win rate over the base model. When the evaluation instructions are very different in style from the narrow finetuning domain, the model's responses do not adopt the finetuning domain's style; the effect is broad instruction-following capability, not domain-specific imitation. This is direct evidence that adaptation not designed to teach instruction following can do so implicitly, and that the specific content of a narrow fine-tuning dataset is not the source of the broad behavioral shift.
