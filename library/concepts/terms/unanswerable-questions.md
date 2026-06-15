---
aliases:
- answer unknown
- unanswerable
- known unknowns
tags:
- kg/term
- concept
- term
kg:
  id: term:unanswerable-questions
  type: term
  status: canonical
area: terms
---

Unanswerable questions are questions for which no commonly agreed-upon,
documented correct answer exists regardless of the context provided, requiring a
model to abstain rather than guess. The category includes questions about future
events, deeply contested empirical matters, and queries that fall outside any
recorded knowledge. They differ from false-premise questions in that the question
form itself is not defective; the limitation is epistemic, residing in the
world's or the model's knowledge state.

**Why it matters here:** Unanswerable questions are a core evaluation slice in
abstention benchmarks including [[abstentionbench]] (2506.09038), and teaching
models to recognise them without over-refusing answerable questions is the central
trade-off the SFT-vs-DPO-vs-KTO study is designed to quantify.

**Lineage:** closely related to [[false-premise-questions]] and
[[known-unknown-questions]]; triggers the [[abstention]] decision.
