---
title: knowledge-boundary-gate-and-veto-predate-post-training
aliases:
- The knowledge-boundary readout predates vendor post-training
- Amendment Y H_B1/H_B2 SUPPORTED
- pretraining-origin claim supported on four families
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:knowledge-boundary-gate-and-veto-predate-post-training
  type: mechanism
  status: canonical
cause: "Running the identical answerability-gate and hallucination-veto readout (gate/dial/veto AUROCs exactly as Amendments X/Z/SR define them) on four pretrain-only base models (Qwen3.5-4B-Base, gemma-4-E4B pt, unsloth/Llama-3.2-3B base, Olmo-3-1025-7B), each paired against its vendor-instruct sibling, using a backward-compatible base-mode k-shot prompting path (no chat template, no vendor post-training, no task training of any kind)."
effect: "Every Arm A base reads the answerability gate at AUROC 0.997+ against the pre-registered 0.90 bar (H_B1 SUPPORTED 4/4), and the falsifier (base gate < 0.75 while instruct sibling >= 0.95) fires on 0/4 pairs. The hallucination veto clears AUROC >= 0.65 on every base against the pre-registered bar (H_B2 SUPPORTED 4/4: 0.6657 Qwen3.5 marginal, 0.8743 Gemma, 0.8354 Llama-3.2, 0.8029 Olmo-3). Both readouts of the internal knowledge-boundary signal are present before any vendor post-training, across four independent model families."
polarity: enables
related:
- '[[pretrain-only-base-readout]]'
- '[[answerability-axis-present-without-task-training]]'
- '[[known-unknown-direction]]'
- '[[selfaware]]'
- '[[internal-paper3--knows-but-doesnt-say]]'
relationships:
- type: supported_by
  target: '[[pretrain-only-base-readout]]'
  target_id: experiment:pretrain-only-base-readout
  confidence: high
  evidence:
  - "AMENDMENT.md sec 9 Result table and H_B1/H_B2 adjudication"
- type: related_to
  target: '[[answerability-axis-present-without-task-training]]'
  target_id: mechanism:answerability-axis-present-without-task-training
  confidence: medium
  evidence:
  - "AMENDMENT.md sec 1 Rationale (that mechanism established the axis survives
    OUR downstream task training on top of an ALREADY vendor-post-trained
    instruct base; this mechanism pushes the origin claim one stage earlier,
    to before vendor post-training itself)"
- type: related_to
  target: '[[known-unknown-direction]]'
  target_id: term:known-unknown-direction
  confidence: high
  evidence:
  - "AMENDMENT.md sec 6 (gate/dial/veto AUROCs exactly as X/Z/SR define this
    direction)"
- type: related_to
  target: '[[selfaware]]'
  target_id: dataset:selfaware
  confidence: high
  evidence:
  - "AMENDMENT.md sec 3 (H_B1 gate reads AUROC on the SelfAware anchor)"
- type: related_to
  target: '[[internal-paper3--knows-but-doesnt-say]]'
  target_id: paper:internal-paper3
  confidence: high
  evidence:
  - "papers/paper-3-knows-but-doesnt-say/manuscript.md line 1325 provenance
    table (Section 4 pretraining-origin test) and Section 8 (origin claim
    downgraded to open question at registration, answered here)"
---

Amendment Y's primary result. Every prior "training-free" reading in the
program (Amendments S/T/U/W/X/Z/SR) was measured on vendor-post-trained
instruct checkpoints, so "training-free" meant free of *our* adapters, not
free of vendor post-training. Pairing four families at fixed size and
pretraining corpus and varying only vendor post-training isolates the
question directly: both the answerability gate (H_B1) and the hallucination
veto (H_B2) read at or above their pre-registered bars on every pretrain-only
base, and the falsifier fires on none of the four pairs.

**Why it matters here:** this is the strongest available evidence for the
program's "already paid for by pretraining" framing (regimen/readout papers
§8), which the papers had asserted without ever measuring a pretrain-only
checkpoint. It licenses the pretraining-origin claim on the answerability
gate and hallucination veto, though a companion cell
([[post-training-does-not-sharpen-knowledge-boundary-veto]]) shows the
picture is not simply "training does nothing": post-training does not
sharpen the veto either, and can dull it.

**Lineage:** distinct from, and one training-stage earlier than,
[[answerability-axis-present-without-task-training]] (Amendment W), which
showed the axis survives our task training on top of an *already*
instruct-tuned base. Known confound (stated up front in the amendment):
base-vs-instruct pairs differ in more than post-training (annealing data,
long-context stages, and the base cells' k-shot render vs the instruct
cells' chat template) - the cleanest available contrast, not a perfect
ablation. Source of truth: `experiments/pretrain-only-base-readout/AMENDMENT.md`
sec 3, 6, 9.
