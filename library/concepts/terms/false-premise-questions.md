---
aliases:
- false premise
- FalseQA
- presupposition failure
tags:
- kg/term
- concept
- term
kg:
  id: term:false-premise-questions
  type: term
  status: canonical
area: terms
---

False-premise questions are queries predicated on an incorrect or counterfactual
statement, where the correct model behaviour is to detect and reject the embedded
assumption rather than produce a factual-sounding answer. For example, asking
"Who invented the telephone in 1850?" presupposes a false date, and a well-
calibrated model should surface the false premise instead of answering. They
differ from unanswerable questions in that a true answer exists for the corrected
form of the question.

**Why it matters here:** False-premise questions form a distinct abstention
challenge because the model must perform presupposition-failure detection on top
of ordinary knowledge retrieval, making them a useful stress test for whether
abstention training generalises beyond simple "I don't know" cases in the
epistemic-humility study.

**Lineage:** closely related to [[unanswerable-questions]] and [[abstention]];
studied in the context of [[abstentionbench]] (2506.09038).
