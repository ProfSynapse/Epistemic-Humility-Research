---
aliases:
- LLM judge
- LLM evaluator
- automatic abstention evaluation
- LLM-as-Judge
tags:
- kg/method
- concept
- method
kg:
  id: method:llm-as-judge
  type: method
  status: canonical
area: methods
related:
- '[[abstentionbench]]'
- '[[abstention-recall]]'
- '[[instruction-tuning]]'
relationships:
- type: related_to
  target: '[[abstentionbench]]'
  target_id: dataset:abstentionbench
- type: related_to
  target: '[[abstention-recall]]'
  target_id: metric:abstention-recall
- type: related_to
  target: '[[instruction-tuning]]'
  target_id: method:instruction-tuning
---

LLM-as-Judge is an evaluation method that uses a separate language model to
automatically score a generated response against a criterion, outputting a
verdict (here binary yes/no: did the model abstain?) given the question and
response as context. AbstentionBench uses Llama 3.1 8B Instruct as the judge
to enable consistent, scalable scoring across 20 datasets without requiring
human annotation for every response.

**Why it matters here:** The locked training-regimen abstention study inherits the automated
evaluation convention from AbstentionBench, so the reliability of LLM-as-Judge
for abstention detection is a prerequisite assumption that affects the validity
of all downstream metric comparisons across SFT, DPO, and KTO training arms.

**Lineage:** used by [[abstentionbench]] to score [[abstention-recall]]; related
to [[instruction-tuning]] in that the judge model is itself an instruction-tuned
LLM.
