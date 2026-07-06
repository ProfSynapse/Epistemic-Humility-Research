---
aliases:
- mistake injection test
- CoT mistake perturbation
- Adding Mistakes (Mistake Injection Test)
tags:
- kg/method
- concept
- method
kg:
  id: method:adding-mistakes
  type: method
  status: canonical
area: verification
related:
- '[[2307.13702--measuring-faithfulness-chain-thought-reasoning]]'
- '[[chain-of-thought-prompting]]'
relationships:
- type: proposed_by
  target: '[[2307.13702--measuring-faithfulness-chain-thought-reasoning]]'
  target_id: paper:2307.13702
  confidence: high
- type: derived_from
  target: '[[chain-of-thought-prompting]]'
  target_id: method:chain-of-thought-prompting
---

Adding mistakes is a CoT faithfulness test that injects a plausible LLM-generated
error into one step of an otherwise correct chain-of-thought, then samples the
remaining reasoning and records whether the final answer changes relative to the
unperturbed baseline. A high rate of answer change (strong "mistake sensitivity")
indicates the model genuinely conditions on intermediate steps during inference,
whereas low sensitivity suggests the conclusion is determined independently of the
stated reasoning, pointing toward [[post-hoc-reasoning]].

**Why it matters here:** Answer sensitivity to injected errors provides causal
evidence that stated reasoning steps influence model outputs, which determines
whether confidence or uncertainty expressed within a chain-of-thought reflects
the model's actual epistemic process rather than decorative justification.

**Lineage:** derives from [[chain-of-thought-prompting]]; complements
[[early-answering]] and [[filler-tokens-test]] as the causal-perturbation arm of
the CoT faithfulness battery.
