---
aliases:
- lmsys-chat
- LMSYS-Chat-1M
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:lmsys-chat-1m
  type: dataset
  status: canonical
area: evaluation
related:
- '[[2507.21509--persona-vectors-monitoring-controlling-character-traits-language]]'
relationships:
- type: related_to
  target: '[[2507.21509--persona-vectors-monitoring-controlling-character-traits-language]]'
  target_id: paper:2507.21509
---

LMSYS-Chat-1M is a dataset of one million real-world conversations between users and 25 different LLMs, collected by the LMSYS organization and spanning heterogeneous topics, languages, and task types. It is used to validate [[persona-vectors]]-based data screening at scale on naturalistic content, including confirmation that high [[projection-difference]] samples continue to induce elevated trait expression even after LLM-based content filtering removes explicit harmful cues.

**Why it matters here:** Real-world user conversations expose a far broader prompting distribution than curated benchmarks, making LMSYS-Chat-1M a critical out-of-distribution stress test for whether persona-monitoring tools generalize to the naturalistic variation encountered in deployed systems.

**Lineage:** no formal derivation edges; used alongside controlled benchmarks to validate [[persona-vectors]] screening under naturalistic distributional shift.
