---
aliases:
- instruction finetuning
- RLHF instruction following
tags:
- kg/method
- concept
- method
kg:
  id: method:instruction-tuning
  type: method
  status: canonical
area: methods
---

Instruction tuning is a finetuning procedure that trains a language model on instruction-response pairs to improve its ability to follow natural-language directions. Compared to base pretrained models, instruction-tuned models exhibit stronger task-following, better formatting compliance, and improved alignment with user intent across diverse zero-shot prompts.

**Why it matters here:** Instruction tuning is the baseline training regime that precedes preference optimization in the SFT-vs-DPO-vs-KTO pipeline. The study examines whether adding abstention-specific finetuning on top of an instruction-tuned base (via [[idk-sft]], DPO, or KTO) can improve self-knowledge without incurring an unacceptable [[alignment-tax]]. The mechanism [[instruction-tuning-causes-over-abstention]] also flags a key failure mode this study must navigate.

**Lineage:** prerequisite to [[direct-preference-optimization]] and [[kahneman-tversky-optimization]] training runs; related to [[supervised-finetuning]] (which is the more general term).
