---
aliases:
- Solution Verifier
- trained correctness verifier
- GSM8K verifier
tags:
- kg/method
- concept
- method
kg:
  id: method:solution-verifier
  type: method
  status: canonical
area: methods
related:
- '[[2110.14168--training-verifiers-solve-math-word-problems]]'
- '[[value-function-verifier]]'
- '[[best-of-n-sampling]]'
- '[[generation-discrimination-gap]]'
- '[[confidnet]]'
relationships:
- type: proposed_by
  target: '[[2110.14168--training-verifiers-solve-math-word-problems]]'
  target_id: paper:2110.14168
  confidence: high
- type: related_to
  target: '[[value-function-verifier]]'
  target_id: method:value-function-verifier
  confidence: high
- type: related_to
  target: '[[best-of-n-sampling]]'
  target_id: method:best-of-n-sampling
  confidence: high
- type: related_to
  target: '[[generation-discrimination-gap]]'
  target_id: term:generation-discrimination-gap
  confidence: medium
---

A solution verifier is a separately-trained correctness model — a language model
with a small scalar head (a bias+gain on a reserved special-token logit) — that,
conditioned on a problem and a candidate solution, outputs the probability the
solution is correct. It is trained on generator-sampled solutions auto-labeled by
final-answer match (optionally with a joint LM objective) and used at test time
to rank many sampled completions and return the highest-scored one
(sample-and-rank / verification-over-generation). Generator and verifier are kept
as separate networks to prevent the generator overfitting.

**Why it matters here:** It is the direct ancestor of a trained
confidence/correctness readout used for selection: a learned scalar that scores
solution correctness and drives which answer to trust. It establishes the
"trained correctness readout drives selection" motif central to the
confidence-head line.

**Lineage:** Cobbe et al. 2021 (GSM8K); concurrent with generate-and-rank (Shen
et al. 2021); precursor to outcome and process/step-level reward models and
[[best-of-n-sampling]] verification.
