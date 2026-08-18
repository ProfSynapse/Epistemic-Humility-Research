---
title: prompt-vs-training-panel
aliases:
- 'Prompt-vs-training disentanglement panel: base counterfactuals and instruction-free abstention'
- prompt-vs-training panel
- 11-arm prompt x checkpoint crossing
tags:
- kg/experiment
- experiment
- abstention
kg:
  id: experiment:prompt-vs-training-panel
  type: experiment
  status: canonical
related:
- '[[rc-prompt-elicits-near-ceiling-abstention-from-untrained-base]]'
- '[[only-sft-installs-abstention-in-weights]]'
- '[[grpo-cold-start-induction]]'
- '[[pstruct-internalization-seed-robustness]]'
- '[[context-invariance]]'
- '[[prompt-cannot-override-rlvr-abstention-deficit]]'
- '[[prompt-crossing-heldout-confirmatory]]'
- '[[base-refusal-direction-under-contract]]'
relationships:
- type: builds_on
  target: '[[grpo-cold-start-induction]]'
  target_id: experiment:grpo-cold-start-induction
  confidence: high
  evidence:
  - experiments/prompt-vs-training-panel/AMENDMENT.md (Motivation and posture;
    the panel is scaffolded directly from the cold-GRPO red-team audit's three
    findings about the missing base counterfactual)
- type: supports
  target: '[[rc-prompt-elicits-near-ceiling-abstention-from-untrained-base]]'
  target_id: mechanism:rc-prompt-elicits-near-ceiling-abstention-from-untrained-base
  confidence: high
  evidence:
  - experiments/prompt-vs-training-panel/AMENDMENT.md#outcome (per-arm table,
    raw base row; R1 did not fire, R2 fired)
- type: supports
  target: '[[only-sft-installs-abstention-in-weights]]'
  target_id: mechanism:only-sft-installs-abstention-in-weights
  confidence: high
  evidence:
  - experiments/prompt-vs-training-panel/AMENDMENT.md#outcome (Bands; R3 FIRED,
    cold SFT seed 1 69.57 >= 30 with base 0.00 < 10; cold DPO/KTO seed 1 track
    the base at every prompt)
- type: related_to
  target: '[[context-invariance]]'
  target_id: term:context-invariance
  confidence: medium
  evidence:
  - experiments/prompt-vs-training-panel/AMENDMENT.md#outcome (one-sentence
    verdict; abstention claims are meaningful only relative to the prompt
    condition unless training has internalized the behavior)
- type: related_to
  target: '[[prompt-crossing-heldout-confirmatory]]'
  target_id: experiment:prompt-crossing-heldout-confirmatory
  confidence: high
  evidence:
  - "experiments/prompt-crossing-heldout-confirmatory/experiment.yaml (verdict:
    confirmatory promotion route for this panel's C1/C2 findings on held-out
    AmbigQA, base P-rc minus P-plain gap 70.26pp, cold SFT seeds
    56.39/63.47/61.58, both bands cleared)"
- type: related_to
  target: '[[prompt-cannot-override-rlvr-abstention-deficit]]'
  target_id: mechanism:prompt-cannot-override-rlvr-abstention-deficit
  confidence: medium
  evidence:
  - experiments/prompt-vs-training-panel/AMENDMENT.md#outcome (mirror polarity;
    that mechanism is prompts failing to override a trained always-answer prior,
    this panel is an untrained base's abstention being entirely prompt-carried)
- type: related_to
  target: '[[base-refusal-direction-under-contract]]'
  target_id: experiment:base-refusal-direction-under-contract
  confidence: high
  evidence:
  - "experiments/base-refusal-direction-under-contract/experiment.yaml inputs
    (Stage 1 known-refused vs known-answered labels join from this panel's
    governed retained scored_rows, base P-rc arm, SelfAware n=3369; no fresh
    generation in the downstream cell)"
---

Exploratory (tier-2) measurement cell that crosses three prompt levels
(response-confidence P-rc, plain-answer P-plain, structure-only P-struct)
with checkpoints spanning the raw untrained Qwen3-4B base and cold/warmed
SFT, DPO, KTO, and GRPO arms, 11 arms total. Registered as measurement, not
hypothesis test: it carries an integrity gate (PV-G0) and four pre-stated
interpretation bands (R1-R4) fixed at signing so the prose response to any
outcome was committed in advance. Scaffolded directly from the cold-GRPO
red-team audit, which found no raw-base SelfAware eval existed anywhere in
the program under any prompt contract.

Resolved 2026-08-14. PV-G0 passed on all 11 arms (full n=3,369 coverage,
config_sha stamped, scorer parse path recorded). R1 did not fire
(base+P-plain 0.00% < 20%): the confirmatory block's "only SFT induces
abstention" stands under its own contract. R2 fired (base+P-rc 90.89% >=
60%): the cold-GRPO outcome verb becomes "preserves and sharpens
instruction-elicited abstention." R3 fired (cold SFT seed 1 P-struct 69.57%
>= 30% with base+P-struct 0.00% < 10%): SFT internalizes abstention beyond
instruction compliance. Cold DPO and KTO track the base under every prompt
condition (0≈0 under plain/struct, 94≈91 under RC); GRPO on an SFT base
deepens internalization (77.42% vs its base's 69.48%) while cold GRPO
internalizes nothing (0.00%). A descriptive scorer-scope audit found the
four 0.00% P-struct readings undercount natural-language abstention by
roughly 4-6 points; all conclusions survive against the 10% R3 ceiling.

**Why it matters here:** the panel's one-sentence verdict reframes every
training-regimen abstention claim in the program as meaningful only relative
to the prompt condition it was measured under, unless training has
internalized the behavior into the weights (SFT only) rather than merely
complying with an instruction already present in the prompt. It supplies the
base counterfactual [[grpo-cold-start-induction]] lacked at signing and is
the confirmatory-replication target for [[pstruct-internalization-seed-robustness]].

**Lineage:** builds on the cold-GRPO red-team audit
(`experiments/grpo-cold-start-induction/NOTEBOOK.md`). Source of truth:
`experiments/prompt-vs-training-panel/AMENDMENT.md`, Outcome section,
resolved 2026-08-14.
