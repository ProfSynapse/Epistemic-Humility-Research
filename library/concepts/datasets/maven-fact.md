---
aliases:
- MAVEN-FACT corpus
- MAVEN factuality corpus
- MAVEN-FACT
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:maven-fact
  type: dataset
  status: canonical
area: datasets
related:
- '[[2510.15804--emergence-linear-truth-encodings-language-models]]'
- '[[truth-co-occurrence-hypothesis]]'
relationships:
- type: related_to
  target: '[[2510.15804--emergence-linear-truth-encodings-language-models]]'
  target_id: paper:2510.15804
- type: related_to
  target: '[[truth-co-occurrence-hypothesis]]'
  target_id: term:truth-co-occurrence-hypothesis
---

MAVEN-FACT is a factuality-annotated extension of the MAVEN event corpus in which every event mention inside a news article receives a FactBank-style factuality label (certain-true, certain-false, probable, and related categories), enabling document-level analysis of how truth values cluster within real-world reporting. Articles are sourced from Wikipedia and news outlets, providing naturally occurring co-occurrence statistics for factual and counterfactual claims across adjacent sentences in the same document.

**Why it matters here:** The corpus supplies the empirical co-occurrence frequencies used to test the [[truth-co-occurrence-hypothesis]]: if true claims statistically cluster with true claims in natural text, MAVEN-FACT is the primary evidence base for that premise, grounding the mechanistic prediction that language models develop latent truth encoding from pretraining statistics alone rather than from explicit supervision.

**Lineage:** used in [[2510.15804--emergence-linear-truth-encodings-language-models]] to verify the statistical premises of [[truth-co-occurrence-hypothesis]] as a prerequisite for the [[two-phase-memorization-encoding]] account.
