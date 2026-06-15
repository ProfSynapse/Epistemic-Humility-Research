---
aliases:
- AbstainQA
- abstaining in question answering
tags:
- kg/term
- concept
- term
kg:
  id: term:abstain-qa
  type: term
  status: canonical
area: terms
related:
- '[[2402.00367--dont-hallucinate-abstain]]'
relationships:
- type: proposed_by
  target: '[[2402.00367--dont-hallucinate-abstain]]'
  target_id: paper:2402.00367
  confidence: high
---

AbstainQA is a task formulation in which a model is given a question and must
decide whether to provide an answer or to abstain based on whether it has
sufficient internal knowledge to answer correctly. The abstain decision is
evaluated independently from QA accuracy: a model that abstains on a question it
would have answered wrongly is rewarded, whereas a model that abstains on a
question it would have answered correctly is penalised. This separation allows
researchers to measure the quality of the model's self-knowledge apart from its
factual accuracy.

**Why it matters here:** AbstainQA provides the evaluation framework and the
[[multi-llm-cooperate]] and [[multi-llm-compete]] abstention methods studied in
2402.00367, offering a direct precedent for how the SFT-vs-DPO-vs-KTO experiment
should operationalise abstention decisions as model-level judgements rather than
dataset-level coverage metrics.

**Lineage:** formalises the [[abstention]] decision in open-domain QA; studied
alongside [[known-unknown-questions]] and [[self-knowledge]].
