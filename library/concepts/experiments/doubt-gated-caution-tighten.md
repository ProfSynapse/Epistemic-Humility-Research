---
title: doubt-gated-caution-tighten
aliases:
- Doubt-gated caution snap (resolved headline, 2026-07-07)
- gated confab clean_tighten 73.5% / known-correct false-refusal 3.1%
tags:
- kg/experiment
- experiment
- doubt-snap
kg:
  id: experiment:doubt-gated-caution-tighten
  type: experiment
  status: canonical
related:
- '[[activation-steering]]'
- '[[abstention]]'
- '[[snap-seed-sampled-decode-replication]]'
- '[[ungated-vs-gated-dose-matched]]'
- '[[rr-cross-family-raw-refusal]]'
- '[[doubt-snap-cross-family-confirmatory]]'
relationships:
- type: related_to
  target: '[[activation-steering]]'
  target_id: method:activation-steering
  confidence: high
- type: related_to
  target: '[[abstention]]'
  target_id: term:abstention
  confidence: medium
- type: related_to
  target: '[[snap-seed-sampled-decode-replication]]'
  target_id: experiment:snap-seed-sampled-decode-replication
  confidence: high
  evidence:
  - experiments/snap-seed-sampled-decode-replication/AMENDMENT.md (Motivation and posture)
- type: related_to
  target: '[[ungated-vs-gated-dose-matched]]'
  target_id: experiment:ungated-vs-gated-dose-matched
  confidence: high
  evidence:
  - experiments/ungated-vs-gated-dose-matched/AMENDMENT.md
- type: related_to
  target: '[[rr-cross-family-raw-refusal]]'
  target_id: experiment:rr-cross-family-raw-refusal
  confidence: medium
  evidence:
  - experiments/rr-cross-family-raw-refusal/AMENDMENT.md (Motivation and posture)
- type: related_to
  target: '[[doubt-snap-cross-family-confirmatory]]'
  target_id: experiment:doubt-snap-cross-family-confirmatory
  confidence: high
---

Training-free, exploratory doubt-gated caution snap on raw-base bf16
Qwen3-4B: a doubt-threshold gate fires an erase-and-write intervention along
a caution direction `c_hat`, scope `anchor_onward`, only on rows whose doubt
readout clears a Youden-J-fit threshold.

Resolved 2026-07-07 as an exploratory pass, reported separately from the
locked headline matrix. G0 (instrument validity) passed: held-out
known-correct n=258, FIT AUC 0.9955, direction refit byte-identical, smoke
write read-back mean 200.11, 0% collapse, undosed baseline well-formed rate
1.0. G1 passed: gated confab clean_tighten 136/185 = 73.5% (Wilson 95% CI
[66.7%, 79.3%]). G2 passed: gated known-correct false-refusal cost
8/258 = 3.1% (Wilson 95% CI [1.6%, 6.0%]). G3 passed after a red-team-requested
no-op baseline: the random-direction placebo did not reproduce the gated
effect (confab clean_tighten 13/185 = 7.0% vs no-op 21/185 = 11.4%;
known-correct cost 6/258 = 2.3% vs no-op 5/258 = 1.9%, within the +2pt no-op
tolerance), and the permuted-gate placebo was strictly worse on selectivity
(known-correct cost 59/258 = 22.9% vs the real gate's 3.1%).

Verdict: the instrument passed as a training-free, selective tighten on this
substrate. This 73.5%/3.1% headline is the frozen instrument later
replicated under fresh seeds and sampled decode
([[snap-seed-sampled-decode-replication]]), tested for write-side
selectivity by dosing every row unconditionally
([[ungated-vs-gated-dose-matched]]), and ported (at a different site
per family) to non-Qwen substrates ([[rr-cross-family-raw-refusal]]).
Source of truth: `experiments/doubt-gated-caution-tighten/AMENDMENT.md`.
