---
aliases:
- LIMA
- Less Is More for Alignment
- LIMA dataset
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:lima
  type: dataset
  status: canonical
area: datasets
related:
- '[[2305.11206--lima-less-more-alignment]]'
- '[[superficial-alignment-hypothesis]]'
- '[[supervised-finetuning]]'
relationships:
- type: proposed_by
  target: '[[2305.11206--lima-less-more-alignment]]'
  target_id: paper:2305.11206
  confidence: high
- type: related_to
  target: '[[superficial-alignment-hypothesis]]'
  target_id: term:superficial-alignment-hypothesis
  confidence: high
- type: related_to
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
  confidence: high
---

A curated set of 1,000 (prompt, response) pairs used to fine-tune a pretrained LLM (65B LLaMA in the original paper) with standard supervised loss and no reinforcement learning or additional human-feedback stage, plus a 300-prompt test set and 50-prompt dev set. Sources: 750 curated Stack Exchange/wikiHow/Reddit/Natural-Instructions examples plus 250 examples manually written by the paper's authors in a consistent "helpful AI assistant" voice. "LIMA" is also used as shorthand for the minimal-curated-SFT alignment approach the dataset was built to test, not just the data itself.

**Why it matters here:** LIMA is the reference point for how little labeled SFT signal is needed to induce broadly aligned, instruction-following surface behavior, which frames how much of trained abstention behavior could in principle be reachable via a comparably small budget rather than large-scale RLHF/RLVR. It is also reused directly as a fine-tuning dataset by unrelated later work (e.g. response-tuning ablations, and normalization-architecture studies) as a standard small, high-quality SFT set.

**Lineage:** operationalizes the [[superficial-alignment-hypothesis]]; contrast with prompting-only approaches such as URIAL (arXiv:2312.01552), which claims to reach similar quality with zero gradient updates via in-context demonstrations alone.
