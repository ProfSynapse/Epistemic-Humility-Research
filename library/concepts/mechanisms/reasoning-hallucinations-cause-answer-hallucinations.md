---
aliases:
- hallucinated reasoning facts increase answer hallucination
- reasoning-stage errors propagate to final answer
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:reasoning-hallucinations-cause-answer-hallucinations
  type: mechanism
  status: canonical
cause: "A reasoning trace contains at least one hallucinated intermediate fact (labeled by a search-enabled Gemini-2.5-Flash verifier that may abstain when correctness is undeterminable)."
effect: "The final answer is substantially less likely to be correct: clean vs hallucinated traces yield 41.4% vs 26.4% correct on SimpleQA-Verified and 71.1% vs 32.2% on EntityQuestions, with a within-question regression slope below 1 (0.84 and 0.86) confirming the gap survives controlling for question difficulty."
polarity: increases
related:
- '[[2603.09906--thinking-recall-how-reasoning-unlocks-parametric-knowledge]]'
- '[[factual-priming]]'
- '[[hallucination]]'
relationships:
- type: supported_by
  target: '[[2603.09906--thinking-recall-how-reasoning-unlocks-parametric-knowledge]]'
  target_id: paper:2603.09906
  confidence: high
- type: related_to
  target: '[[factual-priming]]'
  target_id: term:factual-priming
  confidence: high
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
  confidence: high
---

Generative self-retrieval is powerful but fragile: because the primed facts are model-generated they can be hallucinated, and traces with a hallucinated intermediate fact propagate the error into the final answer (Section 5.3, Figure 7). The within-question analysis (slope 0.84 / 0.86) rules out question difficulty as the sole confounder, and the gap motivates a test-time selection strategy that prefers traces with verified, hallucination-free facts (Table 1).
