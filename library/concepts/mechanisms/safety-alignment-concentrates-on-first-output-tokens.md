---
aliases:
- Refusal-prefix shortcut
- Prefix-forcing reveals base-model behavior
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:safety-alignment-concentrates-on-first-output-tokens
  type: mechanism
  status: canonical
cause: "Standard safety alignment (SFT + RLHF/DPO) on a chat model, then measuring harmfulness after prefilling the decoding process with the model's own typical refusal prefix (e.g. \"I cannot\", \"I apologize\")"
effect: "An unaligned base model's harmfulness rate collapses toward the aligned model's near-zero rate once the refusal prefix is forced at the start of decoding, showing the aligned model's safety behavior is concentrated in the choice of first few tokens rather than distributed across the full response"
polarity: mediates
related:
- '[[2406.05946--safety-alignment-should-be-made-more-than]]'
- '[[shallow-safety-alignment]]'
relationships:
- type: supported_by
  target: '[[2406.05946--safety-alignment-should-be-made-more-than]]'
  target_id: paper:2406.05946
  confidence: high
- type: related_to
  target: '[[shallow-safety-alignment]]'
  target_id: term:shallow-safety-alignment
  confidence: high
---

On the HEx-PHI safety benchmark, Llama-2-7B-Chat begins its response with "I cannot" or "I apologize" in 96.1% of harmful instructions, and Gemma-7B-1.1-IT begins with "I am unable" in 96.7% (Section 2.2). With no prefix forced, the unaligned Llama-2-7B base model has a 68.6% harmfulness rate versus ~0% for the aligned chat model; but once the base model's decoding is prefilled with the refusal prefix "I cannot", its harmfulness rate collapses to 16.4%, and with the longer prefix "I cannot fulfill" to 5.4% (Table 1, Section 2.2). Gemma-7B base shows the same pattern (85.4% with no prefix, down to single digits with a refusal prefix forced). This demonstrates that most of what alignment training changes is the model's tendency to emit a refusal token at the very start of generation; once that token is present, the base model's own completion distribution is already mostly safe, meaning the "alignment" work being done by training is concentrated in only the first few output tokens.
