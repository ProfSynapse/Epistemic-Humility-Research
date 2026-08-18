---
aliases:
- P2 holds, P1 does not, under the structure-only contract
- stated confidence is inflated and near-chance discriminative under P-struct
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:pstruct-stated-confidence-miscalibrated-near-chance
  type: mechanism
  status: canonical
cause: "Scoring the stated_confidence field emitted under the structure-only P-struct prompt contract (JSON schema present, no abstention affordance in the prompt) against correctness and against a 10-bin ECE, on 1,832 AmbigQA rows per arm across 17 trained P-struct arms (cold SFT, cold DPO, cold KTO, sequential SFT->DPO, sequential SFT->KTO, SFT->GRPO; base excluded from the trained-arm bands)."
effect: "Calibration is severely broken on every trained arm: 10-bin ECE 0.5482-0.8495, clearing the P2 band (ECE >=0.15 on >=9 of 17) at 17 of 17. Base and cold DPO/KTO arms state mean confidence 0.925-0.945 while answering at only 8.5-10.0 percent accuracy. Discrimination stays near chance for most regimens: only 8 of 17 trained arms land inside the P1 band [0.55, 0.80] (needed >=12, did not hold); cold DPO (3 seeds), cold KTO (3 seeds), clean-SFT merged, and SFT->GRPO all read at or below 0.5449 AUROC, with SFT->GRPO actually below chance at 0.4898. The only arms with informative discrimination are the sequential SFT->KTO seeds (0.6852-0.7245) and, more weakly, cold SFT and sequential SFT->DPO seeds. Neither falsifier fired: F1 (AUROC <=0.55 on ALL trained arms) did not fire because 8 arms cleared 0.55."
polarity: decouples
related:
- '[[stated-confidence-under-pstruct]]'
- '[[verbalized-confidence-channel-bottleneck]]'
- '[[ambigqa-stated-confidence-collapse-not-universal-across-arms]]'
- '[[only-sft-installs-abstention-in-weights]]'
- '[[verbalized-confidence]]'
- '[[auroc]]'
- '[[expected-calibration-error]]'
relationships:
- type: supported_by
  target: '[[stated-confidence-under-pstruct]]'
  target_id: experiment:stated-confidence-under-pstruct
  confidence: high
  evidence:
  - "experiments/stated-confidence-under-pstruct/AMENDMENT.md#outcome (SC-G1 per-prediction adjudication: P2 HOLDS 17/17 trained arms ECE 0.5482-0.8495; P1 DOES NOT HOLD 8/17 in [0.55,0.80] band; F1 did not fire)"
- type: related_to
  target: '[[verbalized-confidence-channel-bottleneck]]'
  target_id: mechanism:verbalized-confidence-channel-bottleneck
  confidence: high
  evidence:
  - "experiments/stated-confidence-under-pstruct/AMENDMENT.md Reading (the channel is not noise, but it is broken in a structured way; severe confidence inflation is universal, discrimination near chance for most regimens - the same emitted-scalar bottleneck paper 3 localizes, now measured under a prompt contract paper 2 left unanalyzed)"
- type: related_to
  target: '[[ambigqa-stated-confidence-collapse-not-universal-across-arms]]'
  target_id: mechanism:ambigqa-stated-confidence-collapse-not-universal-across-arms
  confidence: medium
  evidence:
  - "experiments/stated-confidence-under-pstruct/AMENDMENT.md descriptive per-arm table (same AmbigQA surface and stated-confidence channel as the G5 gate's collapse finding, here scored for calibration and discrimination rather than variance)"
- type: related_to
  target: '[[only-sft-installs-abstention-in-weights]]'
  target_id: mechanism:only-sft-installs-abstention-in-weights
  confidence: medium
  evidence:
  - "experiments/stated-confidence-under-pstruct/AMENDMENT.md descriptive per-arm table (the same 17 trained P-struct arms this mechanism scores are the arms whose refusal recall only-sft-installs-abstention-in-weights measures)"
- type: related_to
  target: '[[verbalized-confidence]]'
  target_id: method:verbalized-confidence
  confidence: high
- type: related_to
  target: '[[auroc]]'
  target_id: metric:auroc
  confidence: high
- type: related_to
  target: '[[expected-calibration-error]]'
  target_id: metric:expected-calibration-error
  confidence: high
---

Under the structure-only P-struct prompt contract (a JSON schema field for
stated confidence, no abstention affordance in the prompt), the
stated-confidence channel is not noise, but it is not usable either. On the
prompt-crossing held-out confirmatory campaign's 1,832-row-per-arm AmbigQA
pool, calibration is severe on all 17 trained arms (10-bin ECE 0.55-0.85, base
and cold DPO/KTO stating mean confidence 0.92-0.95 while answering at
8.5-10 percent accuracy), and confidence-correctness discrimination is at or
near chance for most training regimens: only 8 of 17 trained arms clear an
AUROC of 0.55, and only the sequential SFT->KTO seeds reach the informative-
but-weak band (best 0.7245).

**Why it matters here:** this closes paper 2 Section 5's scope condition,
which flagged the P-struct stated-confidence channel as captured but never
analyzed. The channel carries some correctness information in SFT-lineage
sequential arms, but is severely miscalibrated everywhere and near-useless
for discrimination outside that lineage.

**Lineage:** measured by [[stated-confidence-under-pstruct]], exploratory,
single pass, resolved 2026-08-18. Related to
[[verbalized-confidence-channel-bottleneck]] (paper 3's SelfAware-scoped
finding of the same emitted-scalar bottleneck) and
[[ambigqa-stated-confidence-collapse-not-universal-across-arms]] (the prior
AmbigQA variance finding on the same channel, different contract). Source of
truth: `experiments/stated-confidence-under-pstruct/AMENDMENT.md`, Outcome
section, resolved 2026-08-18.
