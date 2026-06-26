---
aliases:
- probability-based self-improvement
- recursive self-improvement without verifier
- verifier-free recursive self-improvement
- Verifier-Free Self-Improvement
tags:
- kg/method
- concept
- method
kg:
  id: method:verifier-free-self-improvement
  type: method
  status: canonical
area: verification
related: []
relationships: []
---

A class of inference-time methods where a model uses its own sequence probabilities to select, weight, or iteratively refine outputs without an external reward model or verifier. The core idea is that higher-probability responses serve as implicit quality signals, enabling recursive loops that condition on or reinforce those responses. Instances include probability-weighted aggregation over candidate outputs and iterative decoding loops that use prior high-probability completions as context for subsequent passes.

**Why it matters here:** Whether internal sequence probability can substitute for external verification is a central open question in epistemic humility research: if that signal is unreliable under certain conditions, verifier-free self-improvement may systematically reinforce incorrect high-confidence outputs rather than correcting them.

**Lineage:** no direct predecessors encoded in this graph.
