---
title: pretrain-only-base-readout
aliases:
- Amendment Y
- Protocol Amendment Y
- Pretrain-Only Base-Model Readout
- base-readout
- era / origin test
tags:
- kg/experiment
- experiment
- epistemic-humility
kg:
  id: experiment:pretrain-only-base-readout
  type: experiment
  status: canonical
related:
- '[[selfaware]]'
- '[[known-unknown-direction]]'
- '[[answerability-axis-present-without-task-training]]'
- '[[task-training-sharpens-not-creates-hallucination-veto]]'
- '[[internal-paper3--knows-but-doesnt-say]]'
- '[[knowledge-boundary-gate-and-veto-predate-post-training]]'
- '[[post-training-does-not-sharpen-knowledge-boundary-veto]]'
relationships:
- type: evaluates_on
  target: '[[selfaware]]'
  target_id: dataset:selfaware
  confidence: high
  evidence:
  - "AMENDMENT.md sec 3 (H_B1 answerability gate reads AUROC on the SelfAware
    anchor on each Arm A base)"
- type: related_to
  target: '[[known-unknown-direction]]'
  target_id: term:known-unknown-direction
  confidence: high
  evidence:
  - "AMENDMENT.md sec 3, 6 (gate/dial/veto AUROCs exactly as X/Z/SR define
    them, the readout of this direction)"
- type: related_to
  target: '[[answerability-axis-present-without-task-training]]'
  target_id: mechanism:answerability-axis-present-without-task-training
  confidence: medium
  evidence:
  - "AMENDMENT.md sec 1 Rationale (that mechanism shows the axis survives OUR
    downstream task training on top of an already vendor-post-trained
    instruct base; this amendment tests one stage further back, whether the
    axis predates vendor post-training itself - a distinct origin question,
    not a re-measurement of the same claim)"
- type: related_to
  target: '[[task-training-sharpens-not-creates-hallucination-veto]]'
  target_id: mechanism:task-training-sharpens-not-creates-hallucination-veto
  confidence: medium
  evidence:
  - "AMENDMENT.md sec 9 H_B3 (that mechanism finds OUR task training sharpens
    the veto +0.226 AUROC on top of an instruct base; this amendment finds
    vendor post-training itself does not sharpen, and can dull, the veto -
    different training stage, an apparent direction contrast worth noting,
    not a contradiction)"
- type: related_to
  target: '[[internal-paper3--knows-but-doesnt-say]]'
  target_id: paper:internal-paper3
  confidence: high
  evidence:
  - "papers/paper-3-knows-but-doesnt-say/manuscript.md line 1325 provenance
    table (Section 4 pretraining-origin test, four pretrain-only bases at
    0.997+; Section 8 'already paid for by pretraining' downgraded to open
    question at Amendment Y sign-off, answered SUPPORTED 4/4)"
- type: supports
  target: '[[knowledge-boundary-gate-and-veto-predate-post-training]]'
  target_id: mechanism:knowledge-boundary-gate-and-veto-predate-post-training
  confidence: high
  evidence:
  - "AMENDMENT.md sec 9 (H_B1 SUPPORTED 4/4, H_B2 SUPPORTED 4/4)"
- type: supports
  target: '[[post-training-does-not-sharpen-knowledge-boundary-veto]]'
  target_id: mechanism:post-training-does-not-sharpen-knowledge-boundary-veto
  confidence: high
  evidence:
  - "AMENDMENT.md sec 9 (H_B3 NOT SUPPORTED, deltas <= 0 on every pair)"
---

Resolved historical amendment (signed 2026-07-02, fleet complete 2026-07-02).
Tests whether the internal knowledge-boundary signal (answerability gate,
correctness dial, hallucination veto, per the X/Z/SR readout) predates
vendor post-training, i.e. is present on *pretrain-only* base models rather
than only on their vendor-instruct siblings. Every prior "training-free"
result (S/T/U/W/X/Z/SR) was measured on vendor-post-trained instruct
checkpoints, so the pretraining-origin claim in the program papers was
untested in either direction before this amendment.

Design: Arm A pairs four families at the same size and pretraining corpus,
varying only vendor post-training (`Qwen3.5-4B-Base`/`Qwen3.5-4B`,
`gemma-4-E4B` pt/it, `unsloth/Llama-3.2-3B` base/instruct,
`Olmo-3-1025-7B`/`Olmo-3-7B-Instruct`), gated on H_B1/H_B2. Arm B is a
descriptive era ladder of pretrain-only models across generations
(`gpt2-xl` 2019 through the 2026 Arm A bases), report-only, no gate. Base
cells use a backward-compatible base-mode k-shot prompting path (no chat
template); instruct cells keep the chat template (named prompt-surface
confound). All 10 evidence cells cleared the pre-registered adequacy floor
(minimum class count 234 against a floor of 50).

**Result:** H_B1 (pretraining-origin, primary) SUPPORTED 4/4 - every Arm A
base reads the answerability gate at AUROC 0.997+ against a 0.90 bar, and
the falsifier (base < 0.75 while instruct >= 0.95) fires on 0/4 pairs. H_B2
(veto exists pre-post-training) SUPPORTED 4/4 against the 0.65 bar. H_B3
(post-training sharpens the veto, report-only) NOT SUPPORTED: the delta is
<= 0 on every pair (the clean within-run Olmo-3 base->instruct pair moves
veto 0.803 -> 0.731). Arm B stays descriptive per registration: even
GPT-2-XL (2019) clears the 0.65 bar on all three readouts, and the era
signal that does move is the within-SelfAware control (~0.59 pre-2023 era
rising to ~0.71-0.82 from Llama-2 onward), not the gross gate AUROC.

Paper fit (decided at sign-off, pre-result): no standalone paper; folds
into the existing program papers. The regimen/readout papers' "already
paid for by pretraining" strategy reading was downgraded from claim to
open question at registration, with this amendment named as the
instrument that answers it; paper 3 Section 4/8 report the SUPPORTED
result and its scope.

Source of truth: `experiments/pretrain-only-base-readout/AMENDMENT.md`
sections 3, 6, 9.
