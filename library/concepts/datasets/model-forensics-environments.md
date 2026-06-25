---
aliases:
- Six agentic forensics environments
- Model forensics environment suite
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:model-forensics-environments
  type: dataset
  status: canonical
area: datasets
related:
- '[[2606.26071--model-forensics-investigating-whether-concerning-behavior-reflects]]'
- '[[tool-calling-agent]]'
- '[[model-forensics-two-step-protocol]]'
relationships:
- type: proposed_by
  target: '[[2606.26071--model-forensics-investigating-whether-concerning-behavior-reflects]]'
  target_id: paper:2606.26071
  confidence: high
- type: related_to
  target: '[[tool-calling-agent]]'
  target_id: term:tool-calling-agent
  confidence: medium
- type: related_to
  target: '[[model-forensics-two-step-protocol]]'
  target_id: method:model-forensics-two-step-protocol
  confidence: high
---

A suite of six agentic environments built to elicit concerning behavior for forensic study: Pre-commit Hook (type-error workaround), Funding Email (whistleblowing), Evaluation Tampering, Secret Number (oracle cheating), Board Games (reward hacking at chess / tic-tac-toe), and Math Sandbagging. Four are novel (Secret Number among them); Board Games extends Bondarenko et al. 2025 and Math Sandbagging adapts Meinke et al. 2024.

**Why it matters here:** it provides controlled settings where a single behavior admits both a misaligned and a benign reading, the precise case the forensic protocol is meant to adjudicate.

**Lineage:** a [[tool-calling-agent]] benchmark; the environments support counterfactual edits (control settings, removed stakes) so behavior can be tied to specific causes.
