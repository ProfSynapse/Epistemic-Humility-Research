---
title: dial-logprob-baseline-v3
aliases:
- 'Dial token-logprob baseline v3: fresh self-consistent generation, no reproduction
  bet'
- v3 dial-vs-sequence-probability baseline, first gated comparison
tags:
- kg/experiment
- experiment
- correctness-dial
kg:
  id: experiment:dial-logprob-baseline-v3
  type: experiment
  status: canonical
related:
- '[[dial-logprob-baseline]]'
- '[[dial-logprob-baseline-v2]]'
- '[[per-answer-correctness-linearly-readable-post-generation]]'
- '[[sequence-probability]]'
- '[[self-consistent-single-pass-capture-eliminates-reproduction-bet-round-trip-failure]]'
- '[[qwen3-4b-dial-margin-over-logprob-remains-ambiguous-on-fresh-generation]]'
relationships:
- type: builds_on
  target: '[[dial-logprob-baseline]]'
  target_id: experiment:dial-logprob-baseline
  confidence: high
  evidence:
  - experiments/dial-logprob-baseline-v3/AMENDMENT.md (Why a v3, and what it
    changes; "v1 ... re-tokenized decoded text (30/3324 rows off by one
    token at BPE span boundaries)"; question, LP3-G1 threshold/direction/CI
    rule, ambiguous band, and logprob variant definitions carried verbatim
    from v1)
- type: builds_on
  target: '[[dial-logprob-baseline-v2]]'
  target_id: experiment:dial-logprob-baseline-v2
  confidence: high
  evidence:
  - experiments/dial-logprob-baseline-v3/AMENDMENT.md (Why a v3, and what it
    changes; "v2 regenerated months-old cached rows byte-for-byte ... missed
    on 282/1836 (S) and 93/1488 (T) rows"); experiment.yaml inputs list
    experiments/dial-logprob-baseline-v2/AMENDMENT.md and cell.yaml as
    frozen inputs
- type: related_to
  target: '[[per-answer-correctness-linearly-readable-post-generation]]'
  target_id: mechanism:per-answer-correctness-linearly-readable-post-generation
  confidence: high
  evidence:
  - experiments/dial-logprob-baseline-v3/AMENDMENT.md (Design; dial is an
    out-of-fold refit at the source cells' own signed layers, S L20 / T L22)
- type: related_to
  target: '[[sequence-probability]]'
  target_id: term:sequence-probability
  confidence: high
  evidence:
  - experiments/dial-logprob-baseline-v3/AMENDMENT.md (Design; comparison is
    dial OOF AUROC vs primary length-normalized mean answer-span logprob
    AUROC)
- type: supports
  target: '[[self-consistent-single-pass-capture-eliminates-reproduction-bet-round-trip-failure]]'
  target_id: mechanism:self-consistent-single-pass-capture-eliminates-reproduction-bet-round-trip-failure
  confidence: high
  evidence:
  - experiments/dial-logprob-baseline-v3/AMENDMENT.md#outcome (S arm; "Capture
    integrity was perfect -- 0 divergences across all rows, against v2's
    282/1836 (15.4%) round-trip failure rate")
- type: supports
  target: '[[qwen3-4b-dial-margin-over-logprob-remains-ambiguous-on-fresh-generation]]'
  target_id: mechanism:qwen3-4b-dial-margin-over-logprob-remains-ambiguous-on-fresh-generation
  confidence: high
  evidence:
  - experiments/dial-logprob-baseline-v3/AMENDMENT.md#outcome (S arm; "dial
    AUROC minus primary-logprob AUROC = +0.0118, paired 95% CI [-0.0122,
    +0.0359]"; ambiguous-band disposition applies, gate not passed, neither
    falsifier fired)
---

Third cell of the dial-token-logprob-baseline lineage. v1 and v2 both
halted at a pre-outcome integrity gate without ever computing a gated
dial-vs-logprob comparison, and both failed the same way: each bet on
exactly reproducing a past generation event (re-tokenized text in v1,
byte-for-byte cache replay under a drifted stack in v2). v3 removes the bet
by design: one self-consistent generation run (pinned vLLM 0.27.1) per arm
captures fresh answers, generation-time token IDs, per-token logprobs, and
the dial's hidden-state inputs from the same generation event on one
pinned stack, so there is no external artifact left to round-trip against.
The question, the primary gate LP3-G1 (threshold, direction, CI rule), the
ambiguous band, the logprob variant definitions, and the paired-bootstrap
statistic all carry over verbatim from v1/v2; only the capture posture
changes.

Resolved 2026-08-13 (local RTX 3090, single launch sequence, one aborted
engine-init attempt repaired at the host-env level before any evidence
row).

**S arm (primary): first gated result in the lineage.** LP3-G0 integrity
passed with zero divergences across all rows (against v2's 282/1836, 15.4%,
failure rate), eliminating the v1/v2 failure class; see
[[self-consistent-single-pass-capture-eliminates-reproduction-bet-round-trip-failure]].
Coverage complete, 1820 answered rows (>= the 1000-row power floor); fresh
dial OOF AUROC 0.8301 (>= the 0.75 sanity bound; June-signed value 0.834,
descriptive comparison only). The primary quantity, dial AUROC minus
primary-logprob AUROC, is **+0.0118, paired 95% CI [-0.0122, +0.0359]**
(n_boot 2000, seed 20260813): positive but under the +0.05 LP3-G1 floor
with a CI straddling zero, so the registered ambiguous-band disposition
applies -- gate not passed, dial-novelty falsifier not fired either; see
[[qwen3-4b-dial-margin-over-logprob-remains-ambiguous-on-fresh-generation]].
The registered prediction for S (ambiguous band near +0.02) landed as
stated.

**T arm (descriptive-only): registered data-stage stop at the power
floor.** Integrity (0 failures) and coverage passed, but only 710 answered
rows emerged from the pinned 4000-attempt inventory against the 1000-row
floor (June source: 1488). Per gates.yaml the arm's descriptive statistics
are not reported and the registered T-side prediction (+0.15) is untested.
The hypothesis that the deployed abstention-trained checkpoint abstains
more under fresh greedy vLLM generation than in the June cache is recorded
explicitly as a hypothesis only, not a finding, and is not carried into any
typed claim here.

**One-sentence verdict (verbatim from `experiment.yaml`):** on fresh, fully
self-consistent data the dial's advantage over the raw answer-logprob
baseline on the base model is small and statistically uncertain (+0.012,
CI straddling 0) rather than the >= +0.05 novelty margin; the
fresh-generation instrument itself is sound (integrity clean, dial reads
at 0.830); the deployed-arm comparison remains unmeasured for want of
answered rows.

**Lineage:** builds on [[dial-logprob-baseline]] (v1) and
[[dial-logprob-baseline-v2]] (v2), closing the reproduction-bet failure
class both shared. Source of truth:
`experiments/dial-logprob-baseline-v3/AMENDMENT.md`, Outcome section,
resolved 2026-08-13.
