---
aliases:
- reasoning ON/OFF toggle
- hybrid reasoning ablation
- reasoning ON/OFF
tags:
- kg/method
- concept
- method
kg:
  id: method:reasoning-toggle-ablation
  type: method
  status: canonical
area: methods
related:
- '[[2603.09906--thinking-recall-how-reasoning-unlocks-parametric-knowledge]]'
- '[[pass-at-k]]'
- '[[computational-buffer-effect]]'
- '[[factual-priming]]'
relationships:
- type: proposed_by
  target: '[[2603.09906--thinking-recall-how-reasoning-unlocks-parametric-knowledge]]'
  target_id: paper:2603.09906
  confidence: high
- type: related_to
  target: '[[pass-at-k]]'
  target_id: metric:pass-at-k
  confidence: medium
---

A controlled-experiment design that uses hybrid models whose reasoning can be switched ON or OFF via control tokens or system instructions, holding the underlying weights (and thus parametric knowledge) fixed. By comparing the same model in both modes, and by substituting reasoning traces with crafted variants (dummy filler traces for the compute effect; extracted fact lists for the content effect), it isolates which part of a reasoning gain comes from extra computation versus from recalled content.

**Why it matters here:** It is a clean template for attributing a behavioral change to reasoning rather than to a different model, and the trace-substitution variants (ON Dummy, ON Facts, OFF Facts) are reusable probes for testing whether a model's chain of thought is causally informative. The design controls for an ON/OFF training-preference confounder.

**Lineage:** Applies hybrid reasoning models (Gemini-2.5, Qwen3) and pass@k coverage; the dummy-trace and fact-extraction variants extend the filler-token (Goyal et al., 2024) and self-retrieval lines.
