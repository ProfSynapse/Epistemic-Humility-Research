---
title: qwen-midband-verbalized-confidence-anti-tracks-answerability
aliases:
- verbalized confidence anti-tracks answerability on confab-prone rows (qwen mid-band)
- the model verbalizes higher confidence on rows it confabulates
- SC2-void descriptive finding, susceptibility-as-probe (M2)
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:qwen-midband-verbalized-confidence-anti-tracks-answerability
  type: mechanism
  status: canonical
cause: "In the susceptibility-as-probe experiment (M2), one greedy verbalized-confidence elicitation (a frozen template asking for a 0-100 self-rated confidence integer before any answer text) was collected per row for the same 760-row qwen35_4b population as the internal readout and susceptibility channels: 400 confab rows (unanswerable source, answered anyway at baseline) and 360 known_correct_answered rows (answerable source, answered correctly at baseline). 584 of 760 rows parsed (parse rate 0.7684), below the registered SC2 floor of 0.95, voiding the channel as a scored predictor for every registered criterion."
effect: "On the 584 parseable rows, verbalized confidence discriminates confab from known_correct_answered at AUROC 0.1479 [0.1214, 0.1754], far below chance and in the opposite direction from both internal channels on the same rows (readout 0.9821, susceptibility 0.8504). The model reports HIGHER self-rated confidence on rows it confabulates than on rows it answers correctly, the reverse of what a self-report-tracks-answerability story predicts. Because the elicitation channel is void by the SC2 parse-rate gate, this number evaluates no registered framework claim and is not a scored criterion; it is recorded as a registered descriptive-only finding (Outcome, Descriptives), retained for the paper's self-report discussion rather than for any pass/fail adjudication."
polarity: complicates
related:
- '[[susceptibility-as-probe]]'
- '[[margin-theory-of-epistemic-state]]'
- '[[known-unknown-direction]]'
- '[[verbalized-confidence]]'
- '[[qwen-midband-readout-and-susceptibility-channels-are-redundant]]'
relationships:
- type: supported_by
  target: '[[susceptibility-as-probe]]'
  target_id: experiment:susceptibility-as-probe
  confidence: medium
  evidence:
  - experiments/susceptibility-as-probe/AMENDMENT.md#outcome (Outcome,
    Descriptives; SC2 void, parse rate 0.7684 vs floor 0.95, registered
    descriptive finding only)
- type: related_to
  target: '[[margin-theory-of-epistemic-state]]'
  target_id: term:margin-theory-of-epistemic-state
  confidence: medium
  evidence:
  - docs/research/margin-theory-framework.md (section 2, Claim 3; verbalized
    confidence is the program's deployment-baseline self-report comparator
    for the readout and susceptibility channels)
- type: related_to
  target: '[[known-unknown-direction]]'
  target_id: term:known-unknown-direction
  confidence: low
  evidence:
  - experiments/susceptibility-as-probe/AMENDMENT.md (Design, Three per-row
    scores; verbalized confidence is elicited on the same rows and
    population split as the internal known-unknown-direction readout, with
    no shared computation)
- type: related_to
  target: '[[verbalized-confidence]]'
  target_id: method:verbalized-confidence
  confidence: high
  evidence:
  - experiments/susceptibility-as-probe/AMENDMENT.md (Design, Three per-row
    scores; the elicitation is a direct-confidence-elicitation instance of
    this method)
- type: related_to
  target: '[[qwen-midband-readout-and-susceptibility-channels-are-redundant]]'
  target_id: mechanism:qwen-midband-readout-and-susceptibility-channels-are-redundant
  confidence: medium
  evidence:
  - experiments/susceptibility-as-probe/AMENDMENT.md#outcome (Outcome; both
    findings come from the same M2 scoreboard on the same 760 rows)
---

A registered but unscored finding from the susceptibility-as-probe
experiment: verbalized confidence does not merely fail to track
answerability at the qwen mid-band operating point, it anti-tracks it. On
the 584 rows where the elicitation parsed, the model's self-rated
confidence discriminates confab from known_correct_answered at AUROC
0.1479, meaning it is a strong signal in the wrong direction, not a weak
signal in the right one. The internal readout and susceptibility channels
on the identical rows sit at 0.9821 and 0.8504 respectively, so this is not
a population artifact: the model's own hidden states carry the
answerability information cleanly while its verbalized self-report carries
the opposite of it.

**Why it matters here:** the elicitation channel is void by the SC2
parse-rate gate (0.7684 against a 0.95 floor registered before any AUROC
was computed), so this finding evaluates no framework claim and carries no
pass/fail weight in the M2 scoreboard; it is recorded descriptively only,
per the amendment's own framing. Its value is for the paper's discussion of
self-report as an epistemic-state instrument: a channel this anti-predictive
would be actively misleading if used as a deployed confidence signal on
this population, independent of whatever caused the low parse rate. Whether
the anti-tracking survives a template or parse-rate fix, or is itself an
artifact of confab-prone rows eliciting more verbose, hedge-laden output
that this parse rule under-captures, is open and not addressed by this
experiment.

**Lineage:** descriptive byproduct of
[[susceptibility-as-probe]] (M2), the first empirical test of Claim 3 in
[[margin-theory-of-epistemic-state]]. Elicited via the
[[verbalized-confidence]] method (direct confidence elicitation) on the
same 760-row qwen35_4b population as
[[qwen-midband-readout-and-susceptibility-channels-are-redundant]]. Source
of truth: `experiments/susceptibility-as-probe/AMENDMENT.md`, Outcome
section, resolved 2026-07-17.
