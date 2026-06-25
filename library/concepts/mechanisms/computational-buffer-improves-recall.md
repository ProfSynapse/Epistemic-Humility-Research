---
aliases:
- filler reasoning tokens improve recall
- compute buffer raises pass@k
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:computational-buffer-improves-recall
  type: mechanism
  status: canonical
cause: "Conditioning the final answer on extra reasoning tokens that carry no task-relevant semantic content (a dummy 'Let me think.' trace repeated to length), in reasoning ON mode."
effect: "pass@1 and pass@k rise over reasoning OFF (accuracy 0.206 to 0.262 on SimpleQA-Verified, 0.457 to 0.554 on EntityQuestions), but the gain is bounded and non-monotonic in trace length (improving to roughly 2048 tokens then declining), and never fully reaches real reasoning ON."
polarity: increases
related:
- '[[2603.09906--thinking-recall-how-reasoning-unlocks-parametric-knowledge]]'
- '[[computational-buffer-effect]]'
- '[[pass-at-k]]'
relationships:
- type: supported_by
  target: '[[2603.09906--thinking-recall-how-reasoning-unlocks-parametric-knowledge]]'
  target_id: paper:2603.09906
  confidence: high
- type: related_to
  target: '[[computational-buffer-effect]]'
  target_id: term:computational-buffer-effect
  confidence: high
---

Extra reasoning tokens give the model room to perform latent computation independent of trace content, raising factual recall even when the trace is meaningless (Figure 4). A control comparing ON Dummy to ON Single Dummy rules out an ON-mode training-preference confounder, isolating computation length as the cause. The effect saturates and then reverses past an optimal length (Figure 5), so it is bounded and cannot account for all reasoning gains.
