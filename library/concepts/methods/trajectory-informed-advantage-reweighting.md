---
aliases:
- TIAR
- Trajectory-Informed Advantage Reweighting
tags:
- kg/method
- concept
- method
kg:
  id: method:trajectory-informed-advantage-reweighting
  type: method
  status: canonical
area: methods
related:
- '[[2605.25850--tiar-trajectory-informed-advantage-reweighting-llm-abstention]]'
- '[[group-relative-policy-optimization]]'
- '[[ternary-reward-design]]'
- '[[truthrl]]'
relationships:
- type: proposed_by
  target: '[[2605.25850--tiar-trajectory-informed-advantage-reweighting-llm-abstention]]'
  target_id: paper:2605.25850
  confidence: high
- type: related_to
  target: '[[group-relative-policy-optimization]]'
  target_id: method:group-relative-policy-optimization
  confidence: high
- type: related_to
  target: '[[ternary-reward-design]]'
  target_id: method:ternary-reward-design
  confidence: high
- type: related_to
  target: '[[truthrl]]'
  target_id: method:truthrl
  confidence: high
---

Pan et al. (2026) extend the static ternary-reward GRPO abstention setup (correct +1, incorrect -1, abstain 0, as in [[truthrl]]) with Trajectory-Informed Advantage Reweighting: GRPO's multiple sampled trajectories per query are treated as a natural confidence signal (how consistently the policy answers the same query), and this trajectory-level consistency dynamically reweights the abstention advantage during training via a scaling factor lambda, rather than using a fixed reward for abstention regardless of query difficulty. Setting lambda=0 reduces exactly to the static ternary-reward baseline (TruthRL); lambda=1.0 (full inversion) is the paper's recommended default.

**Why it matters here:** TIAR is a pure training-side (GRPO/RL) refinement of abstention reward shaping; the paper evaluates only training-based baselines (R-Tuning SFT, Rejection Fine-Tuning, DPO, TruthRL GRPO) against TIAR, all applied to the same Llama-3.1-8B-Instruct or Qwen3-8B checkpoint, with no prompted-only or instruction-removed evaluation arm (verified against the paper: see [[trajectory-informed-reweighting-improves-abstention-f1]] and the paper note's Relevance section). It is therefore useful as a comparison point for what training-only abstention improvement looks like, but does not itself speak to the prompt-vs-training question.
