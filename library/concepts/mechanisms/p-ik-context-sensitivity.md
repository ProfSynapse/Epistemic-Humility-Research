---
aliases:
- P(IK) responds to in-context evidence
- P(IK) Context Sensitivity
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:p-ik-context-sensitivity
  type: mechanism
  status: canonical
cause: Prepending relevant source material (e.g. a Wikipedia article) or correct step-by-step math hints to a question evaluated by a P(IK) value head trained only on bare questions
effect: P(IK) score increases appropriately; distractors or incorrect hints lower P(IK); effect is larger for shorter, more extractable source documents
polarity: increases
related:
- '[[2207.05221--lms-mostly-know-what-they-know]]'
- '[[p-ik]]'
- '[[triviaqa]]'
- '[[gsm8k]]'
- '[[in-context-learning]]'
relationships:
- type: supported_by
  target: '[[2207.05221--lms-mostly-know-what-they-know]]'
  target_id: paper:2207.05221
  confidence: high
- type: related_to
  target: '[[p-ik]]'
  target_id: method:p-ik
- type: related_to
  target: '[[triviaqa]]'
  target_id: dataset:triviaqa
- type: related_to
  target: '[[gsm8k]]'
  target_id: dataset:gsm8k
- type: related_to
  target: '[[in-context-learning]]'
  target_id: method:in-context-learning
---

A P(IK) classifier trained exclusively on bare TriviaQA questions, with no exposure to
context-augmented inputs during training, nevertheless adjusts its self-knowledge score
appropriately when relevant information is provided in context. An example from the paper
(arXiv:2207.05221, §5.3) shows P(IK) rising from 18% to 78% on an obscure trivia question
when a Wikipedia article about the answer is prepended. For GSM8k math problems (§5.4),
correct chain-of-thought hints raise P(IK) monotonically with the fraction of the hint
revealed, while distractors (hints taken from other questions) lower P(IK) below the
no-hint baseline.

This zero-shot generalization to in-context information suggests the pretrained language
model backbone already encodes a connection between seeing relevant evidence and updating
confidence, and the trained P(IK) head successfully reads that internal signal. The
finding implies that P(IK) is measuring something closer to "can I answer this given what
I know and see" rather than static factual memorization alone.

**Why it matters here:** The locked training-regimen abstention training arms should show, if successful,
that the trained model's uncertainty estimates track context-augmented evidence at least
as well as the pretrained P(IK) baseline does here. A failure to do so would indicate the
training has decoupled the expressed uncertainty signal from underlying evidence integration.
