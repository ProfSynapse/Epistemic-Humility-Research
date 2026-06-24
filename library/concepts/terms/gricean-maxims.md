---
aliases:
- Grice's cooperative principle
- conversational maxims
- maxims of quantity quality relation manner
tags:
- kg/term
- concept
- term
kg:
  id: term:gricean-maxims
  type: term
  status: canonical
area: terms
related:
- '[[2405.21028--lacie-listener-aware-calibration]]'
- '[[overconfidence]]'
- '[[calibration]]'
- '[[rlhf-distorts-all-gricean-maxims]]'
- '[[hallucination]]'
- '[[sycophancy]]'
relationships:
- type: proposed_by
  target: '[[2405.21028--lacie-listener-aware-calibration]]'
  target_id: paper:2405.21028
  confidence: high
- type: related_to
  target: '[[overconfidence]]'
  target_id: term:overconfidence
  confidence: medium
- type: related_to
  target: '[[calibration]]'
  target_id: term:calibration
  confidence: medium
- type: related_to
  target: '[[rlhf-distorts-all-gricean-maxims]]'
  target_id: mechanism:rlhf-distorts-all-gricean-maxims
  confidence: medium
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
  confidence: medium
- type: related_to
  target: '[[sycophancy]]'
  target_id: term:sycophancy
  confidence: medium
---

Four conversational norms proposed by Grice (1975): quantity (say as much as needed, not more), quality (be truthful), relation (be relevant), and manner (be clear and concise). Speakers who violate these norms produce misleading implicatures. In LLM calibration, violating the quality maxim (asserting uncertain claims confidently) is the principal failure mode LACIE targets.

**Why it matters here:** Provides the theoretical grounding for why confidence calibration matters beyond numeric accuracy: a model that sounds confident when wrong violates the quality maxim and misleads listeners pragmatically, a mechanism the graph documents empirically through rlhf-distorts-all-gricean-maxims.

**Lineage:** Introduced by H.P. Grice (1975); applied to LLM evaluation and alignment critique in rlhf-distorts-all-gricean-maxims and used as theoretical motivation in LACIE (2405.21028).
