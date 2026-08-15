---
title: surface-pattern-imitation-explains-low-resource-instruction-tuning-gains
aliases:
- semantics-stripped instructions match real instructions in low-resource IT
- delusive examples match correct examples in low-resource instruction tuning
- IT gains come from output-format and guessing, not instruction semantics
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:surface-pattern-imitation-explains-low-resource-instruction-tuning-gains
  type: mechanism
  status: canonical
cause: "Fine-tuning T5-large-lm-adapt (770M) on task instructions deliberately corrupted two ways in a low-resource setting (fewer than 5 training instances per task): simplified task definitions with all semantic content removed, leaving only output-space/format information, and delusive examples with deliberately wrong input-output mappings, compared against training on the real, uncorrupted instructions and examples."
effect: "Both corrupted-instruction variants reach performance comparable to training on the real instructions and examples (43% exact-match). A random-guessing baseline, which uses no content signal about the task at all, reaches 42.6% exact-match, essentially matching the instruction-tuned model, while both clear the untrained baseline (12.78%). In this low-resource regime, the measured instruction-tuning gain is not evidence the model is learning what the instruction's semantic content means; it is consistent with the model picking up superficial patterns, output format, and guessing."
polarity: complicates
related:
- '[[2305.11383--do-models-really-learn-follow-instructions-empirical]]'
- '[[superficial-alignment-hypothesis]]'
- '[[response-only-training-yields-instruction-following]]'
- '[[narrow-domain-finetuning-yields-broad-instruction-following]]'
relationships:
- type: supported_by
  target: '[[2305.11383--do-models-really-learn-follow-instructions-empirical]]'
  target_id: paper:2305.11383
  confidence: high
  evidence:
  - "2305.11383 abstract and instruction-data ablation section; low-resource setting, exact-match 12.78/43/42.6"
- type: related_to
  target: '[[superficial-alignment-hypothesis]]'
  target_id: term:superficial-alignment-hypothesis
  confidence: medium
  evidence:
  - "adjacent but stronger claim than LIMA's superficial alignment hypothesis: not just that SFT surfaces pre-existing style, but that training on semantically wrong instructions matches training on correct ones in this regime"
- type: related_to
  target: '[[response-only-training-yields-instruction-following]]'
  target_id: mechanism:response-only-training-yields-instruction-following
  confidence: medium
  evidence:
  - "Hewitt et al.'s response tuning strips the instruction entirely; this paper corrupts the instruction's semantics while keeping its format, a complementary manipulation with a similar upshot"
- type: related_to
  target: '[[narrow-domain-finetuning-yields-broad-instruction-following]]'
  target_id: mechanism:narrow-domain-finetuning-yields-broad-instruction-following
  confidence: low
---

Kung and Peng corrupt the (instruction, response) training signal two
independent ways, holding the low-resource data budget fixed (fewer than
five instances per task), and find neither corruption costs the model
anything measurable: training on semantics-stripped task definitions, or
on examples with deliberately wrong input-output mappings, matches
training on the genuine instructions. A random-guessing baseline reaches
nearly the same score as the instruction-tuned model (42.6% versus 43%
exact-match), both well above the untrained baseline (12.78%). The
authors' own reading is that the impressive-looking instruction-tuning
gain in this regime is explained by models picking up superficial output-
format patterns and guessing, not by learning what the instruction's
content actually specifies.

**Why it matters here:** the qualifier is load-bearing: this result is
scoped to the low-resource setting, and the paper's own full-data
comparisons (200 instances per task) show the corrupted variants no
longer tracking the real instructions as closely. Cite the 42.6/43/12.78
comparison only with the low-resource qualifier attached. This is the
training-side complement to prompt-side findings in this program: just as
stripping the abstention affordance from a prompt at inference time
removes measured abstention from every objective except SFT (see
[[only-sft-installs-abstention-in-weights]]), stripping the instruction's
semantic content at training time (while keeping its format) leaves
low-resource instruction-tuning performance largely intact.

**Lineage:** established in
[[2305.11383--do-models-really-learn-follow-instructions-empirical]]
(Kung and Peng 2023, ACL 2023, refereed).
