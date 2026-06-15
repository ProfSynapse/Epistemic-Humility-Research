---
aliases:
- model self-knowledge
- knowing what you know
- metacognition in LLMs
- Self-Knowledge
- knowing what you don't know
- LLM self-knowledge
- metacognitive ability
- metacognition
tags:
- kg/term
- concept
- term
kg:
  id: term:self-knowledge
  type: term
  status: canonical
area: terms
related:
- '[[knowledge-boundary]]'
relationships:
- type: related_to
  target: '[[knowledge-boundary]]'
  target_id: term:knowledge-boundary
---

Self-knowledge is the capacity of a language model to accurately assess what it does and does not know. In practice it is operationalised either through prompt-based self-evaluation (see [[p-true]]) or through a finetuned introspective head (see [[p-ik]]). Self-knowledge is distinct from raw accuracy: a model can produce correct answers while being poorly calibrated about which answers are correct, or it can have strong discriminative self-assessment while still producing errors.

**Why it matters here:** The SFT-vs-DPO-vs-KTO abstention study treats self-knowledge as the core capability being trained. Each training arm (SFT via [[idk-sft]], DPO, KTO) attempts to improve the model's ability to say "I don't know" precisely when it crosses its [[knowledge-boundary]], without over-hedging on questions it can answer correctly.

**Lineage:** related to [[knowledge-boundary]]; measured via [[self-knowledge-f1]], [[p-true]], [[p-ik]], and [[expected-calibration-error]]; assessed at dataset level by [[selfaware]] and [[known-unknown-questions]].
