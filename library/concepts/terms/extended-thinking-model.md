---
aliases:
- thinking-token model
- open-reasoning model
- Extended-Thinking Model
tags:
- kg/term
- concept
- term
kg:
  id: term:extended-thinking-model
  type: term
  status: canonical
area: verification
related: []
relationships: []
---

An extended-thinking model is a language model that generates an internal chain-of-thought ("thinking tokens") as a separate, inspectable text stream before producing the user-visible answer, as exemplified by DeepSeek-R1, QwQ, and the OLMo-Think family. The thinking stream is typically enclosed in designated tags and may be shown to users or kept private depending on deployment configuration. Because the thinking channel is generated autoregressively before the answer, it creates a two-stage architecture where internal deliberation and output generation are distinct. This separation makes the model tractable to [[thinking-answer-divergence]] analysis: researchers can ask whether the thinking and answer channels carry the same information.

**Why it matters here:** Extended-thinking models create a rare window into implicit model uncertainty; whether the thinking tokens faithfully represent what the model "knows" before committing to an answer is a central question for evaluating epistemic honesty and calibration.

**Lineage:** none.
