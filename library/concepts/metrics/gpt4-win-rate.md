---
aliases:
- win rate
- GPT-4 judge win rate
- LLM-as-judge win rate
- GPT-4 Win Rate
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:gpt4-win-rate
  type: metric
  status: canonical
area: metrics
related:
- '[[llm-as-judge]]'
relationships:
- type: related_to
  target: '[[llm-as-judge]]'
  target_id: method:llm-as-judge
---

GPT-4 win rate is an automatic evaluation metric where GPT-4 acts as a judge and decides whether a candidate model's response is preferred over a reference response (typically the SFT baseline), scoring the comparison for helpfulness, harmlessness, and conciseness. A win rate above 50% indicates the candidate model matches or exceeds reference quality in the eyes of the GPT-4 judge.

**Why it matters here:** The KTO paper uses GPT-4 win rate against the SFT target as the headline alignment metric, complementing automatic benchmarks and making it relevant when comparing DPO and KTO alignment quality in the abstention study.

**Lineage:** related to [[llm-as-judge]]; used in [[2402.01306--kto-prospect-theoretic]].
