---
aliases:
- Contextually Comply Not
- CoCoNot dataset
- CoCoNot-Pref
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:coconot
  type: dataset
  status: canonical
area: datasets
related:
- '[[2407.12043--coconot-art-of-saying-no]]'
- '[[contextual-noncompliance-taxonomy]]'
- '[[over-abstention]]'
- '[[safety-refusal]]'
- '[[abstention]]'
- '[[supervised-finetuning]]'
- '[[low-rank-adaptation]]'
- '[[direct-preference-optimization]]'
- '[[llm-as-judge]]'
relationships:
- type: proposed_by
  target: '[[2407.12043--coconot-art-of-saying-no]]'
  target_id: paper:2407.12043
  confidence: high
- type: related_to
  target: '[[contextual-noncompliance-taxonomy]]'
  target_id: term:contextual-noncompliance-taxonomy
  confidence: medium
- type: related_to
  target: '[[over-abstention]]'
  target_id: term:over-abstention
  confidence: medium
- type: related_to
  target: '[[safety-refusal]]'
  target_id: term:safety-refusal
  confidence: medium
- type: related_to
  target: '[[abstention]]'
  target_id: term:abstention
  confidence: medium
- type: related_to
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
  confidence: medium
- type: related_to
  target: '[[low-rank-adaptation]]'
  target_id: method:low-rank-adaptation
  confidence: medium
- type: related_to
  target: '[[direct-preference-optimization]]'
  target_id: method:direct-preference-optimization
  confidence: medium
- type: related_to
  target: '[[llm-as-judge]]'
  target_id: method:llm-as-judge
  confidence: medium
---

A benchmark and training resource for contextual noncompliance in language models, comprising 1001 human-verified evaluation prompts and 11,477 training prompt-response pairs spanning five noncompliance categories (Incomplete, Unsupported, Indeterminate, Safety, Humanizing), plus a 379-prompt contrast evaluation set and 927 contrastive preference pairs (CoCoNot-Pref) for DPO training. Compliance rate (percentage of prompts directly answered) is the primary metric.

**Why it matters here:** Provides the first multi-category noncompliance benchmark extending beyond safety refusal, with both a training set and a contrastive compliance set to detect over-refusal. Directly measures the behavioral abstention failure modes targeted by Phase 1 training arms.

**Lineage:** Introduced by Brahman et al. (2407.12043) at Allen Institute for AI; built on SituatedQA for underspecified queries and WildChat for safety queries, with remaining categories synthetically generated using GPT-4.
