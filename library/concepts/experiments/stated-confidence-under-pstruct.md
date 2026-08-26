---
title: stated-confidence-under-pstruct
aliases:
- 'Stated confidence under the structure-only contract: the unanalyzed channel'
- P-struct stated-confidence analysis cell
tags:
- kg/experiment
- experiment
- abstention
kg:
  id: experiment:stated-confidence-under-pstruct
  type: experiment
  status: canonical
related:
- '[[prompt-crossing-heldout-confirmatory]]'
- '[[pstruct-stated-confidence-miscalibrated-near-chance]]'
- '[[sft-lineage-installs-confidence-refusal-coupling]]'
- '[[only-sft-installs-abstention-in-weights]]'
- '[[verbalized-confidence-channel-bottleneck]]'
- '[[ambigqa-stated-confidence-collapse-not-universal-across-arms]]'
- '[[verbalized-confidence]]'
- '[[auroc]]'
- '[[expected-calibration-error]]'
relationships:
- type: builds_on
  target: '[[prompt-crossing-heldout-confirmatory]]'
  target_id: experiment:prompt-crossing-heldout-confirmatory
  confidence: high
  evidence:
  - "experiments/stated-confidence-under-pstruct/AMENDMENT.md Motivation and posture (the rows already exist on disk: the prompt-crossing held-out confirmatory campaign scored 1,832 AmbigQA rows per arm across 18 P-struct-bearing arms; this cell is a CPU-only re-analysis of those existing artifacts, no new generation)"
- type: supports
  target: '[[pstruct-stated-confidence-miscalibrated-near-chance]]'
  target_id: mechanism:pstruct-stated-confidence-miscalibrated-near-chance
  confidence: high
  evidence:
  - "experiments/stated-confidence-under-pstruct/AMENDMENT.md#outcome (SC-G1: P2 HOLDS 17/17 trained arms ECE 0.5482-0.8495; P1 DOES NOT HOLD 8/17 in [0.55,0.80]; F1 did not fire)"
- type: supports
  target: '[[sft-lineage-installs-confidence-refusal-coupling]]'
  target_id: mechanism:sft-lineage-installs-confidence-refusal-coupling
  confidence: high
  evidence:
  - "experiments/stated-confidence-under-pstruct/AMENDMENT.md#outcome (SC-G1: P3 DOES NOT HOLD, 11/17 negative separation, needed >=12; SFT-lineage arms all -0.95, cold DPO/KTO degenerate at 0.0, SFT->GRPO -0.0003 at 71.4pct refusal; F2 did not fire)"
- type: related_to
  target: '[[only-sft-installs-abstention-in-weights]]'
  target_id: mechanism:only-sft-installs-abstention-in-weights
  confidence: medium
  evidence:
  - "experiments/stated-confidence-under-pstruct/AMENDMENT.md descriptive per-arm table (this cell's 17 trained P-struct arms are the same arms whose refusal recall only-sft-installs-abstention-in-weights measures, now also scored on stated confidence)"
- type: related_to
  target: '[[verbalized-confidence-channel-bottleneck]]'
  target_id: mechanism:verbalized-confidence-channel-bottleneck
  confidence: medium
  evidence:
  - "experiments/stated-confidence-under-pstruct/AMENDMENT.md Reading (the channel is not noise, but it is broken in a structured way, localizing to the same emitted-scalar bottleneck under a prompt contract this paper left unanalyzed)"
- type: related_to
  target: '[[ambigqa-stated-confidence-collapse-not-universal-across-arms]]'
  target_id: mechanism:ambigqa-stated-confidence-collapse-not-universal-across-arms
  confidence: medium
  evidence:
  - "experiments/stated-confidence-under-pstruct/AMENDMENT.md Design (same AmbigQA stated-confidence channel and rows, prior variance-only reading now scored for calibration, discrimination, and refusal separation)"
- type: uses
  target: '[[verbalized-confidence]]'
  target_id: method:verbalized-confidence
  confidence: high
- type: measures
  target: '[[auroc]]'
  target_id: metric:auroc
  confidence: high
- type: measures
  target: '[[expected-calibration-error]]'
  target_id: metric:expected-calibration-error
  confidence: high
---

Tier-2 exploratory, single-pass, CPU-only re-analysis cell. Paper 2 records a
scope condition: every stated-calibration reading in that paper comes from
arms whose prompt carried the full contract, and the stated-confidence
channel emitted under the structure-only P-struct prompt was captured on disk
but never analyzed. This cell scores that channel on the prompt-crossing
held-out confirmatory campaign's existing artifacts: 1,832 AmbigQA rows per
arm across 18 P-struct-bearing arms (base plus 17 trained checkpoints -
clean-SFT merged, cold SFT/DPO/KTO seeds 1-3, sequential SFT->DPO and
SFT->KTO seeds 1-3, SFT->GRPO seed 1), computing parse integrity,
confidence-correctness AUROC, 10-bin ECE, and refusal-vs-answer confidence
separation, per arm. No generation, no GPU.

Resolved 2026-08-18 (partial verdict, both predictors' scoreboard calls
recorded pre-run). SC-G0 (integrity) passed: all 18 arms at full 1,832-row
coverage, parse rates 0.983-1.000, zero arms excluded. SC-G1 adjudication
across the 17 trained arms: **P2 (miscalibration) HOLDS**, 17 of 17 at ECE
>=0.15 (actual range 0.5482-0.8495). **P1 (discrimination) DOES NOT HOLD**,
only 8 of 17 in the [0.55, 0.80] AUROC band (needed >=12); most arms read
near chance, with the informative-but-weak exception of sequential
SFT->KTO seeds (best 0.7245). **P3 (refusal separation) DOES NOT HOLD**, 11
of 17 show negative separation (needed >=12); the confidence-refusal
coupling is present only where SFT sits in the training lineage - cold SFT
and both sequential families all read -0.95, while cold DPO/KTO barely
refuse under this contract (1-2 of 1,832 rows) and SFT->GRPO refuses on
71.4 percent of rows at 0.8127 mean stated confidence with essentially zero
separation. Neither registered falsifier fired (F1: AUROC <=0.55 on all
trained arms; F2: majority-reversed separation).

Predictions scoreboard: user called 2 of 3 correctly (P2 holds, P3 fails via
the high-schema-confidence-regardless-of-refusal mechanism); orchestrator
called 1 of 3 (P2 only).

**Why it matters here:** closes paper 2 Section 5's "captured but never
analyzed" scope condition for the structure-only stated-confidence channel.
The channel is not noise, but it is broken in a structured way: universal
severe miscalibration, near-chance discrimination outside SFT-lineage
sequential arms, and a confidence-refusal coupling that exists only where
SFT is present in the training lineage.

**Lineage:** builds on [[prompt-crossing-heldout-confirmatory]] (source of
the scored AmbigQA rows, no new generation). Produces
[[pstruct-stated-confidence-miscalibrated-near-chance]] (P1/P2) and
[[sft-lineage-installs-confidence-refusal-coupling]] (P3). Exploratory,
reported separately from the paper-2 headline matrix and never pooled with
it. Source of truth: `experiments/stated-confidence-under-pstruct/AMENDMENT.md`,
Outcome section, resolved 2026-08-18.
