---
aliases:
- confidence-refusal coupling only where SFT is in the lineage
- DPO/KTO barely refuse under P-struct; GRPO refuses at high stated confidence
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:sft-lineage-installs-confidence-refusal-coupling
  type: mechanism
  status: canonical
cause: "Measuring, under the structure-only P-struct contract on the same 1,832-row AmbigQA arms, the direction of stated-confidence separation between refused and answered rows (median confidence on refused rows minus median on answered rows), split three ways by training lineage: SFT-rooted with a preference stage on top (cold SFT, sequential SFT->DPO, sequential SFT->KTO), cold preference with no SFT (cold DPO, cold KTO), and SFT followed by GRPO (which has SFT in its lineage but a reinforcement stage after it)."
effect: "Negative separation (refusals paired with markedly lower stated confidence) holds at the maximum measured value, -0.95, in all 3 cold SFT seeds and all 6 sequential SFT->DPO/SFT->KTO seeds. Cold DPO and cold KTO essentially never refuse under this contract (1-2 of 1,832 rows per arm), so their separation reads 0.0 and is degenerate rather than a real null. SFT->GRPO refuses on 71.4 percent of rows while stating mean confidence 0.8127, separation -0.0003, effectively zero: high schema-confidence regardless of refusal behavior. Overall 11 of 17 trained arms showed negative separation against the P3 band (needed >=12 of 17); P3 did not hold, and F2 (majority reversed, refused rows higher) did not fire. Precise mechanism: SFT installs the coupling between low stated confidence and refusal; a subsequent DPO or KTO stage preserves it; a subsequent GRPO stage erases it (SFT->GRPO has SFT in its lineage yet refuses with no confidence signal attached); and cold preference training alone induces neither refusal nor coupling under this contract."
polarity: enables
related:
- '[[stated-confidence-under-pstruct]]'
- '[[only-sft-installs-abstention-in-weights]]'
- '[[pstruct-stated-confidence-miscalibrated-near-chance]]'
- '[[cold-grpo-falsifier-fires-but-reclassified-as-prompt-preservation]]'
- '[[verbalized-confidence]]'
relationships:
- type: supported_by
  target: '[[stated-confidence-under-pstruct]]'
  target_id: experiment:stated-confidence-under-pstruct
  confidence: high
  evidence:
  - "experiments/stated-confidence-under-pstruct/AMENDMENT.md#outcome (SC-G1: P3 DOES NOT HOLD, 11/17 negative separation, needed >=12; SFT-lineage arms all -0.95, cold DPO/KTO degenerate at 0.0, SFT->GRPO -0.0003 at 71.4pct refusal rate; F2 did not fire)"
- type: related_to
  target: '[[only-sft-installs-abstention-in-weights]]'
  target_id: mechanism:only-sft-installs-abstention-in-weights
  confidence: high
  evidence:
  - "experiments/stated-confidence-under-pstruct/AMENDMENT.md Reading (the confidence-refusal coupling exists only where SFT is in the training lineage, the same partition only-sft-installs-abstention-in-weights draws for refusal recall itself under P-struct)"
- type: related_to
  target: '[[pstruct-stated-confidence-miscalibrated-near-chance]]'
  target_id: mechanism:pstruct-stated-confidence-miscalibrated-near-chance
  confidence: high
  evidence:
  - "experiments/stated-confidence-under-pstruct/AMENDMENT.md#outcome (companion adjudication from the same instrument and arm set, SC-G1 P1/P2 versus P3)"
- type: related_to
  target: '[[cold-grpo-falsifier-fires-but-reclassified-as-prompt-preservation]]'
  target_id: mechanism:cold-grpo-falsifier-fires-but-reclassified-as-prompt-preservation
  confidence: medium
  evidence:
  - "experiments/stated-confidence-under-pstruct/AMENDMENT.md descriptive per-arm table (sft_grpo_seed1 refuses 71.4 percent of P-struct rows at mean stated confidence 0.8127 with zero separation, the same checkpoint whose cold-start GRPO refusal behavior is adjudicated as prompt-preservation, not induction, elsewhere)"
- type: related_to
  target: '[[verbalized-confidence]]'
  target_id: method:verbalized-confidence
  confidence: high
---

Under the structure-only P-struct contract, whether a model's stated
confidence drops when it refuses depends on its training lineage, not on
whether it refuses at all. Cold SFT and both sequential SFT->DPO/SFT->KTO
families pair refusals with sharply lower stated confidence (separation
-0.95, the maximum measured value, in all 9 of 9 seeds). Cold DPO and cold
KTO almost never refuse under this contract (1-2 rows of 1,832), so no real
coupling can be measured. SFT->GRPO refuses on 71.4 percent of rows while
stating a mean confidence of 0.8127 with essentially zero separation:
high schema-confidence regardless of whether the model is refusing.

**Why it matters here:** this is the mechanism the user's registered
prediction called ("the model emits high schema-confidence regardless of
whether it is refusing"), and it holds specifically in the non-SFT-lineage
arms (cold DPO/KTO degenerate, SFT->GRPO zero separation at high refusal
rate), while the SFT-lineage arms show the opposite pattern. The channel's
usefulness as a refusal signal is conditional on SFT being present in the
lineage.

**Lineage:** measured by [[stated-confidence-under-pstruct]], exploratory,
single pass, resolved 2026-08-18. Companion finding to
[[pstruct-stated-confidence-miscalibrated-near-chance]] from the same
instrument and arm set; parallels the SFT/non-SFT partition
[[only-sft-installs-abstention-in-weights]] draws for refusal recall itself.
Source of truth: `experiments/stated-confidence-under-pstruct/AMENDMENT.md`,
Outcome section, resolved 2026-08-18.
