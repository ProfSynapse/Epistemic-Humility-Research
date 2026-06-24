---
aliases:
- HonestyBench
- Honesty Bench
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:honesty-bench
  type: dataset
  status: canonical
area: datasets
related:
- '[[2510.17509--elical-universal-honesty-alignment]]'
- '[[triviaqa]]'
- '[[pararel]]'
- '[[popqa]]'
- '[[mmlu]]'
- '[[consistency-based-confidence]]'
- '[[auroc]]'
- '[[elical]]'
relationships:
- type: proposed_by
  target: '[[2510.17509--elical-universal-honesty-alignment]]'
  target_id: paper:2510.17509
  confidence: high
- type: related_to
  target: '[[triviaqa]]'
  target_id: dataset:triviaqa
  confidence: medium
- type: related_to
  target: '[[pararel]]'
  target_id: dataset:pararel
  confidence: medium
- type: related_to
  target: '[[popqa]]'
  target_id: dataset:popqa
  confidence: medium
- type: related_to
  target: '[[mmlu]]'
  target_id: dataset:mmlu
  confidence: medium
- type: related_to
  target: '[[consistency-based-confidence]]'
  target_id: method:consistency-based-confidence
  confidence: medium
- type: related_to
  target: '[[auroc]]'
  target_id: metric:auroc
  confidence: medium
- type: related_to
  target: '[[elical]]'
  target_id: method:elical
  confidence: medium
---

A large-scale benchmark for universal LLM honesty alignment covering ten free-form factual QA datasets. Training split: 567,647 instances from NQ, TriviaQA, HotpotQA, 2WikiMultihopQA, and ParaRel. In-domain evaluation: 37,904 instances from the same five dataset splits. OOD evaluation: 32,805 instances from SQuAD, WebQuestions, CWQ, MuSiQue, and PopQA. Each question-model pair is annotated with one greedy response and k=20 sampled responses (temperature=1), labeled for both correctness and semantic self-consistency by Qwen2.5-32B-Instruct, for three LLMs (Qwen2.5-7B-Instruct, Qwen2.5-14B-Instruct, Llama3-8B-Instruct).

**Why it matters here:** Enables the first training-to-upper-bound study of honesty alignment at scale, providing both the annotation-efficiency curve (1k to 560k correctness labels) and a held-out OOD evaluation set covering genuinely new QA distributions. Its dual annotation (correctness and self-consistency) enables the EliCal two-stage training protocol.

**Lineage:** Extends the tradition of large-scale QA benchmarks (NQ, TriviaQA, HotpotQA) into a unified honesty-alignment testbed. The OOD split overlaps with popqa, triviaqa, and pararel which are already in the atom library.
