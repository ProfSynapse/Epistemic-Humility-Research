---
aliases:
- BingRel dataset
- Bing web-crawled relational prompts
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:bingrel
  type: dataset
  status: canonical
area: factual-knowledge-probing
related:
- '[[2104.08696--knowledge-neurons-pretrained-transformers]]'
- '[[pararel]]'
- '[[knowledge-neurons]]'
relationships:
- type: proposed_by
  target: '[[2104.08696--knowledge-neurons-pretrained-transformers]]'
  target_id: paper:2104.08696
  confidence: high
- type: related_to
  target: '[[pararel]]'
  target_id: dataset:pararel
---

BingRel is a dataset constructed by crawling Bing search results to collect open-domain texts expressing 27,738 relational facts drawn from [[pararel]], yielding 210,217 head-plus-tail texts and 266,020 head-only texts across 27 relation types. It was introduced to validate that [[knowledge-neurons]] identified on templated cloze prompts also activate on naturally occurring web text expressing the same facts. Unlike [[pararel]], which uses manually authored prompt templates, BingRel provides unseen, natural-language contexts.

**Why it matters here:** Demonstrating that knowledge neurons generalize to web text supports the claim that they capture genuinely stored relational knowledge rather than surface-form artifacts, strengthening the mechanistic grounding needed to reason about a model's knowledge boundary and hallucination risk.

**Lineage:** derived relationally from [[pararel]] (shares the same 27,738 facts); used as an out-of-template generalization test for [[knowledge-neurons]].
