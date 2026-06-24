---
aliases:
- AH
- associated hallucinations
- knowledge-associated hallucination
tags:
- kg/term
- concept
- term
kg:
  id: term:associated-hallucination
  type: term
  status: canonical
area: terms
related:
- '[[2510.09033--probes-read-recall-not-truth]]'
- '[[unassociated-hallucination]]'
- '[[hallucination]]'
- '[[ah-uh-hallucination-taxonomy]]'
- '[[probe-reads-recall-not-truth]]'
- '[[knowledge-boundary]]'
- '[[spurious-dishonesty]]'
relationships:
- type: proposed_by
  target: '[[2510.09033--probes-read-recall-not-truth]]'
  target_id: paper:2510.09033
  confidence: high
- type: related_to
  target: '[[unassociated-hallucination]]'
  target_id: term:unassociated-hallucination
  confidence: medium
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
  confidence: medium
- type: related_to
  target: '[[ah-uh-hallucination-taxonomy]]'
  target_id: term:ah-uh-hallucination-taxonomy
  confidence: medium
- type: related_to
  target: '[[probe-reads-recall-not-truth]]'
  target_id: mechanism:probe-reads-recall-not-truth
  confidence: medium
- type: related_to
  target: '[[knowledge-boundary]]'
  target_id: term:knowledge-boundary
  confidence: medium
- type: related_to
  target: '[[spurious-dishonesty]]'
  target_id: term:spurious-dishonesty
  confidence: medium
---

A factual error produced when an LLM relies on spurious parametric associations triggered by the input subject. The model draws on encoded subject representations and propagates subject information to the output token through the standard knowledge-recall pathway, so the error shares the internal computational signature of a factually correct answer.

**Why it matters here:** AHs are the hard case for hallucination detection: because the model's information flow looks identical to a correct recall, internal probes and black-box confidence signals achieve only near-chance AUROC (0.46-0.69 depending on method and model). Refusal tuning trained on UH samples also fails to generalize to AHs. AHs are more common on popular subjects, making their undetected errors disproportionately consequential for user trust.

**Lineage:** Introduced and operationalized in Cheang et al. (2510.09033) as part of a three-way taxonomy contrasting FAs, AHs, and UHs; draws on earlier work on knowledge shortcuts and co-occurrence bias (Kang and Choi 2023).
