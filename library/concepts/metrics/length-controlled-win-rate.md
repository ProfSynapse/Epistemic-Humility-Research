---
aliases:
- LC win rate
- Length-controlled win rate
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:length-controlled-win-rate
  type: metric
  status: canonical
area: metrics
related:
- '[[2603.00425--weight-updates-as-activation-shifts-principled-framework]]'
- '[[gpt4-win-rate]]'
relationships:
- type: used_by
  target: '[[2603.00425--weight-updates-as-activation-shifts-principled-framework]]'
  target_id: paper:2603.00425
  confidence: high
- type: related_to
  target: '[[gpt4-win-rate]]'
  target_id: metric:gpt4-win-rate
  confidence: high
---

Length-controlled win rate compares instruction-following outputs while
adjusting for response-length effects. The paper reports this metric for its
AlpacaEval instruction-tuning experiment.

**Why it matters here:** The adjustment helps separate behavioral quality from
a preference judge's tendency to favor longer answers.

**Lineage:** It is a controlled variant of model-judged response win rate,
related to [[gpt4-win-rate]].
