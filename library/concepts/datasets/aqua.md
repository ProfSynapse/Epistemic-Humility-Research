---
aliases:
- AQuA
- Algebra Question Answering
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:aqua
  type: dataset
  status: canonical
area: datasets
related:
- '[[2603.00425--weight-updates-as-activation-shifts-principled-framework]]'
- '[[gsm8k]]'
relationships:
- type: used_by
  target: '[[2603.00425--weight-updates-as-activation-shifts-principled-framework]]'
  target_id: paper:2603.00425
  confidence: high
- type: related_to
  target: '[[gsm8k]]'
  target_id: dataset:gsm8k
  confidence: medium
---

AQuA is a multiple-choice algebra word-problem dataset with natural-language
rationales. The paper uses it to evaluate parameter-efficient adaptation on
mathematical reasoning.

**Why it matters here:** AQuA tests whether an intervention preserves and
adapts multi-step reasoning behavior.

**Lineage:** It complements the open-answer arithmetic benchmark [[gsm8k]].
