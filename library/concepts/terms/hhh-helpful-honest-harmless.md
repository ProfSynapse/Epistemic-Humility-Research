---
aliases:
- HHH
- Helpful, Honest, and Harmless
tags:
- kg/term
- concept
- term
kg:
  id: term:hhh-helpful-honest-harmless
  type: term
  status: canonical
area: terms
related:
- '[[2112.00861--general-language-assistant-as-laboratory-alignment]]'
- '[[context-distillation]]'
relationships:
- type: proposed_by
  target: '[[2112.00861--general-language-assistant-as-laboratory-alignment]]'
  target_id: paper:2112.00861
  confidence: high
- type: related_to
  target: '[[context-distillation]]'
  target_id: method:context-distillation
  confidence: high
---

Askell et al. (2021, Anthropic) define an AI as "aligned" if it is Helpful, Honest, and Harmless (HHH). The paper operationalizes this as a prompting target and evaluation criterion: a hand-written HHH prompt conditions a base language-model assistant toward this behavior, and HHH-style evaluations (alongside TruthfulQA and toxicity metrics) measure how well models satisfy it.

**Why it matters here:** HHH is the earliest explicit prompting-first alignment target in this line of work, predating and motivating later comparisons between prompted and trained alignment (LIMA, URIAL).
