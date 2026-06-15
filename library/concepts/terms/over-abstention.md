---
aliases:
- over-conservativeness
- false abstention
- ARSP
- exaggerated safety
- Over-abstention
tags:
- kg/term
- concept
- term
kg:
  id: term:over-abstention
  type: term
  status: canonical
area: terms
related:
- '[[abstention]]'
- '[[abstention-rate]]'
- '[[effective-reliability]]'
- '[[over-conservativeness-score]]'
relationships:
- type: related_to
  target: '[[abstention]]'
  target_id: term:abstention
- type: related_to
  target: '[[abstention-rate]]'
  target_id: metric:abstention-rate
- type: related_to
  target: '[[effective-reliability]]'
  target_id: metric:effective-reliability
- type: related_to
  target: '[[over-conservativeness-score]]'
  target_id: metric:over-conservativeness-score
---

Over-abstention is the failure mode where a language model refuses to answer
queries it is capable of answering correctly. It is quantified by ARSP
(N3 / (N1 + N2 + N3)), the share of answerable questions on which the model
still withholds a response. Methods that improve the recall of correct
abstentions, such as instruction tuning on refusal data, tend to worsen
over-abstention because the model generalises the refusal signal too broadly.

**Why it matters here:** The SFT-vs-DPO-vs-KTO abstention study must track
over-abstention alongside abstention recall: a training method that causes the
model to refuse everything would score perfectly on recall but catastrophically
on [[effective-reliability]], so both directions of the tradeoff need to be
measured.

**Lineage:** related to [[abstention]], [[over-conservativeness-score]], and
[[effective-reliability]]; identified as a central tension in
[[2407.18418--know-your-limits-abstention-survey]].
