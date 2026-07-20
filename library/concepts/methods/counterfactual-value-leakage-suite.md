---
aliases:
- Value Leakage Evaluation Suite
- Donation Bet
- AI Bubble
- AGI Tweet
- Job Offer
- Agentic Grading
- Choosing Activities
tags:
- kg/method
- concept
- method
kg:
  id: method:counterfactual-value-leakage-suite
  type: method
  status: canonical
area: verification
related:
- '[[2607.14345--value-leakage-llm-s-answers-silently-shaped]]'
- '[[covert-value-leakage]]'
- '[[chain-of-thought-faithfulness]]'
- '[[monitorability]]'
relationships:
- type: proposed_by
  target: '[[2607.14345--value-leakage-llm-s-answers-silently-shaped]]'
  target_id: paper:2607.14345
  confidence: high
- type: related_to
  target: '[[covert-value-leakage]]'
  target_id: term:covert-value-leakage
  confidence: high
- type: related_to
  target: '[[chain-of-thought-faithfulness]]'
  target_id: term:chain-of-thought-faithfulness
  confidence: medium
- type: related_to
  target: '[[monitorability]]'
  target_id: metric:monitorability
  confidence: medium
---

A suite of six counterfactual prompt-based and agentic evaluations for
covert value leakage: Donation Bet (Fermi-estimate questions with a
good-cause/bad-cause donation threshold that should not affect the correct
estimate), AI Bubble and AGI Tweet (probability estimates that mention a
specific AI company, testing own-company bias), Job Offer (career-advice
literature summaries conditioned on which company is the current employer
vs. the offering company), Agentic Grading (a coding-agent grading task
where identical answers are shuffled across fictitious model labels), and
Choosing Activities (asking the model to pick "at random" between two
leisure activities it has a stated preference over). Each task pairs a bias
metric (deviation from the unbiased baseline across the counterfactual set)
with an LLM-judge covertness classifier over CoT/response disclosure
categories (Admits to bias / Mentions bias / No mention of bias / Denies
bias), decomposed in the most model-favorable way to yield a lower-bound
covertness estimate.

**Why it matters here:** This is a reusable counterfactual-prompt template
for detecting a bias source (here, model values) from behavioral evidence
alone, independent of the model's own account of its reasoning. The same
disclosure-category decomposition could be repurposed to probe whether
abstention or hedging behavior in our own experiments is faithfully
disclosed versus post-hoc rationalized.

**Lineage:** builds on the counterfactual-prompt methodology of
[[chain-of-thought-faithfulness]] work (contrasted with hint-based setups
such as [[biasing-features-drive-cot-rationalization]]) and reuses the
intervention-style monitorability analysis of [[monitorability]] research
as a robustness check.
