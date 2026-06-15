---
aliases:
- Self-Ask
- self-ask classification
- Self-Ask Prompting
tags:
- kg/method
- concept
- method
kg:
  id: method:self-ask-prompting
  type: method
  status: canonical
area: methods
---

Self-Ask Prompting is a prompting strategy in which the model first generates a
candidate answer to a question and then, in a second step, uses that answer to
classify the question as "known" or "unknown." The two-step structure lets the
model leverage its own generated output as evidence before committing to a
confidence label.

**Why it matters here:** In the Cheng et al. framework (Can AI Assistants Know
What They Don't Know?), Self-Ask is evaluated alongside direct and
[[in-context-learning]] prompting as one of three baselines for binary and
multi-class unknown-question classification, and it is the approach most prone
to [[self-ask-induces-overconfidence]] because generating an answer first biases
the model toward claiming knowledge.

**Lineage:** standalone prompting strategy; no formal parent method in the
controlled vocabulary.
