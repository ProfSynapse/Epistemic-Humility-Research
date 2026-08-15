---
aliases:
- Response-only training
- Response tuning
tags:
- kg/method
- concept
- method
kg:
  id: method:response-tuning
  type: method
  status: canonical
area: methods
related:
- '[[2409.14254--instruction-following-without-instruction-tuning]]'
- '[[implicit-instruction-tuning]]'
- '[[supervised-finetuning]]'
relationships:
- type: proposed_by
  target: '[[2409.14254--instruction-following-without-instruction-tuning]]'
  target_id: paper:2409.14254
  confidence: high
- type: related_to
  target: '[[implicit-instruction-tuning]]'
  target_id: term:implicit-instruction-tuning
  confidence: high
- type: related_to
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
  confidence: high
---

Given an instruction-tuning dataset of (instruction, response) pairs, response tuning discards every instruction, replacing it with the empty string, and fine-tunes the model only to raise the marginal likelihood of the responses: min_theta (1/k) sum_i -log p_theta(response_i | empty string). Unlike ordinary instruction tuning, which learns the conditional p(y|x), response tuning can only directly teach the desired distribution of outputs p(y), with no training signal that ties any particular response to any particular instruction.

**Why it matters here:** response tuning isolates whether the (instruction, response) *pairing* is doing real work in instruction tuning, or whether merely nudging the output distribution toward "assistant-shaped" responses is what matters. Hewitt et al. find the latter is largely sufficient (see [[response-only-training-yields-instruction-following]]), which is directly relevant to disentangling what SFT on abstention data teaches: the specific instruction-to-abstention mapping, or just a shift in the model's default response distribution.
