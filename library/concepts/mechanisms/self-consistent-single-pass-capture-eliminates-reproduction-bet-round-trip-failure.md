---
title: self-consistent-single-pass-capture-eliminates-reproduction-bet-round-trip-failure
aliases:
- Single-pass generation-time capture eliminates the v1/v2 round-trip failure class
- Fresh self-consistent generation removes the reproduction bet
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:self-consistent-single-pass-capture-eliminates-reproduction-bet-round-trip-failure
  type: mechanism
  status: canonical
cause: "Capturing generation-time token IDs, per-token logprobs, and the dial's hidden-state inputs in one self-consistent generation call under a single pinned stack (vLLM 0.27.1), rather than reconstructing a past generation's token identities by re-tokenizing decoded text or by replaying a cached generation on a later, drifted software stack."
effect: "The v1/v2 round-trip failure class (mechanism:reproduction-bet-causes-generation-capture-round-trip-failure) does not occur: capture integrity is perfect, 0 divergences across every row of both arms, against v2's 282/1836 (15.4%) S-arm and 93/1488 (6.3%) T-arm byte-for-byte failure rates on the same underlying comparison. The pre-registered LP3-G0 integrity gate passes cleanly, and the design's second falsifier (the fresh-generation posture failing its own integrity gate) does not fire."
polarity: prevents
related:
- '[[dial-logprob-baseline-v3]]'
- '[[reproduction-bet-causes-generation-capture-round-trip-failure]]'
relationships:
- type: supported_by
  target: '[[dial-logprob-baseline-v3]]'
  target_id: experiment:dial-logprob-baseline-v3
  confidence: high
  evidence:
  - experiments/dial-logprob-baseline-v3/AMENDMENT.md#outcome (S arm; "Capture
    integrity was perfect -- 0 divergences across all rows, against v2's
    282/1836 (15.4%) round-trip failure rate -- so the single-capture posture
    eliminated the failure class that stopped v1/v2, and falsifier (2) did
    not fire.")
- type: related_to
  target: '[[reproduction-bet-causes-generation-capture-round-trip-failure]]'
  target_id: mechanism:reproduction-bet-causes-generation-capture-round-trip-failure
  confidence: high
  evidence:
  - experiments/dial-logprob-baseline-v3/AMENDMENT.md (Why a v3, and what it
    changes)
---

Where [[dial-logprob-baseline]] (v1) and [[dial-logprob-baseline-v2]] (v2)
both halted on a reproduction bet, [[dial-logprob-baseline-v3]] removed the
bet by design: one self-consistent vLLM generation call per row produces the
answer text, the token IDs, the per-token logprobs, and (via the same call or
a same-run teacher-forced fallback, recorded in the run provenance) the
dial's hidden-state inputs together, on one pinned stack, with nothing
regenerated or replayed from an earlier run. On the S arm this produced zero
integrity divergences across every row, a clean pass of the redefined LP3-G0
capture-integrity check that v1 and v2 both failed under their respective
reproduction bets.

**Why it matters here:** this is the instrument-design lesson of the
lineage: the recurring failure across v1 and v2 was never about the
dial-versus-logprob comparison itself, it was about betting on exact
reproduction of a prior generation event. Removing that bet (rather than
widening its tolerance, which v2 tried implicitly by redefining the
round-trip check to compare content rather than count) is what let v3 reach
a clean, gated comparison for the first time in this lineage.

**Lineage:** the direct fix for
[[reproduction-bet-causes-generation-capture-round-trip-failure]], validated
in [[dial-logprob-baseline-v3]] (resolved 2026-08-13).
