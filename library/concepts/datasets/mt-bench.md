---
aliases:
- MT-Bench
- Multi-turn Benchmark
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:mt-bench
  type: dataset
  status: canonical
area: datasets
related:
- '[[llm-as-judge]]'
- '[[2608.14392--tripwire-triggering-aligned-refusal-statistically-certified-safety]]'
relationships:
- type: related_to
  target: '[[llm-as-judge]]'
  target_id: method:llm-as-judge
  confidence: high
- type: related_to
  target: '[[2608.14392--tripwire-triggering-aligned-refusal-statistically-certified-safety]]'
  target_id: paper:2608.14392
  confidence: high
  note: "Used as the general-utility benchmark to measure the safety/utility trade-off of neuron-level jailbreak defenses."
---

MT-Bench is a multi-turn instruction-following benchmark whose responses are scored by an LLM judge, used as a general-purpose measure of model utility and helpfulness.

**Why it matters here:** in safety-defense papers, MT-Bench (and a keyword-matched over-refusal rate on its benign prompts) is the standard way to quantify how much a jailbreak defense degrades normal usability, i.e. the utility side of the safety/utility trade-off.

**Lineage:** widely adopted general-purpose LLM evaluation benchmark; no direct lineage to other atoms in this vault.
